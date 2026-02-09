@echo off
echo ============================================================
echo   Genesis Forge Studio 启动脚本
echo ============================================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请安装Python 3.8或更高版本
    pause
    exit /b 1
)

REM 检查虚拟环境
if not exist "venv\Scripts\activate.bat" (
    echo 警告: 未找到虚拟环境，正在创建...
    python -m venv venv
    if errorlevel 1 (
        echo 错误: 创建虚拟环境失败
        pause
        exit /b 1
    )
)

REM 激活虚拟环境
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo 错误: 激活虚拟环境失败
    pause
    exit /b 1
)

REM 安装依赖
echo 正在检查依赖...
pip install -r config\requirements.txt >nul 2>&1
if errorlevel 1 (
    echo 警告: 依赖安装失败，尝试继续启动...
)

REM 创建必要的目录
echo 正在创建目录...
if not exist "logs" mkdir logs
if not exist "temp" mkdir temp

REM 启动后端服务器
echo 正在启动后端服务器...
echo.
python scripts\start_dev.py

REM 如果后端服务器退出，暂停以便查看错误
echo.
echo 后端服务器已停止
pause