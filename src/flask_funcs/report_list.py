from flask import Blueprint, render_template
import os
import logging
from typing import Dict, List
from env_config_init import REPORT_PATH

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
        
        # 计算总的报告数量
        report_count = sum(len(files) for files in directory_structure.values())
    except Exception as e:
        logger.error(f"获取报告目录结构时发生错误: {str(e)}")
        directory_structure = {}
        report_count = 0

    # 创建报告列表渲染器并渲染页面
    try:
        renderer = ReportListRendererFlask()
        html_content = renderer.render_report_list_with_directory(directory_structure)
    except Exception as e:
        logger.error(f"渲染报告列表时发生错误: {str(e)}")
        return "页面渲染错误", 500

    return html_content