import argparse
import sys
import os
from datetime import datetime

from flask import Flask, send_from_directory, abort
from flask_cors import CORS
from src.flask_funcs import environment_bp, report_list_bp, static_bp, local_knowledge_bp, \
    local_knowledge_detail_bp, label_studio_env_bp, local_knowledge_question_bp
from src.flask_funcs.local_knowledge_detail_label_studio import local_knowledge_label_studio_bp
from src.flask_funcs.local_knowledge_detail_task import local_knowledge_detail_task_bp
from src.flask_funcs.knowledge_base import knowledge_base_bp
from src.flask_funcs.qa_data_group import qa_data_group_bp
from src.flask_funcs.qa_data import qa_data_bp
from src.flask_funcs.llm_model_routes import llm_model_bp
from src.flask_funcs.annotation_tasks import annotation_tasks_bp
from src.sql_funs.sql_base import PostgreSQLManager

# 创建日志目录
LOG_DIR = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

# 定义日志文件路径
STDOUT_LOG = os.path.join(LOG_DIR, 'app_stdout.log')
STDERR_LOG = os.path.join(LOG_DIR, 'app_stderr.log')


class DualLogger:
    """双日志类：同时输出到控制台和文件"""
    def __init__(self, filepath, stream):
        self.filepath = filepath
        self.stream = stream  # 原始流 (sys.stdout 或 sys.stderr)
        # 清空旧日志文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# Log started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    def write(self, message):
        # 写入原始流（控制台）
        self.stream.write(message)
        self.stream.flush()
        # 写入文件
        with open(self.filepath, 'a', encoding='utf-8') as f:
            f.write(message)

    def flush(self):
        self.stream.flush()

    def fileno(self):
        return self.stream.fileno()


# 重定向 stdout 和 stderr
sys.stdout = DualLogger(STDOUT_LOG, sys.stdout)
sys.stderr = DualLogger(STDERR_LOG, sys.stderr)

# 创建Flask应用
app = Flask(__name__)

# 配置 CORS - 允许前端跨域访问
# 支持从环境变量读取额外的来源，或者使用通配符*（仅开发环境）
import os

# 基础来源列表（本地开发）
_base_origins = [
    "http://localhost:5001",
    "http://127.0.0.1:5001", 
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]

# 从环境变量读取额外来源（生产环境配置）
_extra_origins = os.environ.get('CORS_ORIGINS', '').split(',')
_extra_origins = [o.strip() for o in _extra_origins if o.strip()]

# 如果设置 CORS_ALLOW_ALL=true，则允许所有来源（仅开发环境！）
_allow_all = os.environ.get('CORS_ALLOW_ALL', 'false').lower() == 'true'

if _allow_all:
    _cors_origins = "*"
    print("[WARNING] CORS 已配置为允许所有来源（CORS_ALLOW_ALL=true），仅用于开发环境！")
else:
    _cors_origins = _base_origins + _extra_origins
    print(f"[INFO] CORS 来源: {_cors_origins}")

CORS(app, resources={
    r"/api/*": {
        "origins": _cors_origins,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    },
    r"/local_knowledge/*": {
        "origins": _cors_origins,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "supports_credentials": True
    },
    r"/local_knowledge/upload": {
        "origins": _cors_origins,
        "methods": ["POST", "OPTIONS"],
        "supports_credentials": True
    },
    r"/local_knowledge_detail/*": {
        "origins": _cors_origins,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "supports_credentials": True
    },
    r"/local_knowledge_doc/*": {
        "origins": _cors_origins,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "supports_credentials": True
    },
    r"/environment/*": {
        "origins": _cors_origins,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "supports_credentials": True
    },
    r"/environment_detail/*": {
        "origins": _cors_origins,
        "methods": ["GET", "POST", "OPTIONS"],
        "supports_credentials": True
    },
    r"/environment_detail_list": {
        "origins": _cors_origins,
        "methods": ["POST", "OPTIONS"],
        "supports_credentials": True
    },
    r"/label_studio_env/*": {
        "origins": _cors_origins,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "supports_credentials": True
    },
    r"/report_list/*": {
        "origins": _cors_origins,
        "methods": ["GET", "POST", "OPTIONS"],
        "supports_credentials": True
    },
    r"/knowledge_base/*": {
        "origins": _cors_origins,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "supports_credentials": True
    },
    r"/annotation_tasks/*": {
        "origins": _cors_origins,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "supports_credentials": True
    },
    r"/llm/*": {
        "origins": _cors_origins,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "supports_credentials": True
    },
    r"/qa/*": {
        "origins": _cors_origins,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "supports_credentials": True
    }
})

# 注册蓝图 (API 路由优先)
# 注意：前后端分离模式下，API 蓝图仍然需要注册，页面路由由 Vue 前端接管
app.register_blueprint(qa_data_group_bp)
app.register_blueprint(qa_data_bp)
app.register_blueprint(llm_model_bp)
app.register_blueprint(annotation_tasks_bp)
app.register_blueprint(knowledge_base_bp)  # API 路由保留
app.register_blueprint(local_knowledge_bp)  # API 路由保留（/local_knowledge/list 等）
app.register_blueprint(local_knowledge_detail_bp)  # API 路由保留
app.register_blueprint(label_studio_env_bp)  # API 路由保留
app.register_blueprint(local_knowledge_question_bp)  # API 路由保留
app.register_blueprint(local_knowledge_label_studio_bp)  # API 路由保留
app.register_blueprint(local_knowledge_detail_task_bp)  # API 路由保留
app.register_blueprint(environment_bp)  # API 路由保留
app.register_blueprint(report_list_bp)  # API 路由保留
app.register_blueprint(static_bp)

# 设置静态文件和模板文件目录
template_dir = os.path.join(os.path.dirname(__file__), 'src', 'flask_funcs', 'reports', 'templates')
statics_dir = os.path.join(os.path.dirname(__file__), 'src', 'flask_funcs', 'reports', 'statics')
js_dir = os.path.join(statics_dir, 'js')
css_dir = os.path.join(statics_dir, 'css')

# 更新 Flask app 的模板和静态文件配置
app.template_folder = template_dir
app.static_folder = statics_dir

# Vue 3 前端静态文件目录
frontend_dist_dir = os.path.join(os.path.dirname(__file__), 'frontend', 'dist')

# 从环境变量读取配置，默认为自动检测
VUE_FRONTEND_MODE = os.environ.get('VUE_FRONTEND_MODE', 'auto').lower()

if VUE_FRONTEND_MODE == 'force':
    # 强制使用 Vue 前端
    use_vue_frontend = True
    print("[INFO] VUE_FRONTEND_MODE=force, 强制使用 Vue 3 前端")
elif VUE_FRONTEND_MODE == 'disable':
    # 禁用 Vue 前端，使用传统模板
    use_vue_frontend = False
    print("[INFO] VUE_FRONTEND_MODE=disable, 使用传统 Flask 模板")
else:
    # 自动检测
    use_vue_frontend = os.path.exists(frontend_dist_dir) and os.path.exists(os.path.join(frontend_dist_dir, 'index.html'))
    if use_vue_frontend:
        print(f"[INFO] Vue 前端构建目录已找到: {frontend_dist_dir}")
        print("[INFO] 将使用 Vue 3 前端替代传统模板")
    else:
        print(f"[WARNING] Vue 前端构建目录不存在或缺少 index.html: {frontend_dist_dir}")
        print("[WARNING] 将回退到使用传统 Flask 模板")

# Vue SPA 路由回退 - 所有非 API 路由返回 Vue 的 index.html
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_vue_app(path):
    """
    服务 Vue 3 前端应用
    - API 路由由 Blueprint 优先处理
    - 静态文件优先从 dist 目录提供
    - 其他所有路由返回 index.html (SPA 回退)
    """
    if not use_vue_frontend:
        # 如果没有 Vue 构建，返回传统首页
        from flask import render_template, url_for
        return render_template('home.html', css_path=url_for('static_bp.custom_css', filename='styles.css'))
    
    # API 路由不应该到达这里，因为蓝图路由优先
    # 但如果用户直接访问某个 API URL，而 API 不存在时，会走到这里
    # 做一下防护，返回 404
    # 注意：以下前缀已移至 Vue3 前端处理
    api_prefixes = (
        'api/', 'static/', 'css/', 'js/'
    )
    if any(path.startswith(prefix) for prefix in api_prefixes):
        abort(404)
    
    # 检查是否是静态资源请求 (JS/CSS/assets 等)
    static_file = os.path.join(frontend_dist_dir, path)
    if path and os.path.exists(static_file) and os.path.isfile(static_file):
        return send_from_directory(frontend_dist_dir, path)
    
    # 所有其他路由返回 Vue 的 index.html (SPA 回退)
    # 这支持 Vue Router 的 history 模式
    return send_from_directory(frontend_dist_dir, 'index.html')

if __name__ == '__main__':
    # 初始化数据库连接池（应用启动时调用一次）
    print('Initializing database connection pool...')
    PostgreSQLManager.initialize_pool(minconn=10, maxconn=50)
    print('Database connection pool initialized successfully!')

    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='AI-KEN Application')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host address (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5001, help='Port number (default: 5001)')
    parser.add_argument('--debug', action='store_true', default=False, help='Enable debug mode (default: False)')

    args = parser.parse_args()

    print(f'Starting server on {args.host}:{args.port}')
    print(f'Debug mode: {args.debug}')

    app.run(args.host, port=args.port, debug=args.debug)
