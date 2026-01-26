#!/bin/bash
set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to install Python 3.10 on different systems
install_python() {
    echo -e "${YELLOW}Installing Python 3.10...${NC}"
    
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        case $NAME in
            *"Ubuntu"*|*"Debian"*)
                echo -e "${BLUE}Detected Ubuntu/Debian system${NC}"
                sudo apt update
                sudo apt install -y software-properties-common
                sudo add-apt-repository -y ppa:deadsnakes/ppa
                sudo apt update
                sudo apt install -y python3.10 python3.10-venv python3.10-dev
                ;;
            *"CentOS"*|*"Red Hat"*|*"Fedora"*)
                echo -e "${BLUE}Detected Red Hat/CentOS/Fedora system${NC}"
                if command -v dnf &> /dev/null; then
                    sudo dnf install -y gcc openssl-devel bzip2-devel libffi-devel zlib-devel wget
                else
                    sudo yum install -y gcc openssl-devel bzip2-devel libffi-devel zlib-devel wget
                fi
                
                # Download and compile Python 3.10
                cd /tmp
                wget https://www.python.org/ftp/python/3.10.15/Python-3.10.15.tgz
                tar xzf Python-3.10.15.tgz
                cd Python-3.10.15
                ./configure --enable-optimizations --prefix=/usr/local
                make -j$(nproc)
                sudo make altinstall  # Use altinstall to avoid replacing system python
                ;;
            *)
                echo -e "${RED}Unsupported Linux distribution. Please install Python 3.10 manually.${NC}"
                exit 1
                ;;
        esac
    else
        echo -e "${RED}Could not determine Linux distribution. Please install Python 3.10 manually.${NC}"
        exit 1
    fi
}

check_environment() {
    echo -e "${BLUE}检查环境...${NC}"
    
    # Check if Python3 is available
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Python3未安装${NC}"
        install_python
    fi
    
    # Function to get Python version
    get_python_version() {
        python3 --version 2>/dev/null | grep -oP 'Python \K[0-9]+\.[0-9]+' || python --version 2>/dev/null | grep -oP 'Python \K[0-9]+\.[0-9]+'
    }
    
    python_version=$(get_python_version)
    if [[ -z "$python_version" ]]; then
        echo -e "${RED}无法获取Python版本${NC}"
        exit 1
    fi
    
    # Extract major and minor version numbers
    major=$(echo "$python_version" | cut -d. -f1)
    minor=$(echo "$python_version" | cut -d. -f2)
    
    if [[ $major -lt 3 ]] || [[ $major -eq 3 && $minor -lt 10 ]]; then
        echo -e "${YELLOW}当前Python版本 $python_version 不满足要求 (3.10+)${NC}"
        echo -e "${YELLOW}尝试安装Python 3.10...${NC}"
        install_python
        
        # Check if python3.10 is now available
        if command -v python3.10 &> /dev/null; then
            echo -e "${GREEN}Using Python 3.10${NC}"
            python_version=$(python3.10 --version | grep -oP 'Python \K[0-9]+\.[0-9]+')
        else
            # Check if the default python3 has been updated
            updated_version=$(get_python_version)
            updated_major=$(echo "$updated_version" | cut -d. -f1)
            updated_minor=$(echo "$updated_version" | cut -d. -f2)
            
            if [[ $updated_major -lt 3 ]] || [[ $updated_major -eq 3 && $updated_minor -lt 10 ]]; then
                echo -e "${RED}Installed Python still does not meet requirements. Current: $updated_version${NC}"
                exit 1
            fi
            python_version=$updated_version
        fi
    fi
    
    echo -e "${GREEN} Python $python_version${NC}"
    
    # 检查项目文件
    # 在Linux/CentOS上，使用requirements_centos.txt
    [ -f "requirements_centos.txt" ] || { echo -e "${RED}未找到requirements_centos.txt${NC}"; exit 1; }
    [ -d "src/sql_funs/creaters" ] || { echo -e "${YELLOW}警告: 无数据库脚本目录${NC}"; }
}

collect_input() {
    PROJECT_ROOT=$(pwd)
    echo -e "${GREEN}项目目录: $PROJECT_ROOT${NC}"
    
    # 数据库配置
    read -p "数据库主机 [localhost]: " SQL_HOST; SQL_HOST=${SQL_HOST:-localhost}
    read -p "数据库端口 [5432]: " SQL_PORT; SQL_PORT=${SQL_PORT:-5432}
    read -p "数据库名 [label_studio]: " SQL_DB; SQL_DB=${SQL_DB:-label_studio}
    read -p "用户名 [labelstudio]: " SQL_USER; SQL_USER=${SQL_USER:-labelstudio}
    read -sp "密码: " SQL_PASSWORD; echo
    
    # 路径配置
    read -p "知识目录 [$PROJECT_ROOT/data/knowledge]: " KNOWLEDGE_LOCAL_PATH
    KNOWLEDGE_LOCAL_PATH=${KNOWLEDGE_LOCAL_PATH:-$PROJECT_ROOT/data/knowledge}
    
    read -p "模型目录 [$PROJECT_ROOT/models]: " MODEL_PATH
    MODEL_PATH=${MODEL_PATH:-$PROJECT_ROOT/models}
    
    # 模型参数
    read -p "重叠阈值 [0.8]: " OVERLAP_THRESHOLD; OVERLAP_THRESHOLD=${OVERLAP_THRESHOLD:-0.8}
    read -p "相似度阈值 [0.7]: " SIMILARITY_THRESHOLD; SIMILARITY_THRESHOLD=${SIMILARITY_THRESHOLD:-0.7}
    read -p "语义权重 [0.9]: " SEMANTIC_WEIGHT; SEMANTIC_WEIGHT=${SEMANTIC_WEIGHT:-0.9}
    read -p "TOP_K [1,3,5,10]: " TOP_K_INPUT; TOP_K_INPUT=${TOP_K_INPUT:-1,3,5,10}
    TOP_K="[$TOP_K_INPUT]"
    
    # API配置
    read -p "DeepSeek API密钥: " DEEPSEEK_API_KEY
    read -p "API地址 [https://api.deepseek.com]: " DEEPSEEK_API_BASE
    DEEPSEEK_API_BASE=${DEEPSEEK_API_BASE:-https://api.deepseek.com}
    read -p "模型名 [deepseek-chat]: " MODEL_NAME
    MODEL_NAME=${MODEL_NAME:-deepseek-chat}
    
    # 确认配置
    echo -e "${BLUE}确认配置? [Y/n]: ${NC}"
    read confirm
    [[ "$confirm" =~ ^[Yy]?$ ]] || exit
    
    # 导出为全局变量
    export PROJECT_ROOT SQL_HOST SQL_PORT SQL_DB SQL_USER SQL_PASSWORD KNOWLEDGE_LOCAL_PATH MODEL_PATH OVERLAP_THRESHOLD SIMILARITY_THRESHOLD SEMANTIC_WEIGHT TOP_K DEEPSEEK_API_KEY DEEPSEEK_API_BASE MODEL_NAME
}

setup_venv() {
    echo -e "${BLUE}设置虚拟环境...${NC}"
    
    if [ -d "venv" ]; then
        echo -e "${YELLOW}虚拟环境已存在，重新创建? [y/N]: ${NC}"
        read recreate
        [[ "$recreate" =~ ^[Yy]$ ]] && rm -rf venv
    fi
    
    # Use python3.10 if available, otherwise use python3
    if command -v python3.10 &> /dev/null; then
        python3.10 -m venv venv
    else
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    echo -e "${GREEN} 虚拟环境就绪${NC}"
}

install_deps() {
    echo -e "${BLUE}安装依赖...${NC}"
    
    # 检测操作系统类型
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # 在Linux上检测是否为CentOS
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            if [[ "$NAME" == *"CentOS"* ]]; then
                echo -e "${BLUE}检测到CentOS系统，使用CentOS优化的依赖文件${NC}"
                pip install --upgrade pip
                pip install -r requirements_centos.txt
            else
                # 非CentOS Linux系统，使用通用requirements.txt
                echo -e "${BLUE}检测到非CentOS Linux系统，使用通用依赖文件${NC}"
                pip install --upgrade pip
                pip install -r requirements.txt
            fi
        else
            # 无法确定Linux发行版，使用通用requirements.txt
            echo -e "${BLUE}无法确定Linux发行版，使用通用依赖文件${NC}"
            pip install --upgrade pip
            pip install -r requirements.txt
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS系统，使用通用requirements.txt
        echo -e "${BLUE}检测到macOS系统，使用通用依赖文件${NC}"
        pip install --upgrade pip
        pip install -r requirements.txt
    else
        # 其他系统（如WSL），使用通用requirements.txt
        echo -e "${BLUE}检测到其他系统类型，使用通用依赖文件${NC}"
        pip install --upgrade pip
        pip install -r requirements.txt
    fi
    
    echo -e "${GREEN} 依赖安装完成${NC}"
}

create_config() {
    echo -e "${BLUE}创建配置...${NC}"
    
    # 创建目录
    mkdir -p configs "$KNOWLEDGE_LOCAL_PATH" "$MODEL_PATH" logs data
    
    # 生成settings.toml
    cat > configs/settings.toml << EOF
[default]
PROJECT_ROOT = '$PROJECT_ROOT'
SQL_HOST = '$SQL_HOST'
SQL_PORT = $SQL_PORT
SQL_DB = '$SQL_DB'
SQL_USER = '$SQL_USER'
SQL_PASSWORD = '$SQL_PASSWORD'
KNOWLEDGE_LOCAL_PATH = '$KNOWLEDGE_LOCAL_PATH'
OVERLAP_THRESHOLD = $OVERLAP_THRESHOLD
SIMILARITY_THRESHOLD = $SIMILARITY_THRESHOLD
SEMANTIC_WEIGHT = $SEMANTIC_WEIGHT
MODEL_PATH = '$MODEL_PATH'
TOP_K = $TOP_K
DEEPSEEK_API_KEY = "$DEEPSEEK_API_KEY"
DEEPSEEK_API_BASE = "$DEEPSEEK_API_BASE"
MODEL_NAME = "$MODEL_NAME"
EOF
    echo -e "${GREEN} 配置文件创建完成${NC}"
}

init_db() {
    echo -e "${BLUE}初始化数据库...${NC}"
    
    SQL_DIR="src/sql_funs/creaters"
    if [ -d "$SQL_DIR" ]; then
        for script in "$SQL_DIR"/create*.py; do
            [ -f "$script" ] && python "$script" && echo -e "${GREEN} 运行 $(basename "$script")${NC}"
        done
    else
        echo -e "${YELLOW}跳过数据库初始化${NC}"
    fi
}

main() {
    echo -e "${GREEN}=== AI项目初始化脚本 ===${NC}"
    
    check_environment
    collect_input
    setup_venv
    install_deps
    create_config
    init_db
    
    echo -e "${BLUE}================================${NC}"
    echo -e "${GREEN} 初始化完成！${NC}"
    echo -e "${YELLOW}下一步:${NC}"
    echo -e "1. 下载模型到: $MODEL_PATH"
    echo -e "2. 激活环境: source venv/bin/activate"
    echo -e "3. 启动应用: python app.py --host 0.0.0.0 --port 5001 --debug"
    echo -e "${BLUE}================================${NC}"
}

main "$@"
