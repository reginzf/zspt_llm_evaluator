#!/bin/bash
set -e

# Color definitions
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
    echo -e "${BLUE}Checking environment...${NC}"
    
    # Check if Python3 is available
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Python3 not installed${NC}"
        install_python
    fi
    
    # Function to get Python version
    get_python_version() {
        python3 --version 2>/dev/null | grep -oP 'Python \K[0-9]+\.[0-9]+' || python --version 2>/dev/null | grep -oP 'Python \K[0-9]+\.[0-9]+'
    }
    
    python_version=$(get_python_version)
    if [[ -z "$python_version" ]]; then
        echo -e "${RED}Cannot get Python version${NC}"
        exit 1
    fi
    
    # Extract major and minor version numbers
    major=$(echo "$python_version" | cut -d. -f1)
    minor=$(echo "$python_version" | cut -d. -f2)
    
    if [[ $major -lt 3 ]] || [[ $major -eq 3 && $minor -lt 10 ]]; then
        echo -e "${YELLOW}Current Python version $python_version does not meet requirement (3.10+)${NC}"
        echo -e "${YELLOW}Attempting to install Python 3.10...${NC}"
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
    
    # Check project files in the current working directory
    if [ ! -f "requirements_centos.txt" ]; then
        echo -e "${RED}requirements_centos.txt not found in current directory $(pwd)${NC}"
        exit 1
    fi
    
    if [ ! -d "src/sql_funs/creaters" ]; then
        echo -e "${YELLOW}Warning: No database scripts directory${NC}"
    fi
}

collect_input() {
    PROJECT_ROOT=$(pwd)
    echo -e "${GREEN}Project directory: $PROJECT_ROOT${NC}"
    
    # Database configuration
    read -p "Database host [localhost]: " SQL_HOST; SQL_HOST=${SQL_HOST:-localhost}
    read -p "Database port [5432]: " SQL_PORT; SQL_PORT=${SQL_PORT:-5432}
    read -p "Database name [label_studio]: " SQL_DB; SQL_DB=${SQL_DB:-label_studio}
    read -p "Username [labelstudio]: " SQL_USER; SQL_USER=${SQL_USER:-labelstudio}
    read -sp "Password: " SQL_PASSWORD; echo
    
    # Path configuration
    read -p "Knowledge directory [$PROJECT_ROOT/data/knowledge]: " KNOWLEDGE_LOCAL_PATH
    KNOWLEDGE_LOCAL_PATH=${KNOWLEDGE_LOCAL_PATH:-$PROJECT_ROOT/data/knowledge}
    
    read -p "Model directory [$PROJECT_ROOT/models]: " MODEL_PATH
    MODEL_PATH=${MODEL_PATH:-$PROJECT_ROOT/models}
    
    # Model parameters
    read -p "Overlap threshold [0.8]: " OVERLAP_THRESHOLD; OVERLAP_THRESHOLD=${OVERLAP_THRESHOLD:-0.8}
    read -p "Similarity threshold [0.7]: " SIMILARITY_THRESHOLD; SIMILARITY_THRESHOLD=${SIMILARITY_THRESHOLD:-0.7}
    read -p "Semantic weight [0.9]: " SEMANTIC_WEIGHT; SEMANTIC_WEIGHT=${SEMANTIC_WEIGHT:-0.9}
    read -p "TOP_K [1,3,5,10]: " TOP_K_INPUT; TOP_K_INPUT=${TOP_K_INPUT:-1,3,5,10}
    TOP_K="[$TOP_K_INPUT]"
    
    # API configuration
    read -p "DeepSeek API key: " DEEPSEEK_API_KEY
    read -p "API base [https://api.deepseek.com]: " DEEPSEEK_API_BASE
    DEEPSEEK_API_BASE=${DEEPSEEK_API_BASE:-https://api.deepseek.com}
    read -p "Model name [deepseek-chat]: " MODEL_NAME
    MODEL_NAME=${MODEL_NAME:-deepseek-chat}
    
    # Confirm configuration
    echo -e "${BLUE}Confirm configuration? [Y/n]: ${NC}"
    read confirm
    [[ "$confirm" =~ ^[Yy]?$ ]] || exit
    
    # Export as global variables
    export PROJECT_ROOT SQL_HOST SQL_PORT SQL_DB SQL_USER SQL_PASSWORD KNOWLEDGE_LOCAL_PATH MODEL_PATH OVERLAP_THRESHOLD SIMILARITY_THRESHOLD SEMANTIC_WEIGHT TOP_K DEEPSEEK_API_KEY DEEPSEEK_API_BASE MODEL_NAME
}

setup_venv() {
    echo -e "${BLUE}Setting up virtual environment...${NC}"
    
    if [ -d "venv" ]; then
        echo -e "${YELLOW}Virtual environment already exists, recreate? [y/N]: ${NC}"
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
    echo -e "${GREEN} Virtual environment ready${NC}"
}

install_deps() {
    echo -e "${BLUE}Installing dependencies...${NC}"
    
    # Detect operating system type
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # On Linux, detect if it's CentOS
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            if [[ "$NAME" == *"CentOS"* ]]; then
                echo -e "${BLUE}Detected CentOS system, using CentOS-optimized requirements${NC}"
                pip install --upgrade pip
                pip install -r requirements_centos.txt
            else
                # Non-CentOS Linux system, use general requirements.txt
                echo -e "${BLUE}Detected non-CentOS Linux system, using general requirements${NC}"
                pip install --upgrade pip
                pip install -r requirements.txt
            fi
        else
            # Cannot determine Linux distribution, use general requirements.txt
            echo -e "${BLUE}Cannot determine Linux distribution, using general requirements${NC}"
            pip install --upgrade pip
            pip install -r requirements.txt
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS system, use general requirements.txt
        echo -e "${BLUE}Detected macOS system, using general requirements${NC}"
        pip install --upgrade pip
        pip install -r requirements.txt
    else
        # Other systems (like WSL), use general requirements.txt
        echo -e "${BLUE}Detected other system type, using general requirements${NC}"
        pip install --upgrade pip
        pip install -r requirements.txt
    fi
    
    echo -e "${GREEN} Dependencies installed${NC}"
}

create_config() {
    echo -e "${BLUE}Creating configuration...${NC}"
    
    # Create directories
    mkdir -p configs "$KNOWLEDGE_LOCAL_PATH" "$MODEL_PATH" logs data
    
    # Generate settings.toml
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
    echo -e "${GREEN} Configuration file created${NC}"
}

init_db() {
    echo -e "${BLUE}Initializing database...${NC}"
    
    SQL_DIR="src/sql_funs/creaters"
    if [ -d "$SQL_DIR" ]; then
        for script in "$SQL_DIR"/create*.py; do
            [ -f "$script" ] && python "$script" && echo -e "${GREEN} Running $(basename "$script")${NC}"
        done
    else
        echo -e "${YELLOW}Skipping database initialization${NC}"
    fi
}

main() {
    echo -e "${GREEN}=== AI Project Initialization Script ===${NC}"
    
    check_environment
    collect_input
    setup_venv
    install_deps
    create_config
    init_db
    
    echo -e "${BLUE}================================${NC}"
    echo -e "${GREEN} Initialization completed!${NC}"
    echo -e "${YELLOW}Next steps:${NC}"
    echo -e "1. Download models to: $MODEL_PATH"
    echo -e "2. Activate environment: source venv/bin/activate"
    echo -e "3. Start app: python app.py --host 0.0.0.0 --port 5001 --debug"
    echo -e "${BLUE}================================${NC}"
}

main "$@"
