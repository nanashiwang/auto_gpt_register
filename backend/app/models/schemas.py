"""Pydantic 数据模型"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator, EmailStr
import re
from .enums import RegistrationStatus, LogLevel


class AccountModel(BaseModel):
    """账号数据模型"""
    id: Optional[int] = None
    email: EmailStr = Field(..., description="微软账号邮箱")
    password: str = Field(..., min_length=8, description="密码(加密存储)")
    recovery_email: Optional[EmailStr] = Field(None, description="备用邮箱")
    proxy_host: Optional[str] = Field(None, description="代理地址")
    proxy_port: Optional[int] = Field(None, ge=1, le=65535, description="代理端口")
    proxy_username: Optional[str] = Field(None, description="代理用户名")
    proxy_password: Optional[str] = Field(None, description="代理密码(加密)")
    status: RegistrationStatus = Field(default=RegistrationStatus.PENDING, description="注册状态")
    gpt_account_id: Optional[str] = Field(None, description="注册成功的 GPT 账号 ID")
    gpt_email: Optional[str] = Field(None, description="GPT 关联邮箱")
    error_message: Optional[str] = Field(None, description="错误信息")
    retry_count: int = Field(default=0, ge=0, description="重试次数")
    last_attempt: Optional[datetime] = Field(None, description="最后尝试时间")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    class Config:
        """Pydantic 配置"""
        use_enum_values = True


class RegistrationTask(BaseModel):
    """注册任务模型"""
    task_id: str = Field(..., description="任务ID")
    total_accounts: int = Field(..., ge=0, description="总账号数")
    completed_accounts: int = Field(default=0, ge=0, description="已完成账号数")
    success_count: int = Field(default=0, ge=0, description="成功数量")
    failed_count: int = Field(default=0, ge=0, description="失败数量")
    status: str = Field(..., description="任务状态")
    started_at: datetime = Field(default_factory=datetime.now, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    current_account_email: Optional[str] = Field(None, description="当前处理的账号邮箱")


class RegistrationLog(BaseModel):
    """注册日志模型"""
    id: Optional[int] = None
    task_id: str = Field(..., description="任务ID")
    account_email: str = Field(..., description="账号邮箱")
    level: LogLevel = Field(default=LogLevel.INFO, description="日志级别")
    message: str = Field(..., description="日志消息")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    screenshot_path: Optional[str] = Field(None, description="截图路径")


class ProxyConfig(BaseModel):
    """代理配置模型"""
    id: Optional[int] = None
    host: str = Field(..., description="代理主机地址")
    port: int = Field(..., ge=1, le=65535, description="代理端口")
    protocol: str = Field(default="http", pattern="^(http|https|socks5)$", description="代理协议")
    username: Optional[str] = Field(None, description="代理用户名")
    password: Optional[str] = Field(None, description="代理密码(加密)")
    is_active: bool = Field(default=True, description="是否启用")
    success_count: int = Field(default=0, ge=0, description="成功次数")
    fail_count: int = Field(default=0, ge=0, description="失败次数")
    last_used: Optional[datetime] = Field(None, description="最后使用时间")


class SystemConfig(BaseModel):
    """系统配置模型"""
    max_concurrent_tasks: int = Field(default=3, ge=1, le=10, description="最大并发注册数")
    max_retry_count: int = Field(default=3, ge=0, le=10, description="最大重试次数")
    captcha_service: str = Field(default="2captcha", description="验证码服务提供商")
    captcha_api_key: str = Field(..., description="验证码服务 API Key")
    screenshot_on_error: bool = Field(default=True, description="出错时截图")
    headless_mode: bool = Field(default=True, description="无头模式")
    browser_timeout: int = Field(default=30000, ge=5000, description="浏览器超时时间(毫秒)")
    log_level: LogLevel = Field(default=LogLevel.INFO, description="日志级别")
