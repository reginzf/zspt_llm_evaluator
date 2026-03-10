@echo off
chcp 65001 >nul
:: AI-KEN 开发环境一键启动脚本 (Windows)
:: 使用: scripts\start_dev.bat

echo ====================================
echo   AI-KEN 开发环境启动脚本
echo ====================================
echo.

:: 项目根目录
set "PROJECT_ROOT=%~dp0.."
cd /d "%PROJECT_ROOT%"

:: 检查虚拟环境
if not exist ".venv" (
    echo [WARN] 虚拟环境不存在，正在创建...
    python -m venv .venv
)

:: 激活虚拟环境
echo [1/4] 激活虚拟环境...
call .venv\Scripts\activate.bat

:: 安装依赖
echo [2/4] 检查 Python 依赖...
pip install -q flask flask-cors psycopg2-binary 2>nul

:: 设置环境变量
set CORS_ALLOW_ALL=true
set FLASK_HOST=0.0.0.0
set FLASK_PORT=5001

echo [3/4] 启动 Flask 后端...
echo 后端服务将在 http://0.0.0.0:5001 启动
echo.

:: 后台启动后端（使用 start 命令）
start "AI-KEN Backend" python scripts/start_backend.py --host 0.0.0.0 --port 5001

:: 等待后端启动
timeout /t 3 /nobreak >nul

echo [4/4] 启动 Vue 前端...
echo 前端服务将在 http://localhost:5173 启动
echo.

:: 进入前端目录
cd frontend

:: 检查 node_modules
if not exist "node_modules" (
    echo [WARN] node_modules 不存在，正在安装...
    call npm install
)

echo ====================================
echo   服务启动完成！
echo ====================================
echo.
echo   前端: http://localhost:5173
echo   后端: http://localhost:5001
echo.
echo   关闭窗口即可停止服务
echo.

:: 启动前端
npm run dev
