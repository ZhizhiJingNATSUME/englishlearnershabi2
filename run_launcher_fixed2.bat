@echo off
setlocal EnableExtensions

REM Writes output to run.log and opens it so errors never "flash and disappear".

set "ROOT=%~dp0"
set "LOG=%ROOT%run.log"

chcp 65001 >nul

call :MAIN > "%LOG%" 2>&1

echo.
echo ===== Launcher finished =====
echo Log saved to: "%LOG%"
start "" notepad "%LOG%"
echo.
pause
exit /b

:MAIN
echo === INFO ===
echo Script location: "%ROOT%"
echo Current dir:     "%cd%"
echo Date/Time:       %date% %time%
echo.

cd /d "%ROOT%" || (echo ERROR: Could not cd into script folder. & exit /b 1)

echo === CHECK: python ===
where python || (echo ERROR: python not found in PATH. & exit /b 1)
python --version
echo.

echo === CHECK: node/npm ===
where node || echo WARN: node not found in PATH.
where npm  || echo WARN: npm not found in PATH.
node --version

REM IMPORTANT: npm is a .cmd (batch) file. From inside a .bat, you MUST use CALL or your script gets replaced.
call npm --version
echo.

echo === CHECK: project files ===
if exist "%ROOT%start_backend.py" (echo OK: start_backend.py) else (echo ERROR: start_backend.py missing)
if exist "%ROOT%requirements.txt" (echo OK: requirements.txt) else (echo WARN: requirements.txt missing)
if exist "%ROOT%frontend\" (echo OK: frontend folder) else (echo ERROR: frontend folder missing)
if exist "%ROOT%frontend\package.json" (echo OK: frontend\package.json) else (echo WARN: frontend\package.json missing)
echo.

echo === RUN: backend ===
python start_backend.py
echo Backend exit code: %errorlevel%
echo.

echo === RUN: frontend ===
if not exist "%ROOT%frontend\" (
  echo Skipping frontend: folder not found.
  exit /b 1
)

cd /d "%ROOT%frontend" || (echo ERROR: could not cd into frontend folder. & exit /b 1)

if not exist "%ROOT%frontend\node_modules\" (
  echo node_modules not found, running npm install...
  call npm install
)

echo Starting Vite dev server...
call npm run dev
echo Frontend exit code: %errorlevel%
echo.

exit /b 0
