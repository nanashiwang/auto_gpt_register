"""注册流程状态机模块"""
import asyncio
from enum import Enum
from typing import Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from app.models.enums import RegistrationStatus
from app.core.browser import BrowserService
from app.core.captcha_solver import CaptchaSolver
from app.core.proxy_manager import ProxyManager
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RegistrationState(Enum):
    """注册状态机状态"""
    INIT = "init"  # 初始化
    LOAD_PAGE = "load_page"  # 加载注册页面
    FILL_FORM = "fill_form"  # 填写表单
    SOLVE_CAPTCHA = "solve_captcha"  # 解决验证码
    SUBMIT_FORM = "submit_form"  # 提交表单
    VERIFY_EMAIL = "verify_email"  # 验证邮箱
    COMPLETE = "complete"  # 完成
    FAILED = "failed"  # 失败
    RETRY = "retry"  # 重试


@dataclass
class RegistrationContext:
    """注册上下文"""
    email: str
    password: str
    browser: BrowserService
    captcha_solver: Optional[CaptchaSolver]
    proxy_manager: Optional[ProxyManager]
    task_id: str
    max_retries: int = 3
    current_retry: int = 0
    error_message: Optional[str] = None
    log_callback: Optional[Callable] = None  # 日志回调函数

    async def log(self, level: str, message: str):
        """记录日志"""
        logger.info(f"[{self.email}] {message}")
        if self.log_callback:
            await self.log_callback(level, message)


class RegistrationStateMachine:
    """注册流程状态机类"""

    def __init__(self):
        """初始化状态机"""
        self.state = RegistrationState.INIT
        self.context: Optional[RegistrationContext] = None

    async def execute(self, context: RegistrationContext) -> RegistrationStatus:
        """
        执行注册流程

        Args:
            context: 注册上下文

        Returns:
            最终注册状态
        """
        self.context = context
        self.state = RegistrationState.INIT

        state_handlers = {
            RegistrationState.INIT: self._handle_init,
            RegistrationState.LOAD_PAGE: self._handle_load_page,
            RegistrationState.FILL_FORM: self._handle_fill_form,
            RegistrationState.SOLVE_CAPTCHA: self._handle_solve_captcha,
            RegistrationState.SUBMIT_FORM: self._handle_submit_form,
            RegistrationState.VERIFY_EMAIL: self._handle_verify_email,
            RegistrationState.COMPLETE: self._handle_complete,
            RegistrationState.FAILED: self._handle_failed,
            RegistrationState.RETRY: self._handle_retry,
        }

        try:
            while self.state not in [RegistrationState.COMPLETE, RegistrationState.FAILED]:
                handler = state_handlers.get(self.state)
                if not handler:
                    raise ValueError(f"未处理的状态: {self.state}")

                # 记录状态转换
                await context.log("INFO", f"执行状态: {self.state.value}")

                # 执行状态处理器
                next_state = await handler()

                # 状态转换
                if next_state != self.state:
                    logger.info(f"[{context.email}] 状态转换: {self.state} -> {next_state}")
                self.state = next_state

            # 返回最终状态
            return RegistrationStatus.SUCCESS if self.state == RegistrationState.COMPLETE else RegistrationStatus.FAILED

        except Exception as e:
            logger.error(f"[{context.email}] 注册流程异常: {str(e)}")
            context.error_message = str(e)
            await context.log("ERROR", f"注册流程异常: {str(e)}")
            return RegistrationStatus.FAILED

        finally:
            # 清理资源
            if context.browser:
                try:
                    await context.browser.close()
                except:
                    pass

    async def _handle_init(self) -> RegistrationState:
        """初始化状态 - 启动浏览器"""
        try:
            # 获取代理配置
            proxy_config = None
            if self.context.proxy_manager:
                proxy_config = await self.context.proxy_manager.get_proxy()

            # 启动浏览器
            await self.context.browser.start(proxy_config)
            return RegistrationState.LOAD_PAGE

        except Exception as e:
            self.context.error_message = f"浏览器启动失败: {str(e)}"
            return RegistrationState.RETRY

    async def _handle_load_page(self) -> RegistrationState:
        """加载注册页面"""
        try:
            page = await self.context.browser.get_page()

            # 访问 GPT 注册页面
            await self.context.browser.goto(page, 'https://chat.openai.com/auth/login')

            # 等待页面加载
            await asyncio.sleep(2)

            # 检查是否需要登录
            current_url = page.url
            await self.context.log("INFO", f"当前页面: {current_url}")

            return RegistrationState.FILL_FORM

        except Exception as e:
            self.context.error_message = f"加载页面失败: {str(e)}"
            await self.context.log("ERROR", self.context.error_message)
            return RegistrationState.RETRY

    async def _handle_fill_form(self) -> RegistrationState:
        """填写表单"""
        try:
            page = await self.context.browser.get_page()

            # 查找微软登录按钮
            await asyncio.sleep(1)

            # 这里需要根据实际页面结构调整选择器
            # 示例代码,实际选择器需要根据页面情况修改
            try:
                # 尝试查找登录按钮
                login_button = await page.query_selector('button:has-text("Log in")')
                if login_button:
                    await login_button.click()
                    await asyncio.sleep(2)
            except:
                pass

            # 检查是否有 Microsoft 登录选项
            microsoft_button = await page.query_selector('button:has-text("Microsoft")')
            if microsoft_button:
                await microsoft_button.click()
                await asyncio.sleep(2)

            # 填写微软账号密码
            # 这里需要根据实际的 Microsoft 登录页面流程来实现
            # 示例流程:
            await self._fill_microsoft_credentials(page)

            return RegistrationState.SUBMIT_FORM

        except Exception as e:
            self.context.error_message = f"填写表单失败: {str(e)}"
            await self.context.log("ERROR", self.context.error_message)
            return RegistrationState.RETRY

    async def _fill_microsoft_credentials(self, page):
        """填写微软账号凭据"""
        """这是一个示例实现,需要根据实际页面调整"""

        # 等待邮箱输入框
        await self.context.browser.wait_for_selector(page, 'input[type="email"]', timeout=5000)
        await page.fill('input[type="email"]', self.context.email)
        await page.click('input[type="submit"]')

        await asyncio.sleep(2)

        # 等待密码输入框
        await self.context.browser.wait_for_selector(page, 'input[type="password"]', timeout=5000)
        await page.fill('input[type="password"]', self.context.password)
        await page.click('input[type="submit"]')

        await asyncio.sleep(2)

    async def _handle_solve_captcha(self) -> RegistrationState:
        """解决验证码"""
        if not self.context.captcha_solver:
            self.context.error_message = "未配置验证码服务"
            return RegistrationState.FAILED

        try:
            page = await self.context.browser.get_page()

            # 查找验证码元素
            captcha_element = await page.query_selector('[data-sitekey]')
            if not captcha_element:
                # 没有验证码,直接提交
                return RegistrationState.SUBMIT_FORM

            # 获取 reCAPTCHA site key
            site_key = await captcha_element.get_attribute('data-sitekey')
            page_url = page.url

            await self.context.log("INFO", f"开始解决验证码, site_key: {site_key}")

            # 调用验证码服务
            solution = await self.context.captcha_solver.solve_recaptcha_v2(
                site_key=site_key,
                page_url=page_url
            )

            # 注入解决方案
            script = f"""
            document.getElementById('g-recaptcha-response').innerHTML = '{solution}';
            """
            await self.context.browser.execute_script(page, script)

            await self.context.log("INFO", "验证码已解决并注入")

            return RegistrationState.SUBMIT_FORM

        except Exception as e:
            self.context.error_message = f"验证码解决失败: {str(e)}"
            await self.context.log("ERROR", self.context.error_message)

            # 截图保存
            await self.context.browser.take_screenshot(
                await self.context.browser.get_page(),
                f"captcha_failed_{self.context.email}.png"
            )

            return RegistrationState.FAILED

    async def _handle_submit_form(self) -> RegistrationState:
        """提交表单"""
        try:
            page = await self.context.browser.get_page()

            # 等待页面响应
            await asyncio.sleep(3)

            # 检查当前 URL
            current_url = page.url
            await self.context.log("INFO", f"提交后 URL: {current_url}")

            # 检查是否注册成功
            if 'chat.openai.com' in current_url and '/auth/' not in current_url:
                return RegistrationState.COMPLETE

            # 检查是否需要邮箱验证
            if 'verify' in current_url or 'confirm' in current_url:
                return RegistrationState.VERIFY_EMAIL

            # 检查错误信息
            error_selectors = ['.error', '[role="alert"]', '.error-message']
            for selector in error_selectors:
                error_element = await page.query_selector(selector)
                if error_element:
                    error_text = await error_element.text_content()
                    if error_text:
                        self.context.error_message = error_text
                        await self.context.log("ERROR", f"页面错误: {error_text}")
                        return RegistrationState.RETRY

            # 可能需要等待重定向
            await asyncio.sleep(2)

            # 再次检查
            if 'chat.openai.com' in page.url:
                return RegistrationState.COMPLETE

            return RegistrationState.COMPLETE

        except Exception as e:
            self.context.error_message = f"提交表单失败: {str(e)}"
            await self.context.log("ERROR", self.context.error_message)
            return RegistrationState.RETRY

    async def _handle_verify_email(self) -> RegistrationState:
        """验证邮箱(需要人工介入或自动读取邮箱)"""
        self.context.error_message = "需要人工验证邮箱"
        await self.context.log("WARNING", self.context.error_message)
        return RegistrationState.FAILED

    async def _handle_complete(self) -> RegistrationState:
        """完成状态"""
        await self.context.log("INFO", "注册成功!")
        return RegistrationState.COMPLETE

    async def _handle_failed(self) -> RegistrationState:
        """失败状态"""
        await self.context.log("ERROR", self.context.error_message or "注册失败")
        return RegistrationState.FAILED

    async def _handle_retry(self) -> RegistrationState:
        """重试状态"""
        self.context.current_retry += 1

        if self.context.current_retry <= self.context.max_retries:
            await self.context.log(
                "WARNING",
                f"重试 {self.context.current_retry}/{self.context.max_retries}"
            )

            # 延迟后重试
            await asyncio.sleep(5)
            return RegistrationState.LOAD_PAGE
        else:
            await self.context.log("ERROR", "达到最大重试次数,放弃")
            return RegistrationState.FAILED
