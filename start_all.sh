#!/bin/bash

# Faga Adaptive English Teacher - 一键启动脚本 (uv 增强版)

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # 无颜色

echo -e "${BLUE}=======================================${NC}"
echo -e "${BLUE}   Faga English Teacher Starting Up    ${NC}"
echo -e "${BLUE}=======================================${NC}"

# 获取项目根目录
PROJECT_ROOT=$(pwd)

# 确保在退出时清理所有子进程
cleanup() {
    echo -e "\n${YELLOW}Stopping services...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}All services stopped. Goodbye!${NC}"
    exit
}

trap cleanup SIGINT SIGTERM

# 1. 启动后端 (使用 uv run)
echo -e "${YELLOW}[1/2] Starting Flask Backend (uv run)...${NC}"
export PYTHONPATH=$PROJECT_ROOT
uv run python backend/app.py > backend.log 2>&1 &
BACKEND_PID=$!

# 等待后端启动检查
sleep 3
if ps -p $BACKEND_PID > /dev/null; then
    echo -e "${GREEN}✓ Backend started successfully!${NC}"
else
    echo -e "\033[0;31m✗ Backend failed to start. Check backend.log for details.\033[0m"
    # 尝试直接显示最后几行日志帮助排错
    tail -n 5 backend.log
    exit 1
fi

# 2. 启动前端
echo -e "${YELLOW}[2/2] Starting React Frontend (Port 5173)...${NC}"
cd frontend
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!

# 等待前端启动检查
sleep 3
if ps -p $FRONTEND_PID > /dev/null; then
    echo -e "${GREEN}✓ Frontend started successfully!${NC}"
else
    echo -e "\033[0;31m✗ Frontend failed to start. Check frontend.log for details.\033[0m"
    kill $BACKEND_PID
    exit 1
fi

echo -e "${BLUE}=======================================${NC}"
echo -e "${GREEN}Services are running!${NC}"
echo -e "Backend:  ${BLUE}http://localhost:5000${NC}"
echo -e "Frontend: ${BLUE}http://localhost:5173${NC}"
echo -e "Logs:     ${NC}tail -f backend.log frontend.log"
echo -e "${YELLOW}Press Ctrl+C to stop all services.${NC}"
echo -e "${BLUE}=======================================${NC}"

# 保持脚本运行
wait
