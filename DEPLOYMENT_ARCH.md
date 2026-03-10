# AI-KEN 生产环境部署架构

## 部署模式

采用**前后端分离**架构，部署在同一台机器上：

```
┌─────────────────────────────────────────────────────────────┐
│                      用户访问                                │
│                         │                                   │
│                         ▼                                   │
│              ┌─────────────────────┐                        │
│              │   Nginx (端口5002)  │  ← ai-ken-frontend     │
│              │  - 静态文件服务      │                        │
│              │  - API 反向代理      │                        │
│              └──────────┬──────────┘                        │
│                         │                                   │
│              ┌──────────┴──────────┐                        │
│              │                     │                        │
│              ▼                     ▼                        │
│    ┌─────────────────┐   ┌─────────────────┐               │
│    │  前端静态文件    │   │ Flask API      │  ← 端口5001    │
│    │  (Vue3 dist)    │   │  ai-ken-backend │               │
│    └─────────────────┘   └─────────────────┘               │
│                                  │                          │
│                                  ▼                          │
│                          ┌──────────────┐                   │
│                          │  PostgreSQL  │                   │
│                          │  Qdrant      │                   │
│                          └──────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

## 服务配置

### 1. ai-ken-backend (后端服务)

- **端口**: 5001
- **监听**: 127.0.0.1（仅本地访问，外部通过 Nginx 代理）
- **服务文件**: `/etc/systemd/system/ai-ken-backend.service`
- **功能**: Flask REST API

```ini
[Unit]
Description=AI-KEN Backend Service (Flask API)
After=network.target

[Service]
Type=simple
User=<deploy_user>
WorkingDirectory=<project_dir>
Environment=PATH=<project_dir>/venv/bin
Environment=FLASK_ENV=production
Environment=CORS_ALLOW_ALL=false
ExecStart=<project_dir>/venv/bin/python app.py --host 127.0.0.1 --port 5001
Restart=always
RestartSec=10
```

### 2. ai-ken-frontend (前端服务)

- **端口**: 5002
- **服务文件**: `/etc/systemd/system/ai-ken-frontend.service`
- **功能**: Nginx 静态文件服务 + API 代理

```ini
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
ExecStop=/bin/kill -s QUIT $MAINPID
Restart=always
RestartSec=5
```

### 3. Nginx 配置

配置文件: `/etc/nginx/conf.d/ai-ken.conf`

```nginx
server {
    listen 5002;
    server_name localhost;
    
    # 前端静态文件
    root <project_dir>/frontend/dist;
    index index.html;
    
    # Vue Router history 模式支持
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # API 代理到后端
    location /api/ {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # 其他后端路由代理
    location /local_knowledge/ { proxy_pass http://127.0.0.1:5001; }
    location /environment/ { proxy_pass http://127.0.0.1:5001; }
    location /label_studio/ { proxy_pass http://127.0.0.1:5001; }
    location /qdrant/ { proxy_pass http://127.0.0.1:5001; }
}
```

## 部署脚本

**注册服务脚本**: `scripts/register_service_with_proxy.sh`

功能：
1. 安装/升级 Node.js 20
2. 安装前端依赖并构建
3. 安装并配置 Nginx
4. 创建并启动两个 systemd 服务

## 管理命令

```bash
# 查看服务状态
sudo systemctl status ai-ken-backend
sudo systemctl status ai-ken-frontend

# 启动服务
sudo systemctl start ai-ken-backend
sudo systemctl start ai-ken-frontend

# 停止服务
sudo systemctl stop ai-ken-backend
sudo systemctl stop ai-ken-frontend

# 重启服务
sudo systemctl restart ai-ken-backend
sudo systemctl restart ai-ken-frontend

# 查看日志
sudo journalctl -u ai-ken-backend -f
sudo journalctl -u ai-ken-frontend -f
```

## 访问地址

- **前端界面**: `http://<server_ip>:5002`
- **API 接口**: `http://<server_ip>:5002/api/`

## 注意事项

1. **后端安全**: 后端服务仅监听 127.0.0.1，外部无法直接访问 5001 端口
2. **服务依赖**: 前端服务依赖于后端服务，启动时会自动启动后端
3. **代理配置**: 如需修改代理设置，编辑服务文件后执行 `sudo systemctl daemon-reload`
4. **防火墙**: 确保开放 5002 端口供外部访问
