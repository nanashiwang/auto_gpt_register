"""枚举定义模块"""
from enum import Enum


class RegistrationStatus(str, Enum):
    """注册状态枚举"""
    PENDING = "pending"  # 待注册
    IN_PROGRESS = "in_progress"  # 注册中
    SUCCESS = "success"  # 成功
    FAILED = "failed"  # 失败
    CAPTCHA_FAILED = "captcha_failed"  # 验证码失败
    PROXY_FAILED = "proxy_failed"  # 代理失败
    ACCOUNT_BANNED = "account_banned"  # 账号被封
    VERIFICATION_REQUIRED = "verification_required"  # 需��人工验证


class LogLevel(str, Enum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"  # 待执行
    RUNNING = "running"  # 运行中
    PAUSED = "paused"  # 已暂停
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消
    FAILED = "failed"  # 失败
