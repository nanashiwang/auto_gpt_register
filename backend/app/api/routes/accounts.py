"""账号管理 API 路由"""
from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from typing import List, Optional
from datetime import datetime
from app.models.schemas import AccountModel, RegistrationStatus
from app.services.excel_service import ExcelService
from app.services.crypto_service import CryptoService
from app.api.routes.websocket import manager
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/accounts", tags=["账号管理"])

# 全局 Excel 服务实例
excel_service = ExcelService(settings.ACCOUNTS_FILE)
crypto_service = CryptoService()


@router.get("/", response_model=List[AccountModel])
async def get_accounts(
    status: Optional[RegistrationStatus] = None,
    page: int = 1,
    page_size: int = 20
):
    """
    获取账号列表

    Args:
        status: 按状态筛选
        page: 页码
        page_size: 每页数量

    Returns:
        账号列表
    """
    try:
        accounts = await excel_service.load_accounts()

        # 按状态筛选
        if status:
            accounts = [a for a in accounts if a.status == status]

        # 分页
        start = (page - 1) * page_size
        end = start + page_size
        paginated_accounts = accounts[start:end]

        logger.info(f"获取账号列表: 总数={len(accounts)}, 返回={len(paginated_accounts)}")
        return paginated_accounts

    except Exception as e:
        logger.error(f"获取账号列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_accounts_stats():
    """
    获取账号统计信息

    Returns:
        统计信息字典
    """
    try:
        accounts = await excel_service.load_accounts()

        stats = {
            'total': len(accounts),
            'pending': len([a for a in accounts if a.status == RegistrationStatus.PENDING]),
            'in_progress': len([a for a in accounts if a.status == RegistrationStatus.IN_PROGRESS]),
            'success': len([a for a in accounts if a.status == RegistrationStatus.SUCCESS]),
            'failed': len([a for a in accounts if a.status == RegistrationStatus.FAILED]),
            'captcha_failed': len([a for a in accounts if a.status == RegistrationStatus.CAPTCHA_FAILED]),
            'proxy_failed': len([a for a in accounts if a.status == RegistrationStatus.PROXY_FAILED]),
        }

        return stats

    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import")
async def import_accounts(file: UploadFile = File(...)):
    """
    导入账号文件

    Args:
        file: 上传的 Excel 文件

    Returns:
        导入结果
    """
    try:
        # 保存上传的文件
        import os
        file_path = f"{settings.DATA_DIR}/uploaded_{file.filename}"
        os.makedirs(settings.DATA_DIR, exist_ok=True)

        with open(file_path, 'wb') as f:
            content = await file.read()
            f.write(content)

        # 读取并验证账号
        temp_service = ExcelService(file_path, crypto_service)
        accounts = await temp_service.load_accounts()

        # 保存到主文件
        await excel_service.save_accounts(accounts)

        logger.info(f"导入 {len(accounts)} 个账号成功")
        return {
            'message': f'成功导入 {len(accounts)} 个账号',
            'count': len(accounts)
        }

    except Exception as e:
        logger.error(f"导入账号失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export")
async def export_accounts(status: Optional[RegistrationStatus] = None):
    """
    导出账号文件

    Args:
        status: 按状态筛选导出

    Returns:
        文件路径
    """
    try:
        accounts = await excel_service.load_accounts()

        # 按状态筛选
        if status:
            accounts = [a for a in accounts if a.status == status]

        # 生成导出文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_path = f"{settings.DATA_DIR}/exported_accounts_{timestamp}.xlsx"

        export_service = ExcelService(export_path, crypto_service)
        await export_service.save_accounts(accounts)

        logger.info(f"导出 {len(accounts)} 个账号到: {export_path}")
        return {
            'message': f'成功导出 {len(accounts)} 个账号',
            'file_path': export_path,
            'count': len(accounts)
        }

    except Exception as e:
        logger.error(f"导出账号失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{account_id}")
async def update_account(account_id: int, account: AccountModel):
    """
    更新账号信息

    Args:
        account_id: 账号 ID
        account: 账号数据

    Returns:
        更新后的账号
    """
    try:
        accounts = await excel_service.load_accounts()

        # 查找并更新账号
        for idx, acc in enumerate(accounts):
            if acc.id == account_id:
                account.id = account_id
                accounts[idx] = account
                await excel_service.save_accounts(accounts)

                logger.info(f"更新账号: {account.email}")
                return account

        raise HTTPException(status_code=404, detail="账号不存在")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新账号失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{account_id}")
async def delete_account(account_id: int):
    """
    删除账号

    Args:
        account_id: 账号 ID

    Returns:
        删除结果
    """
    try:
        accounts = await excel_service.load_accounts()

        # 查找并删除账号
        original_count = len(accounts)
        accounts = [a for a in accounts if a.id != account_id]

        if len(accounts) == original_count:
            raise HTTPException(status_code=404, detail="账号不存在")

        await excel_service.save_accounts(accounts)

        logger.info(f"删除账号 ID: {account_id}")
        return {'message': '账号删除成功'}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除账号失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add")
async def add_account(account: AccountModel):
    """
    添加单个账号

    Args:
        account: 账号数据

    Returns:
        添加的账号
    """
    try:
        accounts = await excel_service.load_accounts()

        # 分配 ID
        if accounts:
            account.id = max(a.id for a in accounts if a.id) + 1
        else:
            account.id = 1

        accounts.append(account)
        await excel_service.save_accounts(accounts)

        logger.info(f"添加账号: {account.email}")
        return account

    except Exception as e:
        logger.error(f"添加账号失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
