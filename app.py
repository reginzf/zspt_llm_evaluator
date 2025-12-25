from flask import Flask
from src.flask_funcs import home_bp
from src.flask_funcs.environment import environment_bp
from src.flask_funcs.static_routes import static_bp
import os

# 创建Flask应用
app = Flask(__name__)

# 注册蓝图
app.register_blueprint(home_bp)
app.register_blueprint(environment_bp)
app.register_blueprint(static_bp)

# 设置静态文件和模板文件目录
template_dir = os.path.join(os.path.dirname(__file__), 'src', 'flask_funcs', 'reports', 'templates')
statics_dir = os.path.join(os.path.dirname(__file__), 'src', 'flask_funcs', 'reports', 'statics')
js_dir = os.path.join(statics_dir, 'js')
css_dir = os.path.join(statics_dir, 'css')

# 更新 Flask app 的模板和静态文件配置
app.template_folder = template_dir
app.static_folder = statics_dir

# 静态文件路由 - 使用Flask内置的static路由
# Flask会自动处理/static/路径下的文件

if __name__ == '__main__':
    app.run('0.0.0.0', debug=True)
    # app.run('0.0.0.0')