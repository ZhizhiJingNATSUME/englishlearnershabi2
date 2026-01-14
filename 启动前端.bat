@echo off
chcp 65001 > nul
title 英语学习平台 - 启动前端

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%frontend"

echo ============================================================
echo    🎨 启动前端服务
echo ============================================================
echo.

call npm run dev

echo.
echo 前端服务已停止
pause
