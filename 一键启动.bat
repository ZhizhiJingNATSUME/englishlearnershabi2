@echo off
chcp 65001 > nul
title 英语学习平台 - 一键启动

echo ============================================================
echo    🚀 英语学习平台 - 一键启动
echo ============================================================
echo.

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

echo 📦 启动步骤:
echo   1️⃣  启动后端服务 (Flask on :5000)
echo   2️⃣  启动前端服务 (Vite on :5173)
echo.
echo ============================================================
echo.

REM 启动后端 - 使用PowerShell以确保conda环境正确加载
echo [1/2] 🔧 启动后端服务...
start "后端服务 - Flask :5000" powershell -NoExit -Command "cd '%PROJECT_DIR%'; python start_backend.py"

echo ⏳ 等待后端启动 (约10秒)...
timeout /t 10 > nul

echo 🔍 检查后端服务状态...
curl -s http://localhost:5000/api/health > nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 后端服务启动成功！
) else (
    echo ⚠️  后端服务可能未完全启动，请查看后端窗口
)

echo.
echo [2/2] 🎨 启动前端服务...
cd "%PROJECT_DIR%frontend"
start "前端服务 - Vite :5173" powershell -NoExit -Command "cd '%PROJECT_DIR%frontend'; npm run dev"

cd "%PROJECT_DIR%"

echo.
echo ============================================================
echo ✅ 所有服务已启动！
echo ============================================================
echo.
echo 📌 访问地址:
echo   前端: http://localhost:5173
echo   后端: http://localhost:5000
echo.
echo 💡 提示:
echo   • 两个PowerShell窗口已打开
echo   • 关闭窗口或按 Ctrl+C 可停止服务
echo.
echo 按任意键关闭此窗口...
pause > nul
