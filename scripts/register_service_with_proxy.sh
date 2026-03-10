#!/bin/bash

# AI-KEN Application Service Registration Script for CentOS with Proxy Support
# 前后端分离部署：ai-ken-backend (Flask API, 端口5001) + ai-ken-frontend (Nginx, 端口5002)

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 函数：打印带颜色的信息
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_message ${BLUE} "=== AI-KEN 前后端分离服务注册 (CentOS) ==="

# 获取当前工作目录
PROJECT_DIR=$(pwd)
print_message ${GREEN} "当前项目目录: $PROJECT_DIR"

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    print_message ${RED} "错误: 未找到虚拟环境目录 (venv)"
    print_message ${YELLOW} "请先运行初始化脚本创建虚拟环境"
    exit 1
fi

# 检查Python版本
PYTHON_PATH=""

if [ -f "$PROJECT_DIR/venv/bin/python3.12" ]; then
    PYTHON_PATH="$PROJECT_DIR/venv/bin/python3.12"
    print_message ${GREEN} "找到Python 3.12: $PYTHON_PATH"
elif [ -f "$PROJECT_DIR/venv/bin/python3.10" ]; then
    PYTHON_PATH="$PROJECT_DIR/venv/bin/python3.10"
    print_message ${GREEN} "找到Python 3.10: $PYTHON_PATH"
else
    PYTHON_PATH=$(find "$PROJECT_DIR/venv/bin" -name "python3.*" | head -n 1)
    if [ -z "$PYTHON_PATH" ]; then
        PYTHON_PATH="$PROJECT_DIR/venv/bin/python3"
        if [ ! -f "$PYTHON_PATH" ]; then
            print_message ${RED} "错误: 未找到Python可执行文件"
            exit 1
        fi
    fi
    print_message ${YELLOW} "使用找到的Python版本: $PYTHON_PATH"
fi

# 获取当前用户
CURRENT_USER=$(whoami)
print_message ${GREEN} "当前用户: $CURRENT_USER"

# 尝试从环境变量或配置文件中获取代理设置
PROXY_HTTP=""
PROXY_HTTPS=""

# 检查环境变量
if [ -n "$http_proxy" ]; then
    PROXY_HTTP=$http_proxy
    print_message ${GREEN} "检测到HTTP代理: $PROXY_HTTP"
fi

if [ -n "$https_proxy" ]; then
    PROXY_HTTPS=$https_proxy
    print_message ${GREEN} "检测到HTTPS代理: $PROXY_HTTPS"
fi

# 如果环境变量中没有代理，询问用户
if [ -z "$PROXY_HTTP" ] && [ -z "$PROXY_HTTPS" ]; then
    print_message ${YELLOW} "未检测到代理设置"
    read -p "请输入HTTP代理 (例如: http://proxy.company.com:8080): " PROXY_HTTP
    read -p "请输入HTTPS代理 (例如: http://proxy.company.com:8080): " PROXY_HTTPS
fi

# ==================== 初始化：Node.js 安装/升级 ====================
print_message ${BLUE} "=== 检查并安装/升级 Node.js ==="

# 需要的 Node.js 版本
REQUIRED_NODE_VERSION="20"
NEED_INSTALL_NODE=false

# 检查 Node.js 是否已安装
if command -v node &> /dev/null; then
    CURRENT_NODE_VERSION=$(node --version)
    print_message ${YELLOW} "当前 Node.js 版本: $CURRENT_NODE_VERSION"
    
    # 提取主版本号
    CURRENT_MAJOR=$(echo $CURRENT_NODE_VERSION | cut -d'v' -f2 | cut -d'.' -f1)
    
    if [ "$CURRENT_MAJOR" -lt "$REQUIRED_NODE_VERSION" ]; then
        print_message ${YELLOW} "Node.js 版本过低，需要升级到 ${REQUIRED_NODE_VERSION}.x"
        NEED_INSTALL_NODE=true
    else
        print_message ${GREEN} "Node.js 版本符合要求: $CURRENT_NODE_VERSION"
    fi
else
    print_message ${YELLOW} "Node.js 未安装，开始安装..."
    NEED_INSTALL_NODE=true
fi

# 安装/升级 Node.js
if [ "$NEED_INSTALL_NODE" = true ]; then
    print_message ${BLUE} "彻底清理旧版本 Node.js..."
    
    # 完全卸载旧版本
    sudo yum remove -y nodejs npm nodesource-release || true
    sudo yum autoremove -y || true
    
    # 删除所有 NodeSource 仓库配置
    sudo rm -rf /etc/yum.repos.d/nodesource*.repo
    sudo rm -rf /etc/yum.repos.d/nodesource-*.repo
    
    # 清理 yum 缓存
    print_message ${BLUE} "清理 yum 缓存..."
    sudo yum clean all
    sudo yum makecache
    
    # 删除旧的可执行文件
    sudo rm -f /usr/bin/node
    sudo rm -f /usr/bin/npm
    sudo rm -f /usr/local/bin/node
    sudo rm -f /usr/local/bin/npm
    
    print_message ${BLUE} "使用 NodeSource 安装 Node.js 20.x..."
    
    # 设置代理（如果有）用于下载 NodeSource 安装脚本
    CURL_PROXY_ARG=""
    if [ -n "$PROXY_HTTP" ]; then
        CURL_PROXY_ARG="--proxy $PROXY_HTTP"
    fi
    
    # 下载并运行 NodeSource 安装脚本
    print_message ${BLUE} "配置 NodeSource 仓库..."
    curl $CURL_PROXY_ARG -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
    
    # 再次清理缓存，确保使用新仓库
    sudo yum clean all
    sudo yum makecache
    
    # 安装 Node.js
    print_message ${BLUE} "安装 Node.js 20.x..."
    sudo yum install -y nodejs
    
    # 验证安装
    NODE_VERSION=$(node --version)
    NPM_VERSION=$(npm --version)
    print_message ${GREEN} "Node.js 安装成功: $NODE_VERSION"
    print_message ${GREEN} "npm 安装成功: $NPM_VERSION"
    
    # 验证版本是否正确
    INSTALLED_MAJOR=$(echo $NODE_VERSION | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$INSTALLED_MAJOR" -lt "$REQUIRED_NODE_VERSION" ]; then
        print_message ${RED} "错误: Node.js 版本仍低于 ${REQUIRED_NODE_VERSION}.x，安装失败"
        print_message ${YELLOW} "尝试使用备选方案安装..."
        
        # 备选方案：从官方二进制包安装
        print_message ${BLUE} "从 Node.js 官方二进制包安装..."
        
        # 下载并解压 Node.js 20.x
        NODE_TARBALL="node-v20.19.0-linux-x64.tar.xz"
        NODE_URL="https://nodejs.org/dist/v20.19.0/${NODE_TARBALL}"
        
        cd /tmp
        curl $CURL_PROXY_ARG -fsSL "$NODE_URL" -o "$NODE_TARBALL"
        sudo tar -xJf "$NODE_TARBALL" -C /usr/local --strip-components=1
        rm -f "$NODE_TARBALL"
        cd "$PROJECT_DIR"
        
        # 创建符号链接
        sudo ln -sf /usr/local/bin/node /usr/bin/node
        sudo ln -sf /usr/local/bin/npm /usr/bin/npm
        sudo ln -sf /usr/local/bin/npx /usr/bin/npx
        
        # 验证
        NODE_VERSION=$(node --version)
        NPM_VERSION=$(npm --version)
        print_message ${GREEN} "Node.js 安装成功: $NODE_VERSION"
        print_message ${GREEN} "npm 安装成功: $NPM_VERSION"
    fi
fi

# 升级 npm 到与 Node 20 兼容的版本 (10.x)
print_message ${BLUE} "升级 npm 到兼容版本..."
if [ -n "$PROXY_HTTP" ]; then
    npm config set proxy "$PROXY_HTTP"
fi
if [ -n "$PROXY_HTTPS" ]; then
    npm config set https-proxy "$PROXY_HTTPS"
fi

# 安装与 Node 20 兼容的 npm 10.x，而不是最新的 11.x
sudo npm install -g npm@10
print_message ${GREEN} "npm 升级完成: $(npm --version)"

# 检查 node 和 npm 是否可用
if ! command -v node &> /dev/null; then
    print_message ${RED} "错误: Node.js 未正确安装"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    print_message ${RED} "错误: npm 未正确安装"
    exit 1
fi

# ==================== 初始化：前端依赖安装和构建 ====================
print_message ${BLUE} "=== 安装前端依赖并构建 ==="

if [ -d "$PROJECT_DIR/frontend" ]; then
    cd "$PROJECT_DIR/frontend"
    
    # 配置 npm 代理（如果设置了代理）
    if [ -n "$PROXY_HTTP" ]; then
        print_message ${BLUE} "配置 npm HTTP 代理..."
        npm config set proxy "$PROXY_HTTP"
    fi
    
    if [ -n "$PROXY_HTTPS" ]; then
        print_message ${BLUE} "配置 npm HTTPS 代理..."
        npm config set https-proxy "$PROXY_HTTPS"
    fi
    
    # 清理旧的构建和依赖（确保干净安装）
    print_message ${YELLOW} "清理旧的构建文件和 node_modules..."
    rm -rf "$PROJECT_DIR/frontend/dist"
    rm -rf "$PROJECT_DIR/frontend/node_modules"
    rm -f "$PROJECT_DIR/frontend/package-lock.json"
    
    # 安装依赖
    print_message ${BLUE} "运行 npm install..."
    npm install
    
    print_message ${GREEN} "前端依赖安装完成"
    
    # 构建前端
    print_message ${BLUE} "=== 构建 Vue3 前端（生产模式）==="
    
    # 设置构建环境变量（生产模式 - 前后端分离）
    export NODE_ENV=production
    export VITE_API_BASE_URL=""  # 空字符串表示使用相对路径，Nginx会代理到后端
    
    print_message ${BLUE} "运行 npm run build..."
    # 先尝试正常构建，如果失败则跳过 type-check 直接构建
    if ! npm run build; then
        print_message ${YELLOW} "TypeScript 检查失败，尝试跳过类型检查直接构建..."
        npm run build-only
    fi
    
    # 验证构建结果
    if [ -d "$PROJECT_DIR/frontend/dist" ] && [ -f "$PROJECT_DIR/frontend/dist/index.html" ]; then
        print_message ${GREEN} "前端构建成功: frontend/dist"
        print_message ${GREEN} "构建文件列表:"
        ls -la "$PROJECT_DIR/frontend/dist/"
    else
        print_message ${RED} "错误: 前端构建失败，dist 目录或 index.html 不存在"
        exit 1
    fi
    
    # 返回项目根目录
    cd "$PROJECT_DIR"
else
    print_message ${RED} "错误: 未找到 frontend 目录"
    exit 1
fi

# ==================== 安装并配置 Nginx ====================
print_message ${BLUE} "=== 安装并配置 Nginx ==="

# 检查 Nginx 是否已安装
if ! command -v nginx &> /dev/null; then
    print_message ${YELLOW} "Nginx 未安装，开始安装..."
    sudo yum install -y nginx
    print_message ${GREEN} "Nginx 安装完成"
else
    print_message ${GREEN} "Nginx 已安装: $(nginx -v 2>&1)"
fi

# 创建 Nginx 配置文件
NGINX_CONF="/etc/nginx/conf.d/ai-ken.conf"

print_message ${BLUE} "创建 Nginx 配置文件: $NGINX_CONF"

sudo tee $NGINX_CONF > /dev/null <<EOF
# AI-KEN 前后端分离 Nginx 配置
# 前端端口: 5002
# 后端端口: 5001

# 前端服务
server {
    listen 5002;
    server_name localhost;
    
    # 前端静态文件目录
    root $PROJECT_DIR/frontend/dist;
    index index.html;
    
    # 启用 gzip 压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
    
    # 前端路由支持 (Vue Router history 模式)
    location / {
        try_files \$uri \$uri/ /index.html;
    }
    
    # 静态文件缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # 代理 API 请求到后端 (5001端口)
    location /api/ {
        proxy_pass http://127.0.0.1:5001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
    
    # 代理其他后端路由
    location /local_knowledge/ {
        proxy_pass http://127.0.0.1:5001;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
    
    location /environment/ {
        proxy_pass http://127.0.0.1:5001;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
    
    location /label_studio/ {
        proxy_pass http://127.0.0.1:5001;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
    
    location /qdrant/ {
        proxy_pass http://127.0.0.1:5001;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
    
    # 健康检查端点
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

if [ $? -eq 0 ]; then
    print_message ${GREEN} "Nginx 配置文件创建成功"
else
    print_message ${RED} "错误: Nginx 配置文件创建失败"
    exit 1
fi

# 测试 Nginx 配置
print_message ${BLUE} "测试 Nginx 配置..."
if sudo nginx -t; then
    print_message ${GREEN} "Nginx 配置测试通过"
else
    print_message ${RED} "错误: Nginx 配置测试失败"
    exit 1
fi

# ==================== 创建 Systemd 服务：后端 ====================
print_message ${BLUE} "=== 创建后端服务 (ai-ken-backend) ==="

BACKEND_SERVICE="/etc/systemd/system/ai-ken-backend.service"

print_message ${BLUE} "创建服务文件: $BACKEND_SERVICE"

sudo tee $BACKEND_SERVICE > /dev/null <<EOF
[Unit]
Description=AI-KEN Backend Service (Flask API)
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
Environment=HTTP_PROXY=$PROXY_HTTP
Environment=http_proxy=$PROXY_HTTP
Environment=HTTPS_PROXY=$PROXY_HTTPS
Environment=https_proxy=$PROXY_HTTPS
Environment=FLASK_ENV=production
Environment=CORS_ALLOW_ALL=false
# 生产模式：不使用 debug，只监听 localhost（通过 Nginx 代理访问）
ExecStart=$PROJECT_DIR/venv/bin/python app.py --host 127.0.0.1 --port 5001
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

if [ $? -eq 0 ]; then
    print_message ${GREEN} "后端服务文件创建成功"
else
    print_message ${RED} "错误: 后端服务文件创建失败"
    exit 1
fi

# ==================== 创建 Systemd 服务：前端 (Nginx) ====================
print_message ${BLUE} "=== 创建前端服务 (ai-ken-frontend) ==="

FRONTEND_SERVICE="/etc/systemd/system/ai-ken-frontend.service"

print_message ${BLUE} "创建服务文件: $FRONTEND_SERVICE"

sudo tee $FRONTEND_SERVICE > /dev/null <<EOF
[Unit]
Description=AI-KEN Frontend Service (Nginx)
After=network.target ai-ken-backend.service
Requires=ai-ken-backend.service

[Service]
Type=forking
PIDFile=/run/nginx.pid
ExecStartPre=/usr/sbin/nginx -t
ExecStart=/usr/sbin/nginx
ExecReload=/usr/sbin/nginx -s reload
ExecStop=/bin/kill -s QUIT \$MAINPID
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

if [ $? -eq 0 ]; then
    print_message ${GREEN} "前端服务文件创建成功"
else
    print_message ${RED} "错误: 前端服务文件创建失败"
    exit 1
fi

# ==================== 重新加载 Systemd 配置 ====================
print_message ${BLUE} "重新加载 systemd 配置..."
sudo systemctl daemon-reload

if [ $? -eq 0 ]; then
    print_message ${GREEN} "systemd 配置重新加载成功"
else
    print_message ${RED} "错误: systemd 配置重新加载失败"
    exit 1
fi

# ==================== 停止并清理旧服务 ====================
print_message ${BLUE} "=== 停止并清理旧服务 ==="

# 停止旧服务（如果存在）
if sudo systemctl list-unit-files | grep -q "^ai-ken.service"; then
    print_message ${YELLOW} "检测到旧版 ai-ken.service，正在停止并禁用..."
    sudo systemctl stop ai-ken.service 2>/dev/null || true
    sudo systemctl disable ai-ken.service 2>/dev/null || true
    sudo rm -f /etc/systemd/system/ai-ken.service
    print_message ${GREEN} "旧版服务已清理"
fi

# 停止可能正在运行的进程
pkill -f "app.py" 2>/dev/null || true
sleep 2

# ==================== 启用并启动新服务 ====================
print_message ${BLUE} "=== 启用并启动服务 ==="

# 启用后端服务
print_message ${BLUE} "启用后端服务 (ai-ken-backend)..."
sudo systemctl enable ai-ken-backend.service

# 启用前端服务
print_message ${BLUE} "启用前端服务 (ai-ken-frontend)..."
sudo systemctl enable ai-ken-frontend.service

# 启动后端服务
print_message ${BLUE} "启动后端服务..."
sudo systemctl start ai-ken-backend.service

# 等待后端启动
print_message ${BLUE} "等待后端服务启动 (5秒)..."
sleep 5

# 检查后端服务状态
if sudo systemctl is-active --quiet ai-ken-backend.service; then
    print_message ${GREEN} "后端服务启动成功"
else
    print_message ${RED} "错误: 后端服务启动失败，查看日志："
    sudo journalctl -u ai-ken-backend.service --no-pager -n 20
    exit 1
fi

# 启动前端服务（Nginx）
print_message ${BLUE} "启动前端服务 (Nginx)..."
sudo systemctl start ai-ken-frontend.service

# 等待前端启动
sleep 2

# 检查前端服务状态
if sudo systemctl is-active --quiet ai-ken-frontend.service; then
    print_message ${GREEN} "前端服务启动成功"
else
    print_message ${RED} "错误: 前端服务启动失败，查看日志："
    sudo journalctl -u ai-ken-frontend.service --no-pager -n 20
    exit 1
fi

# ==================== 服务状态检查 ====================
print_message ${BLUE} "=== 服务状态检查 ==="

print_message ${BLUE} "后端服务状态:"
sudo systemctl status ai-ken-backend.service --no-pager -l

echo ""
print_message ${BLUE} "前端服务状态:"
sudo systemctl status ai-ken-frontend.service --no-pager -l

# ==================== 完成提示 ====================
echo ""
print_message ${GREEN} "=========================================="
print_message ${GREEN} "=== 前后端分离部署完成 ==="
print_message ${GREEN} "=========================================="
echo ""
print_message ${GREEN} "服务信息:"
print_message ${GREEN} "  后端服务: ai-ken-backend"
print_message ${GREEN} "    - 端口: 5001 (仅监听 127.0.0.1)"
print_message ${GREEN} "    - 路径: $PROJECT_DIR"
print_message ${GREEN} "    - Python: $PYTHON_PATH"
print_message ${GREEN} ""
print_message ${GREEN} "  前端服务: ai-ken-frontend"
print_message ${GREEN} "    - 端口: 5002"
print_message ${GREEN} "    - Nginx: 提供静态文件 + API 代理"
print_message ${GREEN} "    - 静态文件: $PROJECT_DIR/frontend/dist"
print_message ${GREEN} ""
print_message ${GREEN} "访问地址:"
print_message ${GREEN} "  前端: http://$(hostname -I | awk '{print $1}'):5002"
print_message ${GREEN} "  API : http://$(hostname -I | awk '{print $1}'):5002/api/"
print_message ${GREEN} ""
print_message ${GREEN} "代理配置:"
print_message ${GREEN} "  HTTP代理:  $PROXY_HTTP"
print_message ${GREEN} "  HTTPS代理: $PROXY_HTTPS"
print_message ${GREEN} ""
print_message ${GREEN} "常用管理命令:"
print_message ${GREEN} "  查看状态:"
print_message ${GREEN} "    sudo systemctl status ai-ken-backend"
print_message ${GREEN} "    sudo systemctl status ai-ken-frontend"
print_message ${GREEN} ""
print_message ${GREEN} "  启动服务:"
print_message ${GREEN} "    sudo systemctl start ai-ken-backend"
print_message ${GREEN} "    sudo systemctl start ai-ken-frontend"
print_message ${GREEN} ""
print_message ${GREEN} "  停止服务:"
print_message ${GREEN} "    sudo systemctl stop ai-ken-backend"
print_message ${GREEN} "    sudo systemctl stop ai-ken-frontend"
print_message ${GREEN} ""
print_message ${GREEN} "  重启服务:"
print_message ${GREEN} "    sudo systemctl restart ai-ken-backend"
print_message ${GREEN} "    sudo systemctl restart ai-ken-frontend"
print_message ${GREEN} ""
print_message ${GREEN} "  查看日志:"
print_message ${GREEN} "    sudo journalctl -u ai-ken-backend -f"
print_message ${GREEN} "    sudo journalctl -u ai-ken-frontend -f"
print_message ${GREEN} ""
print_message ${YELLOW} "注意:"
print_message ${YELLOW} "  1. 后端服务仅监听 127.0.0.1:5001，外部访问需通过 Nginx (5002端口)"
print_message ${YELLOW} "  2. Nginx 配置了 API 代理，所有 /api/* 请求会转发到后端"
print_message ${YELLOW} "  3. 前端服务依赖于后端服务，启动时会自动启动后端"
print_message ${YELLOW} "  4. 如需修改代理配置，编辑服务文件后执行: sudo systemctl daemon-reload"
