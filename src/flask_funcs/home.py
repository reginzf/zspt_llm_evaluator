from flask import Blueprint, render_template, url_for

# 创建蓝图
home_bp = Blueprint('app', __name__)


@home_bp.route('/')
def index():
    return render_template('home.html', css_path=url_for('static_bp.custom_css', filename='styles.css'))
