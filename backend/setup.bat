@echo off
REM GPT 自动注册系统 - 快速安装脚本

echo ========================================
echo GPT Auto Register - 安装脚本
echo ========================================
echo.

REM 检查 Python 版本
python --version
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python,请先安装 Python 3.10+
    pause
    exit /b 1
)

echo.
echo [1/5] 创建虚拟环境...
python -m venv venv
if %errorlevel% neq 0 (
    echo [错误] 创建虚拟环境失败
    pause
    exit /b 1
)

echo.
echo [2/5] 激活虚拟环境...
call venv\Scripts\activate.bat

echo.
echo [3/5] 升级 pip...
python -m pip install --upgrade pip

echo.
echo [4/5] 安装依赖包...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [错误] 安装依赖失败
    pause
    exit /b 1
)

echo.
echo [5/5] 安装 Playwright 浏览器...
playwright install chromium
if %errorlevel% neq 0 (
    echo [警告] Playwright 浏览器安装失败,请手动运行: playwright install chromium
)

echo.
echo ========================================
echo 安装完成!
echo ========================================
echo.
echo 下一步:
echo 1. 复制 .env.example 为 .env
echo 2. 编辑 .env 配置验证码服务 API Key
echo 3. 创建 data/accounts.xlsx 账号文件
echo 4. 运行: python -m app.main
echo.
echo API 文档: http://localhost:8000/docs
echo.
pause
