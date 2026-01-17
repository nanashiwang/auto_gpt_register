"""日志工具模块"""
import sys
import os
from pathlib import Path
from loguru import logger
from app.config import settings


def setup_logger():
    """配置日志系统"""
    # 移除默认处理器
    logger.remove()

    # 确保日志目录存在
    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

    # 控制台输出格式
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    # 文件输出格式
    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{name}:{function}:{line} | "
        "{message}"
    )

    # 添加控制台处理器
    logger.add(
        sys.stdout,
        format=console_format,
        level=settings.LOG_LEVEL,
        colorize=True,
        enqueue=True  # 线程安全
    )

    # 添加通用日志文件处理器
    logger.add(
        log_dir / "app_{time:YYYY-MM-DD}.log",
        format=file_format,
        level=settings.LOG_LEVEL,
        rotation="00:00",  # 每天午夜轮转
        retention="30 days",  # 保留30天
        compression="zip",  # 压缩旧日志
        enqueue=True
    )

    # 添加错误日志文件处理器
    logger.add(
        log_dir / "error_{time:YYYY-MM-DD}.log",
        format=file_format,
        level="ERROR",
        rotation="00:00",
        retention="60 days",
        compression="zip",
        enqueue=True
    )

    logger.info(f"日志系统初始化完成,日志级别: {settings.LOG_LEVEL}")


def get_logger(name: str):
    """
    获取模块专用 logger

    Args:
        name: 模块名称,通常使用 __name__

    Returns:
        logger 实例
    """
    return logger.bind(name=name)


# 启动时自动配置
setup_logger()
