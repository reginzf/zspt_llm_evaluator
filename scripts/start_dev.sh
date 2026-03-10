#!/bin/bash
# AI-KEN 开发环境一键启动脚本
# 使用: ./scripts/start_dev.sh

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${GREEN}====================================${NC}"
echo -e "${GREEN}  AI-KEN 开发环境启动脚本${NC}"
echo -e "${GREEN}====================================${NC}"

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}[WARN] 虚拟环境不存在，正在创建...${NC}"
    python3 -m venv .venv
fi

# 激活虚拟环境
echo -e "${GREEN}[1/4] 激活虚拟环境...${NC}"
source .venv/bin/activate

# 安装依赖
echo -e "${GREEN}[2/4] 检查 Python 依赖...${NC}"
pip install -q flask flask-cors psycopg2-binary 2>/dev/null || true

# 设置环境变量
export CORS_ALLOW_ALL=true
export FLASK_HOST=0.0.0.0
export FLASK_PORT=5001

echo -e "${GREEN}[3/4] 启动 Flask 后端...${NC}"
echo -e "${YELLOW}后端服务将在 http://0.0.0.0:5001 启动${NC}"
echo ""

# 后台启动后端
python scripts/start_backend.py --host 0.0.0.0 --port 5001 &
BACKEND_PID=$!

# 等待后端启动
sleep 3

# 检查后端是否成功启动
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${RED}[ERROR] 后端启动失败${NC}"
    exit 1
fi

echo -e "${GREEN}[4/4] 启动 Vue 前端...${NC}"
echo -e "${YELLOW}前端服务将在 http://localhost:5173 启动${NC}"
echo ""

# 进入前端目录
cd frontend

# 检查 node_modules
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}[WARN] node_modules 不存在，正在安装...${NC}"
    npm install
fi

# 启动前端
echo -e "${GREEN}====================================${NC}"
echo -e "${GREEN}  服务启动完成！${NC}"
echo -e "${GREEN}====================================${NC}"
echo ""
echo "  前端: http://localhost:5173"
echo "  后端: http://localhost:5001"
echo ""
echo "  按 Ctrl+C 停止服务"
echo ""

# 捕获中断信号，停止后端
trap "echo ''; echo -e '${YELLOW}正在停止服务...${NC}'; kill $BACKEND_PID 2>/dev/null; exit 0" INT

npm run dev
