@echo off
echo ============================================================
echo   Genesis Forge Studio 前端启动脚本
echo ============================================================
echo.

REM 检查Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Node.js，请安装Node.js 18或更高版本
    pause
    exit /b 1
)

REM 检查npm
npm --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到npm
    pause
    exit /b 1
)

REM 进入前端目录
cd frontend

REM 检查node_modules
if not exist "node_modules" (
    echo 正在安装依赖...
    npm install
    if errorlevel 1 (
        echo 错误: 依赖安装失败
        pause
        exit /b 1
    )
)

REM 启动开发服务器
echo 正在启动前端开发服务器...
echo.
npm run dev

REM 如果前端服务器退出，暂停以便查看错误
echo.
echo 前端开发服务器已停止
pause