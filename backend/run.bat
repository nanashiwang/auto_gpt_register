@echo off
REM GPT 自动注册系统 - 启动脚本

echo ========================================
echo GPT Auto Register - 启动服务
echo ========================================
echo.

REM 检查虚拟环境
if not exist "venv\Scripts\activate.bat" (
    echo [错误] 虚拟环境不存在,请先运行 setup.bat
    pause
    exit /b 1
)

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 检查 .env 文件
if not exist ".env" (
    echo [警告] .env 文件不存在
    echo 正在复制 .env.example 为 .env ...
    copy .env.example .env
    echo.
    echo [重要] 请编辑 .env 文件配置以下项:
    echo   - ENCRYPTION_KEY
    echo   - CAPTCHA_API_KEY
    echo.
    pause
)

REM 创建必要目录
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "screenshots" mkdir screenshots

REM 启动服务
echo 正在启动服务...
echo.
echo API 文档: http://localhost:8000/docs
echo ReDoc 文档: http://localhost:8000/redoc
echo.
echo 按 Ctrl+C 停止服务
echo.

python -m app.main
