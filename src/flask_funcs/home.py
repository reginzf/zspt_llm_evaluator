from flask import Blueprint, render_template, url_for
import os
from src.flask_funcs.reports.generate_report import load_metric_data
from src.flask_funcs.reports.metrics_analyzer import analyze_metrics
from src.flask_funcs.reports.metrics_dashboard_renderer_flask import MetricsDashboardRenderer
from src.flask_funcs.reports.report_list_renderer_flask import ReportListRendererFlask
from src.flask_funcs.reports.environment_renderer_flask import EnvironmentRendererFlask
from src.sql_funs.environment_crud import Environment_Crud
from env_config_init import REPORT_PATH

# 创建蓝图
home_bp = Blueprint('app', __name__)


@home_bp.route('/')
def index():
    # 获取REPORT_PATH目录下所有.json文件数量
    report_path = REPORT_PATH
    json_files = [f for f in os.listdir(report_path) if f.endswith('.json')]
    report_count = len(json_files)
    
    # 渲染模板
    return render_template('home.html', report_count=report_count, css_path=url_for('static_bp.custom_css', filename='styles.css'))
@home_bp.route('/environment/')
def environment():
    # 获取环境列表数据
    try:
        with Environment_Crud() as env_crud:
            environment_data = env_crud.environment_list()
        current_environment_id = ""  # 默认当前环境ID为空，可以根据需要设置
    except Exception as e:
        environment_data = []
        current_environment_id = ""
    
    # 创建HTML渲染器
    renderer = EnvironmentRendererFlask()
    
    # 渲染模板
    html_content = renderer.render_environment_page(environment_data, current_environment_id)

    return html_content

@home_bp.route('/metric_data/')
def metric_data():
    # 获取REPORT_PATH目录下所有.json文件
    report_path = REPORT_PATH
    json_files = [f for f in os.listdir(report_path) if f.endswith('.json')]
    
    # 创建报告列表渲染器并渲染页面
    renderer = ReportListRendererFlask()
    html_content = renderer.render_report_list(json_files)
    return html_content


@home_bp.route('/report/<path:filename>')
def report(filename):
    # 加载metric数据
    metric_data = load_metric_data(filename)
    if not metric_data:
        return f"无法加载数据文件: {filename}", 404
    
    # 分析数据
    analysis_results = analyze_metrics(metric_data)
    
    # 创建HTML渲染器
    renderer = MetricsDashboardRenderer()
    
    # 渲染模板
    html_content = renderer.render_metrics_dashboard(analysis_results, metric_data)
    
    return html_content