#!/bin/bash

# AI-KEN Application Service Registration Script for CentOS with Proxy Support
# 此脚本用于将Python应用注册为CentOS系统服务，并配置代理
# 支持 Vue3 前端 + Flask 后端生产环境部署

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

print_message ${BLUE} "=== AI-KEN Application Service Registration with Proxy ==="

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
    
    # 设置构建环境变量（生产模式）
    export NODE_ENV=production
    
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

# ==================== 创建 Systemd 服务 ====================
print_message ${BLUE} "=== 创建 Systemd 服务 ==="

SERVICE_FILE="/etc/systemd/system/ai-ken.service"

print_message ${BLUE} "创建服务文件: $SERVICE_FILE"

# 写入服务配置，包含代理环境变量
sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=AI-KEN Application (Flask + Vue3)
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
Environment=VUE_FRONTEND_MODE=force
# 生产模式：不使用 debug
ExecStart=$PROJECT_DIR/venv/bin/python app.py --host 0.0.0.0 --port 5001
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

if [ $? -eq 0 ]; then
    print_message ${GREEN} "服务文件创建成功，包含代理配置"
else
    print_message ${RED} "错误: 服务文件创建失败"
    exit 1
fi

# 重新加载systemd配置
print_message ${BLUE} "重新加载systemd配置..."
sudo systemctl daemon-reload

if [ $? -eq 0 ]; then
    print_message ${GREEN} "systemd配置重新加载成功"
else
    print_message ${RED} "错误: systemd配置重新加载失败"
    exit 1
fi

# 启用服务（开机自启）
print_message ${BLUE} "启用服务（设置开机自启）..."
sudo systemctl enable ai-ken.service

if [ $? -eq 0 ]; then
    print_message ${GREEN} "服务已启用（开机自启）"
else
    print_message ${RED} "错误: 服务启用失败"
    exit 1
fi

# 如果服务正在运行，先停止它
if sudo systemctl is-active --quiet ai-ken.service; then
    print_message ${BLUE} "停止现有服务..."
    sudo systemctl stop ai-ken.service
fi

# 清理可能存在的旧进程
print_message ${BLUE} "清理可能存在的旧进程..."
pkill -f "app.py" || true
sleep 2

# 启动服务
print_message ${BLUE} "启动服务..."
sudo systemctl start ai-ken.service

# 等待服务启动
print_message ${BLUE} "等待服务启动 (3秒)..."
sleep 3

# 检查服务是否成功启动
if sudo systemctl is-active --quiet ai-ken.service; then
    print_message ${GREEN} "服务启动成功"
else
    print_message ${RED} "错误: 服务启动失败，查看日志："
    sudo journalctl -u ai-ken.service --no-pager -n 20
    exit 1
fi

# 检查服务状态
print_message ${BLUE} "检查服务状态..."
sudo systemctl status ai-ken.service --no-pager -l

print_message ${GREEN} "=== 服务注册完成（包含代理配置） ==="
print_message ${GREEN} "服务名称: ai-ken"
print_message ${GREEN} "端口: 5001"
print_message ${GREEN} "项目路径: $PROJECT_DIR"
print_message ${GREEN} "Python路径: $PYTHON_PATH"
print_message ${GREEN} "HTTP代理: $PROXY_HTTP"
print_message ${GREEN} "HTTPS代理: $PROXY_HTTPS"
print_message ${GREEN} "前端模式: Vue3 生产模式 (frontend/dist)"
print_message ${GREEN} ""
print_message ${GREEN} "常用管理命令:"
print_message ${GREEN} "  启动服务: sudo systemctl start ai-ken"
print_message ${GREEN} "  停止服务: sudo systemctl stop ai-ken" 
print_message ${GREEN} "  重启服务: sudo systemctl restart ai-ken"
print_message ${GREEN} "  查看状态: sudo systemctl status ai-ken"
print_message ${GREEN} "  查看日志: sudo journalctl -u ai-ken -f"
print_message ${GREEN} ""
print_message ${YELLOW} "注意: 如果代理设置不正确，可能需要修改服务文件中的代理配置"
