from flask import Blueprint
import os
import logging

from env_config_init import REPORT_PATH
from src.flask_funcs.reports.generate_report import load_metric_data
from src.flask_funcs.reports.metrics_analyzer import analyze_metrics
from src.flask_funcs.reports.metrics_dashboard_renderer_flask import MetricsDashboardRenderer

# 创建logger
logger = logging.getLogger(__name__)

# 创建蓝图
report_list_bp = Blueprint('report_list', __name__)

# 导入渲染器
from flask_funcs.reports.report_list_renderer_flask import ReportListRendererFlask


@report_list_bp.route('/report_list/')
def list_reports():
    """获取REPORT_PATH目录下的目录结构"""
    try:
        report_path = REPORT_PATH
        directory_structure = {}

        if os.path.exists(report_path):
            for item in os.listdir(report_path):
                item_path = os.path.join(report_path, item)
                if os.path.isdir(item_path):
                    # 如果是目录，获取该目录下的所有.json文件
                    json_files = [f for f in os.listdir(item_path) if f.endswith('.json')]
                    directory_structure[item] = json_files
                elif item.endswith('.json'):
                    # 如果是根目录下的json文件，放到'根目录'键下
                    if '根目录' not in directory_structure:
                        directory_structure['根目录'] = []
                    directory_structure['根目录'].append(item)


    except Exception as e:
        logger.error(f"获取报告目录结构时发生错误: {str(e)}")
        directory_structure = {}

    # 创建报告列表渲染器并渲染页面
    try:
        renderer = ReportListRendererFlask()
        html_content = renderer.render_report_list_with_directory(directory_structure)
    except Exception as e:
        logger.error(f"渲染报告列表时发生错误: {str(e)}")
        return "页面渲染错误", 500

    return html_content


@report_list_bp.route('/report/<path:filename>')
def report(filename):
    try:
        # 构建完整的文件路径
        full_path = os.path.join(REPORT_PATH, filename)

        # 加载metric数据
        metric_data = load_metric_data(full_path)
        if not metric_data:
            logger.warning(f"无法加载数据文件: {full_path}")
            return f"无法加载数据文件: {full_path}", 404

        # 分析数据
        analysis_results = analyze_metrics(metric_data)

        # 创建HTML渲染器
        renderer = MetricsDashboardRenderer()

        # 渲染模板
        html_content = renderer.render_metrics_dashboard(analysis_results, metric_data)

        logger.info(f"成功渲染报告: {full_path}")

    except Exception as e:
        logger.error(f"处理报告 {filename} 时发生错误: {str(e)}")
        return "处理报告时发生错误", 500

    return html_content
