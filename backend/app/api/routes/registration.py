"""注册任务 API 路由"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional
from datetime import datetime
import asyncio
from app.models.schemas import RegistrationTask, AccountModel, RegistrationStatus
from app.services.excel_service import ExcelService
from app.core.registration import RegistrationStateMachine, RegistrationContext
from app.core.browser import BrowserService
from app.core.captcha_solver import CaptchaFactory
from app.core.proxy_manager import ProxyManager
from app.api.routes.websocket import manager
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/registration", tags=["注册任务"])

# 全局任务存储
tasks = {}
task_counter = 0


async def execute_single_account(
    account: AccountModel,
    task_id: str,
    captcha_solver,
    proxy_manager: Optional[ProxyManager]
) -> RegistrationStatus:
    """
    执行单个账号的注册

    Args:
        account: 账号信息
        task_id: 任务 ID
        captcha_solver: 验证码服务
        proxy_manager: 代理管理器

    Returns:
        注册状态
    """
    browser = None
    try:
        # 创建浏览器服务
        browser = BrowserService(headless=settings.HEADLESS_MODE)

        # 创建注册上下文
        context = RegistrationContext(
            email=account.email,
            password=account.password,
            browser=browser,
            captcha_solver=captcha_solver,
            proxy_manager=proxy_manager,
            task_id=task_id,
            max_retries=settings.MAX_RETRY_COUNT,
            log_callback=lambda level, msg: manager.send_log(
                task_id,
                {
                    'account_email': account.email,
                    'level': level,
                    'message': msg,
                    'timestamp': datetime.now().isoformat()
                }
            )
        )

        # 执行注册流程
        state_machine = RegistrationStateMachine()
        status = await state_machine.execute(context)

        return status

    except Exception as e:
        logger.error(f"账号 {account.email} 注册异常: {str(e)}")
        return RegistrationStatus.FAILED

    finally:
        if browser:
            try:
                await browser.close()
            except:
                pass


async def execute_registration(
    task_id: str,
    accounts: list,
    max_concurrent: int = 3
):
    """
    执行批量注册任务

    Args:
        task_id: 任务 ID
        accounts: 账号列表
        max_concurrent: 最大并发数
    """
    try:
        # 初始化验证码服务
        captcha_solver = None
        if settings.CAPTCHA_API_KEY:
            try:
                captcha_solver = CaptchaFactory.create(
                    settings.CAPTCHA_SERVICE,
                    settings.CAPTCHA_API_KEY
                )
            except Exception as e:
                logger.error(f"初始化验证码服务失败: {str(e)}")

        # 初始化代理管理器
        proxy_manager = ProxyManager()

        # 更新任务状态
        if task_id in tasks:
            tasks[task_id]['status'] = 'running'

        total = len(accounts)
        completed = 0
        success_count = 0
        failed_count = 0

        # 创建信号量控制并发
        semaphore = asyncio.Semaphore(max_concurrent)

        async def register_with_semaphore(account):
            nonlocal completed, success_count, failed_count

            async with semaphore:
                # 更新当前处理账号
                if task_id in tasks:
                    tasks[task_id]['current_account'] = account.email

                await manager.send_status(task_id, {
                    'email': account.email,
                    'status': 'in_progress'
                })

                # 执行注册
                status = await execute_single_account(
                    account,
                    task_id,
                    captcha_solver,
                    proxy_manager
                )

                # 更新状态
                completed += 1
                if status == RegistrationStatus.SUCCESS:
                    success_count += 1
                else:
                    failed_count += 1

                # 更新 Excel 中的状态
                excel_service = ExcelService(settings.ACCOUNTS_FILE)
                await excel_service.update_account_status(
                    account.email,
                    status,
                    None if status == RegistrationStatus.SUCCESS else "注册失败"
                )

                # 发送进度更新
                await manager.send_progress(task_id, {
                    'total': total,
                    'completed': completed,
                    'success': success_count,
                    'failed': failed_count,
                    'current_email': account.email
                })

                # 更新任务信息
                if task_id in tasks:
                    tasks[task_id]['completed'] = completed
                    tasks[task_id]['success'] = success_count
                    tasks[task_id]['failed'] = failed_count

        # 并发执行所有账号注册
        await asyncio.gather(*[register_with_semaphore(acc) for acc in accounts])

        # 任务完成
        if task_id in tasks:
            tasks[task_id]['status'] = 'completed'
            tasks[task_id]['completed_at'] = datetime.now()

        logger.info(f"任务 {task_id} 完成: 成功={success_count}, 失败={failed_count}")

    except Exception as e:
        logger.error(f"任务 {task_id} 执行异常: {str(e)}")
        if task_id in tasks:
            tasks[task_id]['status'] = 'failed'

    finally:
        # 清理资源
        if captcha_solver:
            try:
                await captcha_solver.close()
            except:
                pass


@router.post("/start")
async def start_registration(
    background_tasks: BackgroundTasks,
    max_concurrent: int = 3
):
    """
    开始批量注册任务

    Args:
        background_tasks: FastAPI 后台任务
        max_concurrent: 最大并发数

    Returns:
        任务信息
    """
    try:
        global task_counter
        task_counter += 1
        task_id = f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}_{task_counter}"

        # 加载待注册账号
        excel_service = ExcelService(settings.ACCOUNTS_FILE)
        accounts = await excel_service.load_accounts()

        pending_accounts = [a for a in accounts if a.status == RegistrationStatus.PENDING]

        if not pending_accounts:
            raise HTTPException(status_code=400, detail="没有待注册的账号")

        # 创建任务
        tasks[task_id] = {
            'task_id': task_id,
            'total_accounts': len(pending_accounts),
            'completed': 0,
            'success': 0,
            'failed': 0,
            'status': 'running',
            'started_at': datetime.now(),
            'current_account': None
        }

        # 添加后台任务
        background_tasks.add_task(
            execute_registration,
            task_id,
            pending_accounts,
            max_concurrent
        )

        logger.info(f"启动注册任务 {task_id}, 账号数: {len(pending_accounts)}")

        return {
            "task_id": task_id,
            "total_accounts": len(pending_accounts),
            "message": "注册任务已启动"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启动注册任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """
    获取任务状态

    Args:
        task_id: 任务 ID

    Returns:
        任务状态信息
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")

    task = tasks[task_id]
    return {
        'task_id': task['task_id'],
        'total_accounts': task['total_accounts'],
        'completed': task['completed'],
        'success': task['success'],
        'failed': task['failed'],
        'status': task['status'],
        'started_at': task['started_at'],
        'completed_at': task.get('completed_at'),
        'current_account': task.get('current_account')
    }


@router.post("/pause/{task_id}")
async def pause_registration(task_id: str):
    """暂停注册任务(暂未实现)"""
    return {"message": f"任务 {task_id} 暂停功能开发中"}


@router.post("/resume/{task_id}")
async def resume_registration(task_id: str):
    """恢复注册任务(暂未实现)"""
    return {"message": f"任务 {task_id} 恢复功能开发中"}


@router.post("/cancel/{task_id}")
async def cancel_registration(task_id: str):
    """取消注册任务(暂未实现)"""
    return {"message": f"任务 {task_id} 取消功能开发中"}
