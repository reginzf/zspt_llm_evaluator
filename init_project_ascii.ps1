# PowerShell Project Initialization Script
# Supports Windows environment for Python knowledge slicing annotation project

# Set error handling
$ErrorActionPreference = "Stop"

# Color definition function
function Write-Custom {
    param([string]$Message, [string]$Color = "White")
    $foregroundColor = [System.ConsoleColor]::$Color
    Write-Host $Message -ForegroundColor $foregroundColor
}

function Check-Environment {
    Write-Custom "Checking environment..." "Blue"
    
    # Check Python version
    try {
        $pythonVersion = python --version 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "Python not installed or unavailable"
        }
        
        $versionMatch = [regex]::Match($pythonVersion, 'Python (\d+)\.(\d+)')
        if ($versionMatch.Success) {
            $major = [int]$versionMatch.Groups[1].Value
            $minor = [int]$versionMatch.Groups[2].Value
            
            if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 10)) {
                Write-Custom "Requires Python 3.10+, current: $pythonVersion" "Red"
                exit 1
            }
            Write-Custom "Python $major.$minor found" "Green"
        } else {
            Write-Custom "Cannot parse Python version" "Red"
            exit 1
        }
    } catch {
        Write-Custom "Python not installed or unavailable" "Red"
        exit 1
    }
    
    # Check project files
    if (-not (Test-Path "requirements_centos.txt")) {
        Write-Custom "requirements_centos.txt not found" "Red"
        exit 1
    }
    
    if (-not (Test-Path "src\sql_funs\creaters")) {
        Write-Custom "Warning: No database scripts directory" "Yellow"
    }
}

function Collect-Input {
    $PROJECT_ROOT = Get-Location
    Write-Custom "Project directory: $PROJECT_ROOT" "Green"
    
    # Database configuration
    $SQL_HOST = Read-Host "Database host [localhost]" 
    $SQL_HOST = if ([string]::IsNullOrWhiteSpace($SQL_HOST)) { "localhost" } else { $SQL_HOST }
    
    $SQL_PORT = Read-Host "Database port [5432]"
    $SQL_PORT = if ([string]::IsNullOrWhiteSpace($SQL_PORT)) { "5432" } else { $SQL_PORT }
    
    $SQL_DB = Read-Host "Database name [label_studio]"
    $SQL_DB = if ([string]::IsNullOrWhiteSpace($SQL_DB)) { "label_studio" } else { $SQL_DB }
    
    $SQL_USER = Read-Host "Username [labelstudio]"
    $SQL_USER = if ([string]::IsNullOrWhiteSpace($SQL_USER)) { "labelstudio" } else { $SQL_USER }
    
    $SQL_PASSWORD = Read-Host "Password" -AsSecureString
    $SQL_PASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($SQL_PASSWORD))
    
    # Path configuration
    $KNOWLEDGE_LOCAL_PATH = Read-Host "Knowledge directory [$PROJECT_ROOT\data\knowledge]"
    $KNOWLEDGE_LOCAL_PATH = if ([string]::IsNullOrWhiteSpace($KNOWLEDGE_LOCAL_PATH)) { "$PROJECT_ROOT\data\knowledge" } else { $KNOWLEDGE_LOCAL_PATH }
    
    $MODEL_PATH = Read-Host "Model directory [$PROJECT_ROOT\models]"
    $MODEL_PATH = if ([string]::IsNullOrWhiteSpace($MODEL_PATH)) { "$PROJECT_ROOT\models" } else { $MODEL_PATH }
    
    # Model parameters
    $OVERLAP_THRESHOLD = Read-Host "Overlap threshold [0.8]"
    $OVERLAP_THRESHOLD = if ([string]::IsNullOrWhiteSpace($OVERLAP_THRESHOLD)) { "0.8" } else { $OVERLAP_THRESHOLD }
    
    $SIMILARITY_THRESHOLD = Read-Host "Similarity threshold [0.7]"
    $SIMILARITY_THRESHOLD = if ([string]::IsNullOrWhiteSpace($SIMILARITY_THRESHOLD)) { "0.7" } else { $SIMILARITY_THRESHOLD }
    
    $SEMANTIC_WEIGHT = Read-Host "Semantic weight [0.9]"
    $SEMANTIC_WEIGHT = if ([string]::IsNullOrWhiteSpace($SEMANTIC_WEIGHT)) { "0.9" } else { $SEMANTIC_WEIGHT }
    
    $TOP_K_INPUT = Read-Host "TOP_K [1,3,5,10]"
    $TOP_K_INPUT = if ([string]::IsNullOrWhiteSpace($TOP_K_INPUT)) { "1,3,5,10" } else { $TOP_K_INPUT }
    $TOP_K = "[$TOP_K_INPUT]"
    
    # API configuration
    $DEEPSEEK_API_KEY = Read-Host "DeepSeek API key"
    $DEEPSEEK_API_BASE = Read-Host "API base [https://api.deepseek.com]"
    $DEEPSEEK_API_BASE = if ([string]::IsNullOrWhiteSpace($DEEPSEEK_API_BASE)) { "https://api.deepseek.com" } else { $DEEPSEEK_API_BASE }
    
    $MODEL_NAME = Read-Host "Model name [deepseek-chat]"
    $MODEL_NAME = if ([string]::IsNullOrWhiteSpace($MODEL_NAME)) { "deepseek-chat" } else { $MODEL_NAME }
    
    # Confirm configuration
    $confirm = Read-Host "Confirm configuration? [Y/n]"
    if ($confirm -inotmatch "^y$|^$") {
        Write-Custom "User cancelled operation" "Red"
        exit
    }
    
    # Store collected data as global variables
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
    Write-Custom "Setting up virtual environment..." "Blue"
    
    if (Test-Path "venv") {
        $recreate = Read-Host "Virtual environment already exists, recreate? [y/N]"
        if ($recreate -imatch "^y$") {
            Remove-Item -Recurse -Force venv
        }
    }
    
    if (-not (Test-Path "venv")) {
        python -m venv venv
    }
    
    # Activate virtual environment
    $env:PYTHONPATH = "$PWD"
    & "$PWD\venv\Scripts\Activate.ps1"
    Write-Custom " Virtual environment ready" "Green"
}

function Install-Deps {
    Write-Custom "Installing dependencies..." "Blue"
    
    # Activate virtual environment
    & "$PWD\venv\Scripts\Activate.ps1"
    
    # Upgrade pip
    python -m pip install --upgrade pip
    
    # Install dependencies
    python -m pip install -r requirements_centos.txt
    
    Write-Custom " Dependencies installed" "Green"
}

function Create-Config {
    Write-Custom "Creating configuration..." "Blue"
    
    # Create directories
    New-Item -ItemType Directory -Path "configs" -Force | Out-Null
    New-Item -ItemType Directory -Path $Global:Config.KNOWLEDGE_LOCAL_PATH -Force | Out-Null
    New-Item -ItemType Directory -Path $Global:Config.MODEL_PATH -Force | Out-Null
    New-Item -ItemType Directory -Path "logs" -Force | Out-Null
    New-Item -ItemType Directory -Path "data" -Force | Out-Null
    
    # Generate settings.toml
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
    
    # Save configuration file with explicit UTF8 encoding
    [System.IO.File]::WriteAllText("configs\settings.toml", $configContent, [System.Text.Encoding]::UTF8)
    Write-Custom " Configuration file created" "Green"
}

function Init-DB {
    Write-Custom "Initializing database..." "Blue"
    
    $SQL_DIR = "src\sql_funs\creaters"
    if (Test-Path $SQL_DIR) {
        Get-ChildItem "$SQL_DIR\create*.py" | ForEach-Object {
            Write-Custom " Running $($_.Name)" "Green"
            python $_.FullName
        }
    } else {
        Write-Custom "Skipping database initialization" "Yellow"
    }
}

function Main {
    Write-Custom "=== AI Project Initialization Script ===" "Green"
    
    Check-Environment
    Collect-Input
    Setup-Venv
    Install-Deps
    Create-Config
    Init-DB
    
    Write-Custom "================================" "Blue"
    Write-Custom " Initialization completed!" "Green"
    Write-Custom "Next steps:" "Yellow"
    Write-Custom "1. Download models to: $($Global:Config.MODEL_PATH)"
    Write-Custom "2. Activate environment: .\venv\Scripts\Activate.ps1"
    Write-Custom "3. Start app: python app.py --host 0.0.0.0 --port 5001 --debug"
    Write-Custom "================================" "Blue"
}

# Execute main function
Main