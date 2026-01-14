@echo off
setlocal EnableExtensions

cd /d "%~dp0"

set "ROOT=%~dp0"
set "LOG=%ROOT%run_log.txt"

echo ==== %date% %time% ==== > "%LOG%"
echo Project dir: %cd%>> "%LOG%"

REM --- Find venv python ---
set "VENV_PY="
if exist "%ROOT%venv\Scripts\python.exe" set "VENV_PY=%ROOT%venv\Scripts\python.exe"
if not defined VENV_PY if exist "%ROOT%.venv\Scripts\python.exe" set "VENV_PY=%ROOT%.venv\Scripts\python.exe"

if not defined VENV_PY (
  echo [ERROR] venv python not found.>> "%LOG%"
  echo [ERROR] venv python not found.
  pause
  exit /b 1
)

REM --- Check npm ---
where npm >nul 2>&1
if errorlevel 1 (
  echo [ERROR] npm not found.>> "%LOG%"
  echo [ERROR] npm not found. Install Node.js.
  pause
  exit /b 1
)

REM --- Install Python deps ---
if exist "%ROOT%requirements.txt" (
  "%VENV_PY%" -m pip install -r "%ROOT%requirements.txt" >> "%LOG%" 2>&1
)

REM --- Install frontend deps if needed ---
if not exist "%ROOT%frontend\node_modules\" (
  pushd "%ROOT%frontend"
  call npm install >> "%LOG%" 2>&1
  popd
)

echo Starting BACKEND and FRONTEND...

REM --- Backend: force UTF-8 + Python UTF-8 output ---
start "Backend" cmd /k "chcp 65001>nul & set PYTHONIOENCODING=utf-8 & ""%VENV_PY%"" ""%ROOT%start_backend.py"" & echo. & echo Backend exited. Press any key... & pause"

REM --- Frontend: force UTF-8 + run dev server ---
start "Frontend" cmd /k "chcp 65001>nul & cd /d ""%ROOT%frontend"" & npm run dev & echo. & echo Frontend exited. Press any key... & pause"

echo If something fails, open "%LOG%"
pause
endlocal
