# AI-KEN 前后端分离部署指南

## 架构概述

```
┌─────────────────────┐      HTTP/REST API      ┌─────────────────────┐
│                     │  ═══════════════════════► │                     │
│   Vue 3 Frontend    │                         │   Flask Backend     │
│   (Port: 5173)      │ ◄═══════════════════════ │   (Port: 5001)      │
│                     │      CORS / JSON        │                     │
└─────────────────────┘                         └─────────────────────┘
```

## 开发环境部署

### 1. 启动后端服务 (Flask)

```bash
# 进入项目目录
cd /path/to/ai-ken

# 激活虚拟环境
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate     # Windows

# 方式1: 使用启动脚本（推荐）
python scripts/start_backend.py --host 0.0.0.0 --port 5001

# 方式2: 使用环境变量配置
export CORS_ALLOW_ALL=true  # 开发环境允许所有来源
python scripts/start_backend.py

# 方式3: 直接启动
python app.py --host 0.0.0.0 --port 5001
```

后端服务将运行在 `http://0.0.0.0:5001`

### 2. 启动前端服务 (Vue)

```bash
# 进入前端目录
cd frontend

# 安装依赖（首次）
npm install

# 启动开发服务器
npm run dev
```

前端服务将运行在 `http://localhost:5173`

### 3. 跨域配置

#### 方案 A: 使用 Vite 代理（推荐开发环境）

前端 `vite.config.ts` 已配置代理，将 API 请求转发到后端：

```typescript
server: {
  proxy: {
    '^/api': {
      target: 'http://127.0.0.1:5001',
      changeOrigin: true,
    },
    // ... 其他 API 路径
  }
}
```

#### 方案 B: 直接跨域访问（后端 CORS）

如果前端和后端部署在不同机器上，需要配置后端 CORS：

```bash
# 方式1: 允许所有来源（仅开发环境）
export CORS_ALLOW_ALL=true
python scripts/start_backend.py

# 方式2: 指定特定来源
export CORS_ORIGINS="http://10.0.112.233:5173,http://192.168.1.100:5173"
python scripts/start_backend.py
```

同时修改前端环境配置 `frontend/.env.development`：

```bash
# 指向实际后端地址
VITE_BACKEND_URL=http://10.0.112.233:5001
```

## 生产环境部署

### 方案 1: 分别部署（推荐）

#### 后端部署

```bash
# 使用 Gunicorn 部署（Linux）
gunicorn -w 4 -b 0.0.0.0:5001 "app:app"

# 或使用 uWSGI
uwsgi --http 0.0.0.0:5001 --wsgi-file app.py --callable app --processes 4 --threads 2
```

#### 前端部署

```bash
cd frontend

# 构建生产版本
npm run build

# 将 dist 目录部署到 Nginx/Apache
# 或使用 serve 快速部署
npm install -g serve
serve -s dist -l 5173
```

### 方案 2: 使用 Nginx 反向代理

```nginx
# /etc/nginx/sites-available/ai-ken

server {
    listen 80;
    server_name ai-ken.example.com;

    # 前端静态文件
    location / {
        root /path/to/ai-ken/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # API 反向代理到 Flask
    location /api/ {
        proxy_pass http://127.0.0.1:5001/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 其他 API 路由
    location /local_knowledge/ {
        proxy_pass http://127.0.0.1:5001/local_knowledge/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # ... 其他 API 路径
}
```

### 方案 3: Docker 部署

```bash
# 构建镜像
docker-compose up -d
```

## 环境变量参考

### 后端环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `FLASK_HOST` | 服务监听地址 | `0.0.0.0` |
| `FLASK_PORT` | 服务端口 | `5001` |
| `FLASK_DEBUG` | 调试模式 | `false` |
| `CORS_ALLOW_ALL` | 允许所有 CORS 来源 | `false` |
| `CORS_ORIGINS` | 额外的 CORS 来源 | `` |
| `VUE_FRONTEND_MODE` | Vue 前端模式 | `auto` |

### 前端环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `VITE_API_BASE_URL` | API 基础路径 | `/api` |
| `VITE_BACKEND_URL` | 后端服务地址 | `http://127.0.0.1:5001` |
| `VITE_USE_MOCK` | 使用 Mock 数据 | `false` |
| `VITE_APP_TITLE` | 应用标题 | `AI-KEN` |

## 常见问题

### 1. CORS 跨域错误

**问题**: 浏览器报 `Access-Control-Allow-Origin` 错误

**解决**:
```bash
# 开发环境允许所有来源
export CORS_ALLOW_ALL=true
python scripts/start_backend.py
```

### 2. API 请求超时

**问题**: 前端无法连接到后端

**解决**:
1. 检查后端是否运行: `curl http://127.0.0.1:5001/local_knowledge/list`
2. 检查防火墙设置
3. 检查前端代理配置 `VITE_BACKEND_URL`

### 3. 静态文件 404

**问题**: 刷新页面后 404

**解决**: 配置 Nginx 或前端路由回退：
```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

## 开发工作流

```bash
# 终端 1: 启动后端
cd /path/to/ai-ken
python scripts/start_backend.py --host 0.0.0.0 --port 5001

# 终端 2: 启动前端
cd /path/to/ai-ken/frontend
npm run dev

# 访问 http://localhost:5173
```
