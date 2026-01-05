from flask import send_from_directory, Blueprint
import os

# 创建蓝图
static_bp = Blueprint('static_bp', __name__)

# 设置静态文件目录
import os
# 获取项目根目录
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
statics_dir = os.path.join(project_root, 'src', 'flask_funcs', 'reports', 'statics')
js_dir = os.path.join(statics_dir, 'js')
css_dir = os.path.join(statics_dir, 'css')
lib_dir = os.path.join(js_dir, 'lib')


@static_bp.route('/js/<path:filename>')
def custom_js(filename):
    return send_from_directory(js_dir, filename)


@static_bp.route('/css/<path:filename>')
def custom_css(filename):
    return send_from_directory(css_dir, filename)


@static_bp.route('/js/lib/<path:filename>')
def custom_lib(filename):
    return send_from_directory(lib_dir, filename)