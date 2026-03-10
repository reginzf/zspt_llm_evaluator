#!/bin/bash
# AI-KEN 部署诊断脚本

echo "===================================="
echo "  AI-KEN 部署诊断"
echo "===================================="
echo ""

# 检查后端服务
echo "[1/4] 检查 Flask 后端服务..."
if curl -s http://127.0.0.1:5001/local_knowledge/list > /dev/null 2>&1; then
    echo "  ✓ 后端服务在 127.0.0.1:5001 运行正常"
else
    echo "  ✗ 后端服务未运行或无法访问"
    echo "    请运行: python scripts/start_backend.py --host 0.0.0.0 --port 5001"
fi
echo ""

# 检查前端环境变量
echo "[2/4] 检查前端环境变量..."
cd frontend

if [ -f ".env.development.local" ]; then
    echo "  ✓ .env.development.local 存在"
    echo "    内容:"
    cat .env.development.local | grep -E "^VITE_" | sed 's/^/      /'
else
    echo "  ⚠ .env.development.local 不存在，使用默认配置"
    echo "    VITE_BACKEND_URL: $(grep VITE_BACKEND_URL .env.development 2>/dev/null || echo 'http://127.0.0.1:5001')"
fi
echo ""

# 检查 node_modules
echo "[3/4] 检查前端依赖..."
if [ -d "node_modules" ]; then
    echo "  ✓ node_modules 存在"
else
    echo "  ✗ node_modules 不存在，需要运行 npm install"
fi
echo ""

# 检查 vite.config.ts
echo "[4/4] 检查 Vite 配置..."
if grep -q "loadEnv(mode, process.cwd())" vite.config.ts; then
    echo "  ✓ vite.config.ts loadEnv 配置正确"
else
    echo "  ⚠ vite.config.ts loadEnv 配置可能需要更新"
fi
echo ""

echo "===================================="
echo "  诊断完成"
echo "===================================="
echo ""
echo "常见问题和解决方案:"
echo ""
echo "1. 如果后端未运行:"
echo "   export CORS_ALLOW_ALL=true"
echo "   python scripts/start_backend.py --host 0.0.0.0 --port 5001"
echo ""
echo "2. 如果前端代理不生效:"
echo "   在 frontend/.env.development.local 中设置:"
echo "   VITE_BACKEND_URL=http://\$(hostname -I | awk '{print \$1}'):5001"
echo ""
echo "3. 重启前端服务:"
echo "   cd frontend && npm run dev"
echo ""
