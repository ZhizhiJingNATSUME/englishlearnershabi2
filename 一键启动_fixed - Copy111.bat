@echo off
setlocal

cd /d "%~dp0"

echo ================================
echo Starting Backend
echo ================================

REM ---- Backend ----
set PYTHON_EXE=%~dp0venv\Scripts\python.exe
set BACKEND_PY=%~dp0start_backend.py

if not exist "%PYTHON_EXE%" (
    echo ERROR: python.exe not found
    pause
    exit /b 1
)

start "Backend" cmd /k ""%PYTHON_EXE%" "%BACKEND_PY%""

echo Backend started
echo.

echo ================================
echo Starting Frontend
echo ================================

REM ---- Frontend ----
set FRONTEND_DIR=%~dp0frontend

if not exist "%FRONTEND_DIR%\package.json" (
    echo ERROR: frontend\package.json not found
    pause
    exit /b 1
)

cd /d "%FRONTEND_DIR%"

REM Detect package manager
if exist "pnpm-lock.yaml" (
    set PM=pnpm
) else if exist "yarn.lock" (
    set PM=yarn
) else (
    set PM=npm
)

echo Using %PM%

REM Install deps if needed
if not exist "node_modules" (
    echo Installing frontend dependencies...
    %PM% install
)

REM Start frontend
start "Frontend" cmd /k "%PM% run dev"

echo.
echo ================================
echo All services started
echo ================================
echo.
pause
