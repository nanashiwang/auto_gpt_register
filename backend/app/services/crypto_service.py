"""加密服务模块"""
import base64
import os
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CryptoService:
    """加密服务类 - 使用 Fernet 对称加密"""

    def __init__(self, secret_key: Optional[str] = None):
        """
        初始化加密服务

        Args:
            secret_key: 加密密钥,如果不提供则从环境变量读取
        """
        if secret_key:
            self.key = secret_key.encode()
        else:
            # 从环境变量或配置文件读取密钥
            self.key = os.getenv('ENCRYPTION_KEY', 'default-secret-key-change-this').encode()

        self._setup_cipher()

    def _setup_cipher(self):
        """设置加密器"""
        try:
            # 使用 PBKDF2 派生密钥
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'gpt-auto-register-salt',
                iterations=100000,
            )
            derived_key = base64.urlsafe_b64encode(kdf.derive(self.key))
            self.cipher = Fernet(derived_key)
            logger.info("加密服务初始化成功")
        except Exception as e:
            logger.error(f"加密服务初始化失败: {str(e)}")
            raise

    def encrypt(self, plaintext: str) -> str:
        """
        加密字符串

        Args:
            plaintext: 明文字符串

        Returns:
            加密后的 base64 字符串
        """
        if not plaintext:
            return ""

        try:
            encrypted = self.cipher.encrypt(plaintext.encode('utf-8'))
            return base64.urlsafe_b64encode(encrypted).decode('utf-8')
        except Exception as e:
            logger.error(f"加密失败: {str(e)}")
            raise

    def decrypt(self, ciphertext: str) -> str:
        """
        解密字符串

        Args:
            ciphertext: 加密的 base64 字符串

        Returns:
            解密后的明文字符串
        """
        if not ciphertext:
            return ""

        try:
            decoded = base64.urlsafe_b64decode(ciphertext.encode('utf-8'))
            decrypted = self.cipher.decrypt(decoded)
            return decrypted.decode('utf-8')
        except Exception as e:
            # 如果解密失败,返回原字符串(兼容未加密的旧数据)
            logger.warning(f"解密失败,返回原字符串: {str(e)}")
            return ciphertext


# 全局加密服务实例
crypto_service = CryptoService()
