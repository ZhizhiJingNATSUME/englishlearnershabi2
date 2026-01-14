@echo off
chcp 65001 > nul
title 英语学习平台 - 启动后端

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

echo ============================================================
echo    🚀 启动后端服务
echo ============================================================
echo.

REM 优先使用 conda 环境的 Python
where conda >nul 2>&1
if %errorlevel% equ 0 (
    echo 使用 Conda 环境的 Python...
    call conda activate base
    python start_backend.py
) else (
    echo 使用系统默认 Python...
    python start_backend.py
)

echo.
echo 后端服务已停止
pause
