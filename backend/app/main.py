"""FastAPI 主应用入口"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.config import settings
from app.api.routes import accounts, registration, websocket
from app.utils.logger import get_logger

logger = get_logger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="GPT 账号自动注册系统",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(accounts.router)
app.include_router(registration.router)
app.include_router(websocket.router)


@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    logger.info("=" * 50)
    logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} 启动中...")
    logger.info("=" * 50)

    # 确保必要的目录存在
    Path(settings.DATA_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.LOG_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.SCREENSHOT_DIR).mkdir(parents=True, exist_ok=True)

    logger.info(f"数据目录: {settings.DATA_DIR}")
    logger.info(f"日志目录: {settings.LOG_DIR}")
    logger.info(f"截图目录: {settings.SCREENSHOT_DIR}")
    logger.info(f"账号文件: {settings.ACCOUNTS_FILE}")

    # 检查账号文件是否存在
    from app.services.excel_service import ExcelService
    excel_service = ExcelService(settings.ACCOUNTS_FILE)

    import os
    if not os.path.exists(settings.ACCOUNTS_FILE):
        logger.warning(f"账号文件不存在: {settings.ACCOUNTS_FILE}")
        logger.info("请通过 API 导入账号或手动创建 Excel 文件")
    else:
        accounts = await excel_service.load_accounts()
        logger.info(f"已加载 {len(accounts)} 个账号")

    logger.info("=" * 50)
    logger.info("应用启动完成!")
    logger.info(f"API 文档: http://localhost:8000/docs")
    logger.info("=" * 50)


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理"""
    logger.info("=" * 50)
    logger.info("应用正在关闭...")
    logger.info("=" * 50)


@app.get("/")
async def root():
    """根路径"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
