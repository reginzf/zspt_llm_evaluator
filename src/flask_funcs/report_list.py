from flask import Blueprint, jsonify
import os
import logging
import tempfile
from datetime import datetime

from env_config_init import REPORT_PATH
from src.utils.pub_funs import load_metric_data
from src.flask_funcs.reports.metrics_analyzer import analyze_metrics
from src.flask_funcs.reports.flask_metrics_dashboard_renderer import MetricsDashboardRenderer
from src.flask_funcs.common_utils import get_directory_structure
from src.utils.minio_client import get_knowledge_files_client

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


@report_list_bp.route('/report_list/data')
@report_list_bp.route('/api/report_list/data')
def list_reports_data():
    """从 MinIO 获取 reports 目录下的报告文件列表（JSON API供Vue前端使用）"""
    try:
        # 从 MinIO 获取文件列表
        minio_client = get_knowledge_files_client()
        file_list = minio_client.list_files(prefix='reports/', recursive=True)
        
        # 按目录分组
        directory_structure = {}
        reports = []
        
        for file_info in file_list:
            object_name = file_info['name']
            
            # 只处理 .json 文件
            if not object_name.endswith('.json'):
                continue
            
            # 解析路径：reports/子目录/文件名.json 或 reports/文件名.json
            # 去掉 'reports/' 前缀
            relative_path = object_name[len('reports/'):] if object_name.startswith('reports/') else object_name
            
            # 确定目录和文件名
            if '/' in relative_path:
                # 有子目录
                parts = relative_path.split('/')
                directory = parts[0]
                file_name = parts[-1]
            else:
                # 根目录
                directory = '根目录'
                file_name = relative_path
            
            # 添加到目录结构
            if directory not in directory_structure:
                directory_structure[directory] = []
            directory_structure[directory].append(file_name)
            
            # 格式化时间
            last_modified = file_info.get('last_modified')
            created_at = None
            if last_modified:
                if isinstance(last_modified, datetime):
                    created_at = last_modified.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    # 处理可能的字符串格式
                    created_at = str(last_modified)
            
            reports.append({
                'name': file_name,
                'path': relative_path,  # 用于查看的相对路径
                'object_name': object_name,  # 完整的 MinIO 对象名称
                'directory': directory,
                'size': file_info.get('size', 0),
                'created_at': created_at
            })
        
        return jsonify({
            'success': True,
            'data': reports,
            'directory_structure': directory_structure
        })

    except Exception as e:
        logger.error(f"从 MinIO 获取报告列表时发生错误: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'获取报告列表失败: {str(e)}',
            'data': [],
            'directory_structure': {}
        }), 500


@report_list_bp.route('/report/<path:filename>')
def report(filename):
    """从 MinIO 加载并显示报告"""
    try:
        # 标准化路径：将URL中的反斜杠转换为正斜杠（MinIO使用正斜杠）
        filename = filename.replace(os.sep, '/')
        
        # 确保路径包含 reports/ 前缀
        if not filename.startswith('reports/'):
            object_name = f'reports/{filename}'
        else:
            object_name = filename
        
        logger.info(f"尝试从 MinIO 加载报告: {object_name}")
        
        # 从 MinIO 下载报告到临时文件
        minio_client = get_knowledge_files_client()
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            tmp_report_path = tmp_file.name
        
        try:
            # 下载报告文件
            download_success = minio_client.download_file(object_name, tmp_report_path)
            
            if not download_success:
                logger.warning(f"MinIO 中不存在报告: {object_name}")
                return f"报告文件不存在: {filename}", 404
            
            # 从临时文件加载 metric 数据
            metric_data = load_metric_data(tmp_report_path)
            
            if not metric_data:
                logger.warning(f"无法加载报告数据: {object_name}")
                return f"无法加载报告数据: {filename}", 404

            # 分析数据
            analysis_results = analyze_metrics(metric_data)

            # 创建HTML渲染器
            renderer = MetricsDashboardRenderer()

            # 渲染模板
            html_content = renderer.render_metrics_dashboard(analysis_results, metric_data)

            logger.info(f"成功渲染报告: {object_name}")
            
        finally:
            # 清理临时文件
            if os.path.exists(tmp_report_path):
                os.unlink(tmp_report_path)

    except Exception as e:
        logger.error(f"处理报告 {filename} 时发生错误: {str(e)}", exc_info=True)
        return f"处理报告时发生错误: {str(e)}", 500

    return html_content
