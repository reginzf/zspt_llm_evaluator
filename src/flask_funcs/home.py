from flask import Blueprint, render_template
import os
from src.flask_funcs.reports.generate_report import load_metric_data
from src.flask_funcs.reports.metrics_analyzer import analyze_metrics
from src.flask_funcs.reports.html_renderer import HTMLRenderer
from src.flask_funcs.reports.report_list_renderer import ReportListRenderer
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
    return render_template('home.html', report_count=report_count, css_path='/css/styles.css')


@home_bp.route('/metric_data/')
def metric_data():
    # 获取REPORT_PATH目录下所有.json文件
    report_path = REPORT_PATH
    json_files = [f for f in os.listdir(report_path) if f.endswith('.json')]
    
    # 创建报告列表渲染器并渲染页面
    renderer = ReportListRenderer()
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
    renderer = HTMLRenderer()
    
    # 渲染模板
    html_content = renderer.render_metrics_dashboard(analysis_results, metric_data)
    
    return html_content