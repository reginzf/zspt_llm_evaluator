from flask import Blueprint
import os
import logging

from env_config_init import REPORT_PATH
from utils.pub_funs import load_metric_data
from src.flask_funcs.reports.metrics_analyzer import analyze_metrics
from src.flask_funcs.reports.flask_metrics_dashboard_renderer import MetricsDashboardRenderer
from src.flask_funcs.common_utils import get_directory_structure

# 创建logger
logger = logging.getLogger(__name__)

# 创建蓝图
report_list_bp = Blueprint('report_list', __name__)

# 导入渲染器
from src.flask_funcs.reports.flask_report_list_renderer import ReportListRendererFlask


@report_list_bp.route('/report_list/')
def list_reports():
    """获取REPORT_PATH目录下的目录结构"""
    try:
        report_path = REPORT_PATH
        # 使用通用的目录结构获取函数
        directory_structure = get_directory_structure(report_path, '.json')

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
