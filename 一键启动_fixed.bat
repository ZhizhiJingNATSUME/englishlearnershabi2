@echo off
chcp 65001 > nul
title English Learner - One Click Start

echo ==========================================
echo   English Learner - Starting...
echo ==========================================
echo.
echo Please wait about 10 seconds.
echo Do not close this window.
echo.

REM Get project root directory
set "PROJECT_DIR=%~dp0"

REM -------- Start Backend --------
echo [1/2] Starting backend...
cd /d "%PROJECT_DIR%backend"

call venv\Scripts\activate.bat

start "Backend Server" cmd /k ^
"echo Backend is running... && python app.py"

echo Backend started at http://127.0.0.1:5000
echo.

timeout /t 6 > nul

REM -------- Start Frontend --------
echo [2/2] Starting frontend...
cd /d "%PROJECT_DIR%frontend"

start "Frontend Server" cmd /k ^
"echo Frontend is running... && npm run dev"

echo.
echo ==========================================
echo Startup finished.
echo.
echo Open browser and visit:
echo http://localhost:3000
echo ==========================================
echo.

pause
