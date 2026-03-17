from flask import Blueprint, jsonify, render_template_string
import os
import logging
from datetime import datetime

from src.utils.pub_funs import load_metric_data
from src.flask_funcs.reports.metrics_analyzer import analyze_metrics
from src.flask_funcs.reports.flask_metrics_dashboard_renderer import MetricsDashboardRenderer
from src.flask_funcs.common_utils import download_minio_file_to_temp
from src.utils.minio_client import get_knowledge_files_client

# 创建logger
logger = logging.getLogger(__name__)

# 创建蓝图
report_list_bp = Blueprint('report_list', __name__)


# 报告渲染HTML模板
REPORT_VIEW_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>报告详情 - {{ filename }}</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: #f5f7fa;
            padding: 20px;
            line-height: 1.6;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
        }
        .header h1 {
            font-size: 24px;
            margin-bottom: 10px;
        }
        .header .meta {
            opacity: 0.9;
            font-size: 14px;
        }
        .content {
            padding: 30px;
        }
        .json-viewer {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 6px;
            padding: 20px;
            overflow-x: auto;
        }
        .json-viewer pre {
            margin: 0;
            font-family: "Consolas", "Monaco", "Courier New", monospace;
            font-size: 14px;
            line-height: 1.5;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        .string { color: #28a745; }
        .number { color: #007bff; }
        .boolean { color: #dc3545; }
        .null { color: #6c757d; }
        .key { color: #d63384; }
        .back-btn {
            display: inline-block;
            margin-top: 20px;
            padding: 10px 20px;
            background: #6c757d;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            transition: background 0.2s;
        }
        .back-btn:hover {
            background: #5a6268;
        }
        .error {
            padding: 40px;
            text-align: center;
            color: #dc3545;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 {{ filename }}</h1>
            <div class="meta">路径: {{ object_name }}</div>
        </div>
        <div class="content">
            {% if error %}
            <div class="error">
                <h2>加载失败</h2>
                <p>{{ error }}</p>
            </div>
            {% else %}
            <div class="json-viewer">
                <pre>{{ json_content }}</pre>
            </div>
            <a href="javascript:history.back()" class="back-btn">← 返回</a>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

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


@report_list_bp.route('/report/<path:object_name>')
@report_list_bp.route('/api/report/<path:object_name>')
def view_report(object_name):
    """
    查看知识库报告详情页面

    从 MinIO 加载知识库报告 JSON 文件并使用 MetricsDashboardRenderer 渲染为 HTML 页面
    """
    tmp_report_path = None
    try:
        # URL 解码对象名称
        from urllib.parse import unquote
        object_name = unquote(object_name)

        # 标准化路径：将URL中的反斜杠转换为正斜杠（MinIO使用正斜杠）
        object_name = object_name.replace(os.sep, '/')

        logger.info(f"尝试从 MinIO 加载知识库报告: {object_name}")

        # 从 MinIO 下载报告到临时文件（复用通用工具函数）
        tmp_report_path = download_minio_file_to_temp(object_name)

        if not tmp_report_path:
            logger.warning(f"MinIO 中不存在报告: {object_name}")
            return render_template_string(
                REPORT_VIEW_TEMPLATE,
                filename=os.path.basename(object_name),
                object_name=object_name,
                error=f"报告文件不存在: {object_name}",
                json_content=None
            ), 404

        # 从临时文件加载 metric 数据
        metric_data = load_metric_data(tmp_report_path)

        if not metric_data:
            logger.warning(f"无法加载报告数据: {object_name}")
            return render_template_string(
                REPORT_VIEW_TEMPLATE,
                filename=os.path.basename(object_name),
                object_name=object_name,
                error=f"无法加载报告数据: {object_name}",
                json_content=None
            ), 404

        # 分析数据
        analysis_results = analyze_metrics(metric_data)

        # 创建 HTML 渲染器
        renderer = MetricsDashboardRenderer()

        # 渲染模板
        html_content = renderer.render_metrics_dashboard(analysis_results, metric_data)

        logger.info(f"成功渲染知识库报告: {object_name}")

    except Exception as e:
        logger.error(f"处理知识库报告 {object_name} 时发生错误: {str(e)}", exc_info=True)
        return render_template_string(
            REPORT_VIEW_TEMPLATE,
            filename=os.path.basename(object_name) if 'object_name' in locals() else '未知',
            object_name=object_name if 'object_name' in locals() else '',
            error=f"处理报告时发生错误: {str(e)}",
            json_content=None
        ), 500
    finally:
        # 清理临时文件 - 使用 try-except 避免 TOCTOU 问题
        if tmp_report_path:
            try:
                os.unlink(tmp_report_path)
            except FileNotFoundError:
                pass  # 文件已被删除，无需处理

    return html_content


