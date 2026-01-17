"""验证码识别服务模块"""
import asyncio
import httpx
from abc import ABC, abstractmethod
from typing import Optional
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CaptchaSolver(ABC):
    """验证码识别抽象基类"""

    @abstractmethod
    async def solve(self, image_data: bytes) -> str:
        """
        识别图片验证码

        Args:
            image_data: 验证码图片的二进制数据

        Returns:
            识别结果字符串
        """
        pass

    @abstractmethod
    async def solve_recaptcha_v2(self, site_key: str, page_url: str) -> str:
        """
        解决 reCAPTCHA v2

        Args:
            site_key: 站点密钥
            page_url: 页面 URL

        Returns:
            验证码响应令牌
        """
        pass

    @abstractmethod
    async def close(self):
        """关闭资源"""
        pass


class TwoCaptchaSolver(CaptchaSolver):
    """2Captcha 服务实现"""

    def __init__(self, api_key: str):
        """
        初始化 2Captcha 解析器

        Args:
            api_key: 2Captcha API 密钥
        """
        self.api_key = api_key
        self.base_url = "http://2captcha.com"
        self.client = httpx.AsyncClient(timeout=120.0)
        logger.info("2Captcha 服务初始化完成")

    async def solve(self, image_data: bytes) -> str:
        """识别图片验证码"""
        try:
            # 上传图片
            upload_url = f"{self.base_url}/in.php"
            response = await self.client.post(
                upload_url,
                data={
                    'key': self.api_key,
                    'method': 'base64',
                    'body': image_data.hex(),
                    'json': 1
                }
            )
            result = response.json()

            if result['status'] != 1:
                raise Exception(f"上传验证码失败: {result}")

            captcha_id = result['request']
            logger.info(f"验证码已上传, ID: {captcha_id}")

            # 轮询结果
            return await self._get_result(captcha_id)

        except Exception as e:
            logger.error(f"验证码识别失败: {str(e)}")
            raise

    async def solve_recaptcha_v2(self, site_key: str, page_url: str) -> str:
        """解决 reCAPTCHA v2"""
        try:
            url = f"{self.base_url}/in.php"
            response = await self.client.post(
                url,
                data={
                    'key': self.api_key,
                    'method': 'userrecaptcha',
                    'googlekey': site_key,
                    'pageurl': page_url,
                    'json': 1
                }
            )
            result = response.json()

            if result['status'] != 1:
                raise Exception(f"提交 reCAPTCHA 失败: {result}")

            captcha_id = result['request']
            logger.info(f"reCAPTCHA 任务已创建, ID: {captcha_id}")

            return await self._get_result(captcha_id)

        except Exception as e:
            logger.error(f"reCAPTCHA 识别失败: {str(e)}")
            raise

    async def _get_result(self, captcha_id: str, max_attempts: int = 30) -> str:
        """
        获取识别结果

        Args:
            captcha_id: 验证码 ID
            max_attempts: 最大尝试次数

        Returns:
            识别结果字符串
        """
        url = f"{self.base_url}/res.php"

        for attempt in range(max_attempts):
            await asyncio.sleep(3)  # 等待3秒

            response = await self.client.get(
                url,
                params={
                    'key': self.api_key,
                    'action': 'get',
                    'id': captcha_id,
                    'json': 1
                }
            )
            result = response.json()

            if result['status'] == 1:
                logger.info(f"验证码识别成功: {result['request'][:20]}...")
                return result['request']
            elif result['request'] == 'CAPCHA_NOT_READY':
                logger.info(f"等待识别结果... ({attempt + 1}/{max_attempts})")
                continue
            else:
                raise Exception(f"识别失败: {result}")

        raise TimeoutError("验证码识别超时")

    async def close(self):
        """关闭 HTTP 客户端"""
        await self.client.aclose()
        logger.info("2Captcha 服务已关闭")


class YesCaptchaSolver(CaptchaSolver):
    """YesCaptcha 服务实现(更快,更便宜)"""

    def __init__(self, api_key: str):
        """
        初始化 YesCaptcha 解析器

        Args:
            api_key: YesCaptcha API 密钥
        """
        self.api_key = api_key
        self.base_url = "https://api.yescaptcha.com"
        self.client = httpx.AsyncClient(timeout=120.0)
        logger.info("YesCaptcha 服务初始化完成")

    async def solve(self, image_data: bytes) -> str:
        """YesCaptcha 主要处理 reCAPTCHA,图片验证码需要使用其他服务"""
        raise NotImplementedError("YesCaptcha 不支持普通图片验证码")

    async def solve_recaptcha_v2(self, site_key: str, page_url: str) -> str:
        """解决 reCAPTCHA v2"""
        try:
            # 创建任务
            create_url = f"{self.base_url}/createTask"
            response = await self.client.post(
                create_url,
                json={
                    "clientKey": self.api_key,
                    "task": {
                        "type": "RecaptchaV2TaskProxyless",
                        "websiteURL": page_url,
                        "websiteKey": site_key
                    }
                }
            )
            result = response.json()

            if result['errorId'] != 0:
                raise Exception(f"创建任务失败: {result['errorDescription']}")

            task_id = result['taskId']
            logger.info(f"reCAPTCHA 任务已创建, ID: {task_id}")

            # 获取结果
            return await self._get_task_result(task_id)

        except Exception as e:
            logger.error(f"YesCaptcha 识别失败: {str(e)}")
            raise

    async def _get_task_result(self, task_id: str, max_attempts: int = 30) -> str:
        """
        获取任务结果

        Args:
            task_id: 任务 ID
            max_attempts: 最大尝试次数

        Returns:
            识别结果令牌
        """
        for attempt in range(max_attempts):
            await asyncio.sleep(2)

            response = await self.client.post(
                f"{self.base_url}/getTaskResult",
                json={
                    "clientKey": self.api_key,
                    "taskId": task_id
                }
            )
            result = response.json()

            if result['status'] == 'ready':
                logger.info("验证码识别成功")
                return result['solution']['gRecaptchaResponse']
            elif result['status'] == 'processing':
                logger.info(f"处理中... ({attempt + 1}/{max_attempts})")
                continue
            else:
                raise Exception(f"识别失败: {result}")

        raise TimeoutError("验证码识别超时")

    async def close(self):
        """关闭 HTTP 客户端"""
        await self.client.aclose()
        logger.info("YesCaptcha 服务已关闭")


class CaptchaFactory:
    """验证码服务工厂类"""

    @staticmethod
    def create(service_name: str, api_key: str) -> CaptchaSolver:
        """
        创建验证码服务实例

        Args:
            service_name: 服务名称 (2captcha, yescaptcha)
            api_key: API 密钥

        Returns:
            验证码解析器实例
        """
        services = {
            '2captcha': TwoCaptchaSolver,
            'yescaptcha': YesCaptchaSolver,
        }

        solver_class = services.get(service_name.lower())
        if not solver_class:
            raise ValueError(f"不支持的验证码服务: {service_name}")

        return solver_class(api_key)
