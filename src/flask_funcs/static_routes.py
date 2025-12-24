from flask import send_from_directory, Blueprint
import os

# 创建蓝图
static_bp = Blueprint('static_bp', __name__)

# 设置静态文件目录
statics_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reports', 'reports_funcs', 'statics')
js_dir = os.path.join(statics_dir, 'js')
css_dir = os.path.join(statics_dir, 'css')

@static_bp.route('/js/<path:filename>')
def custom_js(filename):
    return send_from_directory(js_dir, filename)

@static_bp.route('/css/<path:filename>')
def custom_css(filename):
    return send_from_directory(css_dir, filename)