from flask import Flask, send_from_directory
from src.flask_funcs import home_bp,static_bp
import os

# 创建Flask应用
app = Flask(__name__)

# 注册蓝图
app.register_blueprint(home_bp)
app.register_blueprint(static_bp)

# 设置静态文件和模板文件目录
template_dir = os.path.join(os.path.dirname(__file__), 'src', 'flask_funcs', 'reports', 'templates')
statics_dir = os.path.join(os.path.dirname(__file__), 'src', 'flask_funcs', 'reports', 'statics')
js_dir = os.path.join(statics_dir, 'js')
css_dir = os.path.join(statics_dir, 'css')

# 更新 Flask app 的模板和静态文件配置
app.template_folder = template_dir

# 静态文件路由 - 由于蓝图限制，这些路由在主应用中定义
@app.route('/js/<path:filename>')
def custom_js(filename):
    return send_from_directory(js_dir, filename)

@app.route('/css/<path:filename>')
def custom_css(filename):
    return send_from_directory(css_dir, filename)

if __name__ == '__main__':
    app.run('0.0.0.0',debug=True)
    # app.run('0.0.0.0')