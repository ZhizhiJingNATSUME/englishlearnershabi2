@echo off
setlocal

cd /d "%~dp0"

set PYTHON_EXE=%~dp0venv\Scripts\python.exe
set BACKEND_PY=%~dp0start_backend.py

echo Using Python:
echo %PYTHON_EXE%
echo.

if not exist "%PYTHON_EXE%" (
    echo ERROR: python.exe not found
    pause
    exit /b 1
)

if not exist "%BACKEND_PY%" (
    echo ERROR: start_backend.py not found
    pause
    exit /b 1
)

call "%PYTHON_EXE%" "%BACKEND_PY%"

echo.
echo Backend exited.
pause
