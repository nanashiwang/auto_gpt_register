"""配置管理模块"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""

    # 应用基础配置
    APP_NAME: str = "GPT Auto Register"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # 数据库配置
    DATABASE_URL: str = "sqlite:///./data/database.db"

    # 加密配置
    ENCRYPTION_KEY: str = "default-secret-key-change-this-in-production"

    # 验证码服务配置
    CAPTCHA_SERVICE: str = "2captcha"  # 2captcha 或 yescaptcha
    CAPTCHA_API_KEY: str = ""

    # 注册方式配置
    REGISTRATION_MODE: str = "microsoft"  # microsoft 或 openai_email

    # 邮箱验证配置
    EMAIL_PROVIDER: str = "none"  # none 或 mailtm
    MAIL_TM_BASE_URL: str = "https://api.mail.tm"
    MAIL_TM_DOMAIN_PAGE: int = 1
    EMAIL_API_TIMEOUT: int = 30  # 秒
    EMAIL_VERIFY_TIMEOUT: int = 180  # 秒
    EMAIL_POLL_INTERVAL: int = 3  # 秒
    EMAIL_SUBJECT_KEYWORDS: str = "OpenAI,verify,verification,confirm"
    EMAIL_SENDER_KEYWORDS: str = "openai.com"

    # 浏览器配置
    HEADLESS_MODE: bool = True
    BROWSER_TIMEOUT: int = 30000  # 毫秒
    BROWSER_USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

    # 并发配置
    MAX_CONCURRENT_TASKS: int = 3
    MAX_RETRY_COUNT: int = 3

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "./logs"
    SCREENSHOT_ON_ERROR: bool = True
    SCREENSHOT_DIR: str = "./screenshots"

    # 文件路径配置
    DATA_DIR: str = "./data"
    ACCOUNTS_FILE: str = "./data/accounts.xlsx"

    # CORS 配置
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]

    # WebSocket 配置
    WS_HEARTBEAT_INTERVAL: int = 30  # 秒

    class Config:
        """Pydantic 配置"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


# 全局配置实例
settings = get_settings()
