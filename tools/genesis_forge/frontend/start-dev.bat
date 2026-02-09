@echo off
echo Starting Genesis Forge Studio Frontend...
echo.

cd /d "%~dp0"

echo Installing dependencies...
call npm install

echo.
echo Starting development server...
echo.
echo Frontend will be available at: http://localhost:3000
echo Backend should be running at: http://localhost:5000
echo.

call npm run dev

pause