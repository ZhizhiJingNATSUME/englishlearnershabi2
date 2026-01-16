@echo off
setlocal EnableExtensions

REM Use only ASCII text to avoid Windows codepage/encoding problems.

cd /d "%~dp0" || (echo ERROR: Could not switch to script folder. & pause & exit /b 1)

REM Check prerequisites
where python >nul 2>nul || (
  echo ERROR: Python was not found in PATH.
  echo Install Python and make sure "Add Python to PATH" is enabled.
  pause
  exit /b 1
)

where npm >nul 2>nul || (
  echo ERROR: Node.js/npm was not found in PATH.
  echo Install Node.js (npm comes with it).
  pause
  exit /b 1
)

REM Check folders
if not exist "%~dp0frontend\" (
  echo ERROR: Folder "frontend" not found next to this .bat file.
  echo Current folder: "%~dp0"
  echo If your frontend folder has a different name, update the script accordingly.
  pause
  exit /b 1
)

REM Optional: install frontend deps if missing
if exist "%~dp0frontend\package.json" (
  if not exist "%~dp0frontend\node_modules\" (
    echo Frontend dependencies not found. Running "npm install"...
    pushd "%~dp0frontend" || (echo ERROR: Could not enter frontend folder. & pause & exit /b 1)
    npm install
    popd
  )
)

echo Starting backend (Flask :5000)...
start "Backend (Flask :5000)" cmd /k "cd /d \"%~dp0\" && python start_backend.py"

echo Waiting 3 seconds...
timeout /t 3 >nul

echo Starting frontend (Vite :5173)...
start "Frontend (Vite :5173)" cmd /k "cd /d \"%~dp0frontend\" && npm run dev"

echo.
echo Services started.
echo Frontend: http://localhost:5173
echo Backend:  http://localhost:5000
echo.
pause
