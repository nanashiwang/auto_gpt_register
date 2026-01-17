"""浏览器自动化服务模块 - 使用 Playwright"""
import asyncio
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class BrowserService:
    """浏览器服务类 - 使用 Playwright 进行自动化操作"""

    def __init__(self, headless: bool = True):
        """
        初始化浏览器服务

        Args:
            headless: 是否使用无头模式
        """
        self.headless = headless
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.proxy_config: Optional[Dict[str, Any]] = None

    async def start(self, proxy_config: Optional[Dict[str, Any]] = None):
        """
        启动浏览器

        Args:
            proxy_config: 代理配置字典
        """
        try:
            self.proxy_config = proxy_config
            self.playwright = await async_playwright().start()

            # 配置代理
            proxy = None
            if proxy_config:
                proxy = {
                    "server": f"{proxy_config.get('protocol', 'http')}://{proxy_config['host']}:{proxy_config['port']}",
                }
                if proxy_config.get('username') and proxy_config.get('password'):
                    proxy['username'] = proxy_config['username']
                    proxy['password'] = proxy_config['password']
                logger.info(f"使用代理: {proxy['server']}")

            # 启动 Chromium 浏览器
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                proxy=proxy,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-infobars',
                    '--window-size=1920,1080'
                ]
            )

            # 创建浏览器上下文(模拟真实用户环境)
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=settings.BROWSER_USER_AGENT,
                locale='zh-CN',
                timezone_id='Asia/Shanghai',
                geolocation={'latitude': 39.9042, 'longitude': 116.4074},  # 北京
                permissions=['geolocation']
            )

            # 注入脚本以隐藏 webdriver 特征
            await self.context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)

            logger.info("浏览器启动成功")
            return True

        except Exception as e:
            logger.error(f"浏览器启动失败: {str(e)}")
            raise

    async def get_page(self) -> Page:
        """
        获取新页面

        Returns:
            Page 对象
        """
        if not self.context:
            raise RuntimeError("浏览器上下文未初始化,请先调用 start() 方法")

        page = await self.context.new_page()

        # 设置默认超时时间
        page.set_default_timeout(settings.BROWSER_TIMEOUT)

        return page

    async def goto(self, page: Page, url: str, wait_until: str = "networkidle"):
        """
        导航到指定 URL

        Args:
            page: Page 对象
            url: 目标 URL
            wait_until: 等待条件 (domcontentloaded, load, networkidle)
        """
        try:
            await page.goto(url, wait_until=wait_until, timeout=settings.BROWSER_TIMEOUT)
            logger.info(f"导航到: {url}")
        except Exception as e:
            logger.error(f"导航失败: {url}, 错误: {str(e)}")
            raise

    async def take_screenshot(self, page: Page, filename: str, full_page: bool = True):
        """
        截图保存

        Args:
            page: Page 对象
            filename: 保存的文件名
            full_page: 是否截取整个页面
        """
        try:
            from pathlib import Path
            from app.config import settings

            # 确保截图目录存在
            screenshot_dir = Path(settings.SCREENSHOT_DIR)
            screenshot_dir.mkdir(parents=True, exist_ok=True)

            filepath = screenshot_dir / filename
            await page.screenshot(path=str(filepath), full_page=full_page)
            logger.info(f"截图已保存: {filepath}")
        except Exception as e:
            logger.error(f"截图失败: {str(e)}")

    async def wait_for_selector(
            self,
            page: Page,
            selector: str,
            timeout: int = None,
            state: str = "visible"
    ):
        """
        等待元素出现

        Args:
            page: Page 对象
            selector: CSS 选择器
            timeout: 超时时间(毫秒)
            state: 等待状态 (attached, detached, visible, hidden)
        """
        try:
            timeout = timeout or settings.BROWSER_TIMEOUT
            await page.wait_for_selector(selector, timeout=timeout, state=state)
        except Exception as e:
            logger.error(f"等待元素超时: {selector}, 错误: {str(e)}")
            raise

    async def fill_input(self, page: Page, selector: str, value: str):
        """
        填写输入框

        Args:
            page: Page 对象
            selector: CSS 选择器
            value: 填写的值
        """
        try:
            await self.wait_for_selector(page, selector)
            await page.fill(selector, value)
            logger.debug(f"填写输入框: {selector} = {value[:10]}...")
        except Exception as e:
            logger.error(f"填写输入框失败: {selector}, 错误: {str(e)}")
            raise

    async def click_button(self, page: Page, selector: str):
        """
        点击按钮

        Args:
            page: Page 对象
            selector: CSS 选择器
        """
        try:
            await self.wait_for_selector(page, selector)
            await page.click(selector)
            logger.debug(f"点击按钮: {selector}")
        except Exception as e:
            logger.error(f"点击按钮失败: {selector}, 错误: {str(e)}")
            raise

    async def get_text(self, page: Page, selector: str) -> str:
        """
        获取元素文本

        Args:
            page: Page 对象
            selector: CSS 选择器

        Returns:
            元素的文本内容
        """
        try:
            await self.wait_for_selector(page, selector)
            element = await page.query_selector(selector)
            text = await element.text_content() if element else ""
            return text.strip()
        except Exception as e:
            logger.error(f"获取文本失败: {selector}, 错误: {str(e)}")
            return ""

    async def execute_script(self, page: Page, script: str):
        """
        执行 JavaScript 脚本

        Args:
            page: Page 对象
            script: JavaScript 代码
        """
        try:
            await page.evaluate(script)
            logger.debug("执行 JavaScript 脚本成功")
        except Exception as e:
            logger.error(f"执行脚本失败: {str(e)}")
            raise

    async def close_page(self, page: Page):
        """
        关闭页面

        Args:
            page: Page 对象
        """
        try:
            await page.close()
            logger.debug("页面已关闭")
        except Exception as e:
            logger.error(f"关闭页面失败: {str(e)}")

    async def close(self):
        """关闭浏览器"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("浏览器已关闭")
        except Exception as e:
            logger.error(f"关闭浏览器失败: {str(e)}")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()
