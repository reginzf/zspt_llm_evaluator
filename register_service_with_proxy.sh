#!/bin/bash

# AI-KEN Application Service Registration Script for CentOS with Proxy Support
# 此脚本用于将Python应用注册为CentOS系统服务，并配置代理

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
# 首先尝试python3.12，然后是python3.10，最后是虚拟环境中的任何python3版本
PYTHON_PATH=""

if [ -f "$PROJECT_DIR/venv/bin/python3.12" ]; then
    PYTHON_PATH="$PROJECT_DIR/venv/bin/python3.12"
    print_message ${GREEN} "找到Python 3.12: $PYTHON_PATH"
elif [ -f "$PROJECT_DIR/venv/bin/python3.10" ]; then
    PYTHON_PATH="$PROJECT_DIR/venv/bin/python3.10"
    print_message ${GREEN} "找到Python 3.10: $PYTHON_PATH"
else
    # 查找虚拟环境中的任何python3版本
    PYTHON_PATH=$(find "$PROJECT_DIR/venv/bin" -name "python3.*" | head -n 1)
    if [ -z "$PYTHON_PATH" ]; then
        # 如果还是没找到，使用python3
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

# 创建systemd服务文件
SERVICE_FILE="/etc/systemd/system/ai-ken.service"

print_message ${BLUE} "创建服务文件: $SERVICE_FILE"

# 写入服务配置，包含代理环境变量
sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=AI-KEN Application
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
# 如果需要，也可以添加其他环境变量
# Environment=NO_PROXY=localhost,127.0.0.1,.company.com
ExecStart=$PYTHON_PATH app.py --host 0.0.0.0 --port 5001
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

# 启动服务
print_message ${BLUE} "启动服务..."
sudo systemctl start ai-ken.service

if [ $? -eq 0 ]; then
    print_message ${GREEN} "服务启动成功"
else
    print_message ${RED} "错误: 服务启动失败"
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
print_message ${GREEN} ""
print_message ${GREEN} "常用管理命令:"
print_message ${GREEN} "  启动服务: sudo systemctl start ai-ken"
print_message ${GREEN} "  停止服务: sudo systemctl stop ai-ken" 
print_message ${GREEN} "  重启服务: sudo systemctl restart ai-ken"
print_message ${GREEN} "  查看状态: sudo systemctl status ai-ken"
print_message ${GREEN} "  查看日志: sudo journalctl -u ai-ken -f"
print_message ${GREEN} ""
print_message ${YELLOW} "注意: 如果代理设置不正确，可能需要修改服务文件中的代理配置"