"""Mail.tm 临时邮箱客户端"""
import asyncio
import secrets
import string
import time
from dataclasses import dataclass
from typing import List, Optional

import httpx
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class MailTmAccount:
    """Mail.tm 账号信息"""
    id: str
    address: str
    password: str
    token: str


class MailTmClient:
    """Mail.tm API 客户端"""

    def __init__(self, base_url: str, timeout: float = 30.0):
        """
        初始化客户端

        Args:
            base_url: API 基础地址
            timeout: 请求超时时间(秒)
        """
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=timeout)

    async def close(self):
        """关闭 HTTP 客户端"""
        await self.client.aclose()

    async def get_domains(self, page: int = 1) -> List[dict]:
        """
        获取可用域名列表

        Args:
            page: 页码
        """
        response = await self.client.get("/domains", params={"page": page})
        response.raise_for_status()
        data = response.json()
        return data.get("hydra:member", [])

    async def create_account(
        self,
        page: int = 1,
        username: Optional[str] = None,
        password: Optional[str] = None
    ) -> MailTmAccount:
        """
        创建临时邮箱账号并获取访问令牌

        Args:
            page: 域名分页页码
            username: 指定用户名(可选)
            password: 指定密码(可选)
        """
        domains = await self.get_domains(page=page)
        domain = self._pick_domain(domains)
        if not domain:
            raise RuntimeError("未获取到可用的临时邮箱域名")

        username = username or self._generate_username()
        password = password or self._generate_password()
        address = f"{username}@{domain}"

        response = await self.client.post(
            "/accounts",
            json={
                "address": address,
                "password": password
            }
        )
        response.raise_for_status()
        data = response.json()

        account_id = data.get("id")
        if not account_id:
            raise RuntimeError("创建临时邮箱账号失败: 缺少账号 ID")

        token = await self._get_token(address, password)
        logger.info(f"创建临时邮箱成功: {address}")

        return MailTmAccount(
            id=account_id,
            address=address,
            password=password,
            token=token
        )

    async def list_messages(self, token: str, page: int = 1) -> List[dict]:
        """
        获取邮件列表

        Args:
            token: Bearer token
            page: 页码
        """
        response = await self.client.get(
            "/messages",
            params={"page": page},
            headers=self._auth_headers(token)
        )
        response.raise_for_status()
        data = response.json()
        return data.get("hydra:member", [])

    async def get_message(self, token: str, message_id: str) -> dict:
        """
        获取邮件详情

        Args:
            token: Bearer token
            message_id: 邮件 ID
        """
        response = await self.client.get(
            f"/messages/{message_id}",
            headers=self._auth_headers(token)
        )
        response.raise_for_status()
        return response.json()

    async def wait_for_message(
        self,
        token: str,
        timeout: int,
        poll_interval: int,
        subject_keywords: Optional[List[str]] = None,
        sender_keywords: Optional[List[str]] = None
    ) -> dict:
        """
        轮询等待匹配条件的邮件

        Args:
            token: Bearer token
            timeout: 最大等待时间(秒)
            poll_interval: 轮询间隔(秒)
            subject_keywords: 主题关键词列表
            sender_keywords: 发件人关键词列表
        """
        end_time = time.monotonic() + timeout
        subject_keywords = [k.lower() for k in (subject_keywords or []) if k]
        sender_keywords = [k.lower() for k in (sender_keywords or []) if k]

        while time.monotonic() < end_time:
            messages = await self.list_messages(token)
            for message in messages:
                if self._match_message(message, subject_keywords, sender_keywords):
                    message_id = message.get("id")
                    if message_id:
                        return await self.get_message(token, message_id)

            await asyncio.sleep(poll_interval)

        raise TimeoutError("获取邮箱邮件超时")

    async def _get_token(self, address: str, password: str) -> str:
        """获取邮箱访问令牌"""
        response = await self.client.post(
            "/token",
            json={
                "address": address,
                "password": password
            }
        )
        response.raise_for_status()
        data = response.json()

        token = data.get("token")
        if not token:
            raise RuntimeError("获取临时邮箱令牌失败")
        return token

    def _auth_headers(self, token: str) -> dict:
        return {"Authorization": f"Bearer {token}"}

    def _pick_domain(self, domains: List[dict]) -> Optional[str]:
        for item in domains:
            if item.get("isActive") and not item.get("isPrivate", False):
                return item.get("domain")
        if domains:
            return domains[0].get("domain")
        return None

    def _match_message(
        self,
        message: dict,
        subject_keywords: List[str],
        sender_keywords: List[str]
    ) -> bool:
        subject = (message.get("subject") or "").lower()
        sender = (message.get("from") or {}).get("address") or ""
        sender = sender.lower()

        if subject_keywords and not any(keyword in subject for keyword in subject_keywords):
            return False
        if sender_keywords and not any(keyword in sender for keyword in sender_keywords):
            return False
        return True

    def _generate_username(self, length: int = 10) -> str:
        alphabet = string.ascii_lowercase + string.digits
        return "u" + "".join(secrets.choice(alphabet) for _ in range(length))

    def _generate_password(self, length: int = 16) -> str:
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))
