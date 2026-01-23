# PowerShell项目初始化脚本
# 支持Windows环境的Python知识切片标注项目环境部署

# 设置错误处理
$ErrorActionPreference = "Stop"

# 颜色定义函数
function Write-Custom {
    param([string]$Message, [string]$Color = "White")
    $foregroundColor = [System.ConsoleColor]::$Color
    Write-Host $Message -ForegroundColor $foregroundColor
}

function Check-Environment {
    Write-Custom "检查环境..." "Blue"
    
    # 检查Python版本
    try {
        $pythonVersion = python --version 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "Python未安装或不可用"
        }
        
        $versionMatch = [regex]::Match($pythonVersion, 'Python (\d+)\.(\d+)')
        if ($versionMatch.Success) {
            $major = [int]$versionMatch.Groups[1].Value
            $minor = [int]$versionMatch.Groups[2].Value
            
            if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 8)) {
                Write-Custom "需要Python 3.8+，当前: $pythonVersion" "Red"
                exit 1
            }
            Write-Custom "Python $major.$minor 已找到" "Green"
        } else {
            Write-Custom "无法解析Python版本" "Red"
            exit 1
        }
    } catch {
        Write-Custom "Python未安装或不可用" "Red"
        exit 1
    }
    
    # 检查项目文件
    if (-not (Test-Path "requirements.txt")) {
        Write-Custom "未找到requirements.txt" "Red"
        exit 1
    }
    
    if (-not (Test-Path "src\sql_funs\creaters")) {
        Write-Custom "警告: 无数据库脚本目录" "Yellow"
    }
}

function Collect-Input {
    $PROJECT_ROOT = Get-Location
    Write-Custom "项目目录: $PROJECT_ROOT" "Green"
    
    # 数据库配置
    $SQL_HOST = Read-Host "数据库主机 [localhost]" 
    $SQL_HOST = if ([string]::IsNullOrWhiteSpace($SQL_HOST)) { "localhost" } else { $SQL_HOST }
    
    $SQL_PORT = Read-Host "数据库端口 [5432]"
    $SQL_PORT = if ([string]::IsNullOrWhiteSpace($SQL_PORT)) { "5432" } else { $SQL_PORT }
    
    $SQL_DB = Read-Host "数据库名 [label_studio]"
    $SQL_DB = if ([string]::IsNullOrWhiteSpace($SQL_DB)) { "label_studio" } else { $SQL_DB }
    
    $SQL_USER = Read-Host "用户名 [labelstudio]"
    $SQL_USER = if ([string]::IsNullOrWhiteSpace($SQL_USER)) { "labelstudio" } else { $SQL_USER }
    
    $SQL_PASSWORD = Read-Host "密码" -AsSecureString
    $SQL_PASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($SQL_PASSWORD))
    
    # 路径配置
    $KNOWLEDGE_LOCAL_PATH = Read-Host "知识目录 [$PROJECT_ROOT\data\knowledge]"
    $KNOWLEDGE_LOCAL_PATH = if ([string]::IsNullOrWhiteSpace($KNOWLEDGE_LOCAL_PATH)) { "$PROJECT_ROOT\data\knowledge" } else { $KNOWLEDGE_LOCAL_PATH }
    
    $MODEL_PATH = Read-Host "模型目录 [$PROJECT_ROOT\models]"
    $MODEL_PATH = if ([string]::IsNullOrWhiteSpace($MODEL_PATH)) { "$PROJECT_ROOT\models" } else { $MODEL_PATH }
    
    # 模型参数
    $OVERLAP_THRESHOLD = Read-Host "重叠阈值 [0.8]"
    $OVERLAP_THRESHOLD = if ([string]::IsNullOrWhiteSpace($OVERLAP_THRESHOLD)) { "0.8" } else { $OVERLAP_THRESHOLD }
    
    $SIMILARITY_THRESHOLD = Read-Host "相似度阈值 [0.7]"
    $SIMILARITY_THRESHOLD = if ([string]::IsNullOrWhiteSpace($SIMILARITY_THRESHOLD)) { "0.7" } else { $SIMILARITY_THRESHOLD }
    
    $SEMANTIC_WEIGHT = Read-Host "语义权重 [0.9]"
    $SEMANTIC_WEIGHT = if ([string]::IsNullOrWhiteSpace($SEMANTIC_WEIGHT)) { "0.9" } else { $SEMANTIC_WEIGHT }
    
    $TOP_K_INPUT = Read-Host "TOP_K [1,3,5,10]"
    $TOP_K_INPUT = if ([string]::IsNullOrWhiteSpace($TOP_K_INPUT)) { "1,3,5,10" } else { $TOP_K_INPUT }
    $TOP_K = "[$TOP_K_INPUT]"
    
    # API配置
    $DEEPSEEK_API_KEY = Read-Host "DeepSeek API密钥"
    $DEEPSEEK_API_BASE = Read-Host "API地址 [https://api.deepseek.com]"
    $DEEPSEEK_API_BASE = if ([string]::IsNullOrWhiteSpace($DEEPSEEK_API_BASE)) { "https://api.deepseek.com" } else { $DEEPSEEK_API_BASE }
    
    $MODEL_NAME = Read-Host "模型名 [deepseek-chat]"
    $MODEL_NAME = if ([string]::IsNullOrWhiteSpace($MODEL_NAME)) { "deepseek-chat" } else { $MODEL_NAME }
    
    # 确认配置
    $confirm = Read-Host "确认配置? [Y/n]"
    if ($confirm -inotmatch "^y$|^$") {
        Write-Custom "用户取消操作" "Red"
        exit
    }
    
    # 将收集的数据存储为全局变量
    $Global:Config = @{
        PROJECT_ROOT = $PROJECT_ROOT
        SQL_HOST = $SQL_HOST
        SQL_PORT = $SQL_PORT
        SQL_DB = $SQL_DB
        SQL_USER = $SQL_USER
        SQL_PASSWORD = $SQL_PASSWORD
        KNOWLEDGE_LOCAL_PATH = $KNOWLEDGE_LOCAL_PATH
        MODEL_PATH = $MODEL_PATH
        OVERLAP_THRESHOLD = $OVERLAP_THRESHOLD
        SIMILARITY_THRESHOLD = $SIMILARITY_THRESHOLD
        SEMANTIC_WEIGHT = $SEMANTIC_WEIGHT
        TOP_K = $TOP_K
        DEEPSEEK_API_KEY = $DEEPSEEK_API_KEY
        DEEPSEEK_API_BASE = $DEEPSEEK_API_BASE
        MODEL_NAME = $MODEL_NAME
    }
}

function Setup-Venv {
    Write-Custom "设置虚拟环境..." "Blue"
    
    if (Test-Path "venv") {
        $recreate = Read-Host "虚拟环境已存在，重新创建? [y/N]"
        if ($recreate -imatch "^y$") {
            Remove-Item -Recurse -Force venv
        }
    }
    
    if (-not (Test-Path "venv")) {
        python -m venv venv
    }
    
    # 激活虚拟环境
    $env:PYTHONPATH = "$PWD"
    & "$PWD\venv\Scripts\Activate.ps1"
    Write-Custom " 虚拟环境就绪" "Green"
}

function Install-Deps {
    Write-Custom "安装依赖..." "Blue"
    
    # 激活虚拟环境
    & "$PWD\venv\Scripts\Activate.ps1"
    
    # 升级pip
    python -m pip install --upgrade pip
    
    # 安装依赖
    python -m pip install -r requirements_centos.txt
    
    Write-Custom " 依赖安装完成" "Green"
}

function Create-Config {
    Write-Custom "创建配置..." "Blue"
    
    # 创建目录
    New-Item -ItemType Directory -Path "configs" -Force | Out-Null
    New-Item -ItemType Directory -Path $Global:Config.KNOWLEDGE_LOCAL_PATH -Force | Out-Null
    New-Item -ItemType Directory -Path $Global:Config.MODEL_PATH -Force | Out-Null
    New-Item -ItemType Directory -Path "logs" -Force | Out-Null
    New-Item -ItemType Directory -Path "data" -Force | Out-Null
    
    # 生成settings.toml
    $configContent = @"
[default]
PROJECT_ROOT = '$($Global:Config.PROJECT_ROOT)'
SQL_HOST = '$($Global:Config.SQL_HOST)'
SQL_PORT = $($Global:Config.SQL_PORT)
SQL_DB = '$($Global:Config.SQL_DB)'
SQL_USER = '$($Global:Config.SQL_USER)'
SQL_PASSWORD = '$($Global:Config.SQL_PASSWORD)'
KNOWLEDGE_LOCAL_PATH = '$($Global:Config.KNOWLEDGE_LOCAL_PATH)'
OVERLAP_THRESHOLD = $($Global:Config.OVERLAP_THRESHOLD)
SIMILARITY_THRESHOLD = $($Global:Config.SIMILARITY_THRESHOLD)
SEMANTIC_WEIGHT = $($Global:Config.SEMANTIC_WEIGHT)
MODEL_PATH = '$($Global:Config.MODEL_PATH)'
TOP_K = $TOP_K
DEEPSEEK_API_KEY = "$($Global:Config.DEEPSEEK_API_KEY)"
DEEPSEEK_API_BASE = "$($Global:Config.DEEPSEEK_API_BASE)"
MODEL_NAME = "$($Global:Config.MODEL_NAME)"
"@
    
    $configContent | Out-File -FilePath "configs\settings.toml" -Encoding UTF8
    Write-Custom " 配置文件创建完成" "Green"
}

function Init-DB {
    Write-Custom "初始化数据库..." "Blue"
    
    $SQL_DIR = "src\sql_funs\creaters"
    if (Test-Path $SQL_DIR) {
        Get-ChildItem "$SQL_DIR\create*.py" | ForEach-Object {
            Write-Custom " 运行 $($_.Name)" "Green"
            python $_.FullName
        }
    } else {
        Write-Custom "跳过数据库初始化" "Yellow"
    }
}

function Main {
    Write-Custom "=== AI项目初始化脚本 ===" "Green"
    
    Check-Environment
    Collect-Input
    Setup-Venv
    Install-Deps
    Create-Config
    Init-DB
    
    Write-Custom "================================" "Blue"
    Write-Custom " 初始化完成！" "Green"
    Write-Custom "下一步:" "Yellow"
    Write-Custom "1. 下载模型到: $($Global:Config.MODEL_PATH)"
    Write-Custom "2. 激活环境: .\venv\Scripts\Activate.ps1"
    Write-Custom "3. 启动应用: python app.py --host 0.0.0.0 --port 5001 --debug"
    Write-Custom "================================" "Blue"
}

# 执行主函数
Main