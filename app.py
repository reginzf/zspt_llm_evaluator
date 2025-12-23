from flask import Flask, send_from_directory
import os
from reports.reports_funcs.generate_report import load_metric_data
from reports.reports_funcs.metrics_analyzer import analyze_metrics
from reports.reports_funcs.html_renderer import HTMLRenderer
from reports.reports_funcs.report_list_renderer import ReportListRenderer
from env_config_init import REPORT_PATH

app = Flask(__name__)

# 设置静态文件和模板文件目录
template_dir = os.path.join(os.path.dirname(__file__), 'reports', 'reports_funcs', 'templates')
statics_dir = os.path.join(os.path.dirname(__file__), 'reports', 'reports_funcs', 'statics')
js_dir = os.path.join(statics_dir, 'js')
css_dir = os.path.join(statics_dir, 'css')

# 更新 Flask app 的模板和静态文件配置
app.template_folder = template_dir

@app.route('/')
def index():
    return '<h1>问答系统召回质量评估报告服务</h1><p>请访问具体的报告路径查看报告</p>'


@app.route('/metric_data/')
def metric_data():
    # 获取REPORT_PATH目录下所有.json文件
    report_path = REPORT_PATH
    json_files = [f for f in os.listdir(report_path) if f.endswith('.json')]
    
    # 创建报告列表渲染器并渲染页面
    renderer = ReportListRenderer()
    html_content = renderer.render_report_list(json_files)
    return html_content

@app.route('/report/<path:filename>')
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

@app.route('/js/<path:filename>')
def custom_js(filename):
    return send_from_directory(js_dir, filename)

@app.route('/css/<path:filename>')
def custom_css(filename):
    return send_from_directory(css_dir, filename)

if __name__ == '__main__':
    app.run('0.0.0.0',debug=True)