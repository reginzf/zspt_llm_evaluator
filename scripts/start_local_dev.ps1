# AI-KEN 本地开发环境启动脚本 (PowerShell)
# 使用: .\scripts\start_local_dev.ps1

$ErrorActionPreference = "Stop"

Write-Host "====================================" -ForegroundColor Green
Write-Host "  AI-KEN 本地开发环境启动" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green
Write-Host ""

# 项目根目录
$PROJECT_ROOT = Split-Path -Parent $PSScriptRoot
Set-Location $PROJECT_ROOT

# 检查 Python
Write-Host "[1/5] 检查 Python 环境..." -ForegroundColor Green
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✓ $pythonVersion"
} catch {
    Write-Host "  ✗ Python 未安装或未添加到 PATH" -ForegroundColor Red
    exit 1
}

# 检查虚拟环境
Write-Host "[2/5] 检查虚拟环境..." -ForegroundColor Green
if (-not (Test-Path ".venv")) {
    Write-Host "  创建虚拟环境..." -ForegroundColor Yellow
    python -m venv .venv
}
Write-Host "  ✓ 虚拟环境已就绪"

# 激活虚拟环境
Write-Host "[3/5] 激活虚拟环境并安装依赖..." -ForegroundColor Green
& .venv\Scripts\Activate.ps1

# 安装依赖
$requiredPackages = @("flask", "flask-cors", "psycopg2-binary")
foreach ($pkg in $requiredPackages) {
    pip show $pkg 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  安装 $pkg..." -ForegroundColor Yellow
        pip install -q $pkg
    }
}
Write-Host "  ✓ 依赖已安装"

# 设置环境变量
Write-Host "[4/5] 配置环境变量..." -ForegroundColor Green
$env:CORS_ALLOW_ALL = "true"
$env:FLASK_HOST = "127.0.0.1"
$env:FLASK_PORT = "5001"
$env:VUE_FRONTEND_MODE = "disable"  # 禁用 Vue 模板回退，纯 API 模式

Write-Host "  CORS_ALLOW_ALL: $env:CORS_ALLOW_ALL"
Write-Host "  FLASK_HOST: $env:FLASK_HOST"
Write-Host "  FLASK_PORT: $env:FLASK_PORT"

# 启动后端
Write-Host "[5/5] 启动 Flask 后端..." -ForegroundColor Green
Write-Host ""
Write-Host "====================================" -ForegroundColor Green
Write-Host "  服务启动信息" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green
Write-Host "后端 API: http://127.0.0.1:5001"
Write-Host ""
Write-Host "测试 API:"
Write-Host "  curl http://127.0.0.1:5001/local_knowledge/list"
Write-Host ""
Write-Host "前端开发:"
Write-Host "  cd frontend"
Write-Host "  npm run dev"
Write-Host ""
Write-Host "按 Ctrl+C 停止服务"
Write-Host "====================================" -ForegroundColor Green
Write-Host ""

# 启动后端
python app.py --host 127.0.0.1 --port 5001
