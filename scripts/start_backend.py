#!/usr/bin/env python3
"""
Flask 后端服务启动脚本

使用方法:
    python scripts/start_backend.py          # 使用默认配置启动
    python scripts/start_backend.py --host 0.0.0.0 --port 5001
    
环境变量:
    FLASK_HOST: 服务监听地址 (默认: 0.0.0.0)
    FLASK_PORT: 服务端口 (默认: 5001)
    FLASK_DEBUG: 是否开启调试模式 (默认: false)
    CORS_ALLOW_ALL: 是否允许所有 CORS 来源 (默认: false, 开发环境可设为 true)
    CORS_ORIGINS: 额外的 CORS 来源，逗号分隔 (例如: http://10.0.112.233:5173,http://192.168.1.100:5173)
"""

import os
import sys
import argparse

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app import app, PostgreSQLManager


def main():
    parser = argparse.ArgumentParser(description='启动 AI-KEN Flask 后端服务')
    parser.add_argument('--host', default=os.environ.get('FLASK_HOST', '0.0.0.0'),
                        help='服务监听地址 (默认: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=int(os.environ.get('FLASK_PORT', 5001)),
                        help='服务端口 (默认: 5001)')
    parser.add_argument('--debug', action='store_true', 
                        default=os.environ.get('FLASK_DEBUG', 'false').lower() == 'true',
                        help='开启调试模式')
    
    args = parser.parse_args()
    
    # 初始化数据库连接池
    print('=' * 60)
    print('AI-KEN Flask Backend Service')
    print('=' * 60)
    print(f'Initializing database connection pool...')
    try:
        PostgreSQLManager.initialize_pool(minconn=10, maxconn=50)
        print('Database connection pool initialized successfully!')
    except Exception as e:
        print(f'[ERROR] Database initialization failed: {e}')
        sys.exit(1)
    
    # 显示配置信息
    cors_allow_all = os.environ.get('CORS_ALLOW_ALL', 'false').lower() == 'true'
    cors_origins = os.environ.get('CORS_ORIGINS', '')
    
    print(f'\nConfiguration:')
    print(f'  Host: {args.host}')
    print(f'  Port: {args.port}')
    print(f'  Debug: {args.debug}')
    print(f'  CORS Allow All: {cors_allow_all}')
    if cors_origins:
        print(f'  CORS Origins: {cors_origins}')
    print(f'\nStarting server...')
    print(f'API Base URL: http://{args.host}:{args.port}')
    print('=' * 60)
    
    # 启动 Flask 服务
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    main()
