@echo off
REM Windows启动脚本

echo Starting English Learning App Server...

REM 激活虚拟环境（如果存在）
if exist venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM 检查数据库是否存在
if not exist english_learning.db (
    echo Database not found. Running setup...
    python setup.py
)

REM 启动服务器
echo.
echo Starting API server on http://localhost:5000
echo Press Ctrl+C to stop
echo.
python backend/app.py

pause

