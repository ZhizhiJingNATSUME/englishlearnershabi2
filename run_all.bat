@echo off
setlocal EnableExtensions

chcp 65001 >nul
cd /d "%~dp0"

set "LOG=%~dp0run_log.txt"
echo ==== %date% %time% ==== > "%LOG%"
echo Project dir: %cd%>> "%LOG%"

echo.
echo ============================
echo   One-click start (venv)
echo ============================
echo Log: "%LOG%"
echo.

REM --- Find venv python ---
set "VENV_PY="
if exist "%~dp0venv\Scripts\python.exe" set "VENV_PY=%~dp0venv\Scripts\python.exe"
if not defined VENV_PY if exist "%~dp0.venv\Scripts\python.exe" set "VENV_PY=%~dp0.venv\Scripts\python.exe"

if not defined VENV_PY (
  echo [ERROR] venv python not found.
  echo Looked for:
  echo   "%~dp0venv\Scripts\python.exe"
  echo   "%~dp0.venv\Scripts\python.exe"
  echo [ERROR] venv python not found.>> "%LOG%"
  pause
  exit /b 1
)

echo Using venv python: "%VENV_PY%"
echo Using venv python: "%VENV_PY%">> "%LOG%"

REM --- Basic checks ---
if not exist "%~dp0frontend\" (
  echo [ERROR] Missing "frontend" folder.
  echo [ERROR] Missing frontend folder.>> "%LOG%"
  pause
  exit /b 1
)

if not exist "%~dp0start_backend.py" (
  echo [ERROR] Missing "start_backend.py".
  echo [ERROR] Missing start_backend.py.>> "%LOG%"
  pause
  exit /b 1
)

where npm >nul 2>&1
if errorlevel 1 (
  echo [ERROR] npm not found. Install Node.js (npm) and ensure it's in PATH.
  echo [ERROR] npm not found.>> "%LOG%"
  pause
  exit /b 1
)

REM --- Install Python deps (optional) ---
if exist "%~dp0requirements.txt" (
  echo Installing Python deps (requirements.txt)...
  "%VENV_PY%" -m pip install -r "%~dp0requirements.txt" >> "%LOG%" 2>&1
  if errorlevel 1 (
    echo [ERROR] pip install failed. Check run_log.txt
    pause
    exit /b 1
  )
) else (
  echo (No requirements.txt found, skipping pip install.)
)

REM --- Install frontend deps if needed ---
if not exist "%~dp0frontend\node_modules\" (
  echo Running npm install in frontend...
  pushd "%~dp0frontend"
  call npm install >> "%LOG%" 2>&1
  if errorlevel 1 (
    popd
    echo [ERROR] npm install failed. Check run_log.txt
    pause
    exit /b 1
  )
  popd
) else (
  echo (node_modules exists, skipping npm install.)
)

echo.
echo Starting BACKEND + FRONTEND...

REM --- Start backend (new window) ---
start "Backend" cmd /k ""%VENV_PY%" "%~dp0start_backend.py" ^& echo. ^& echo Backend exited. Press any key... ^& pause"

REM --- Start frontend (new window) ---
start "Frontend" cmd /k "cd /d "%~dp0frontend" ^& npm run dev ^& echo. ^& echo Frontend exited. Press any key... ^& pause"

echo.
echo If nothing opened, check: "%LOG%"
pause
endlocal
