from flask import Blueprint, jsonify, render_template_string
import os
import logging
import tempfile
import json
from datetime import datetime

from env_config_init import REPORT_PATH
from src.utils.pub_funs import load_metric_data
from src.flask_funcs.reports.metrics_analyzer import analyze_metrics

from src.flask_funcs.common_utils import get_directory_structure
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


def _is_llm_evaluation_report(report_data: dict) -> bool:
    """
    检查报告是否为 LLM 评估报告
    
    LLM 评估报告包含 evaluation_summary 和 results 字段
    """
    return isinstance(report_data, dict) and 'evaluation_summary' in report_data and 'results' in report_data


@report_list_bp.route('/report/<path:object_name>')
def view_report(object_name):
    """
    查看报告详情页面
    
    从 MinIO 加载报告 JSON 文件并渲染为 HTML 页面
    根据报告类型使用相应的渲染器
    """
    try:
        # URL 解码对象名称
        from urllib.parse import unquote
        object_name = unquote(object_name)
        
        # 标准化路径
        object_name = object_name.replace(os.sep, '/')
        
        logger.info(f"尝试从 MinIO 加载报告: {object_name}")
        
        # 从 MinIO 获取报告文件
        minio_client = get_knowledge_files_client()
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            tmp_report_path = tmp_file.name
        
        try:
            # 下载报告文件
            download_success = minio_client.download_file(object_name, tmp_report_path)
            
            if not download_success:
                logger.warning(f"MinIO 中不存在报告: {object_name}")
                return render_template_string(
                    REPORT_VIEW_TEMPLATE,
                    filename=os.path.basename(object_name),
                    object_name=object_name,
                    error=f"报告文件不存在: {object_name}",
                    json_content=None
                ), 404
            
            # 读取并解析 JSON 数据
            with open(tmp_report_path, 'r', encoding='utf-8') as f:
                report_data = json.load(f)
            
            # 检查报告类型并使用相应的渲染器
            if _is_llm_evaluation_report(report_data):
                # 使用 LLM 评估报告渲染器
                logger.info(f"检测到 LLM 评估报告，使用专业渲染器: {object_name}")
                from src.flask_funcs.reports.flask_llm_evaluation_renderer import LLMEvaluationRenderer
                renderer = LLMEvaluationRenderer()
                return renderer.render_evaluation_report(report_data, os.path.basename(object_name))
            else:
                # 使用通用 JSON 查看器
                json_content = json.dumps(report_data, ensure_ascii=False, indent=2)
                logger.info(f"使用通用 JSON 查看器渲染报告: {object_name}")
                return render_template_string(
                    REPORT_VIEW_TEMPLATE,
                    filename=os.path.basename(object_name),
                    object_name=object_name,
                    error=None,
                    json_content=json_content
                )
            
        finally:
            # 清理临时文件
            if os.path.exists(tmp_report_path):
                os.unlink(tmp_report_path)
                
    except json.JSONDecodeError as e:
        logger.error(f"报告文件 JSON 解析失败 {object_name}: {str(e)}")
        return render_template_string(
            REPORT_VIEW_TEMPLATE,
            filename=os.path.basename(object_name),
            object_name=object_name,
            error=f"报告文件格式错误 (非有效 JSON): {str(e)}",
            json_content=None
        ), 500
    except Exception as e:
        logger.error(f"处理报告 {object_name} 时发生错误: {str(e)}", exc_info=True)
        return render_template_string(
            REPORT_VIEW_TEMPLATE,
            filename=os.path.basename(object_name) if 'object_name' in locals() else '未知',
            object_name=object_name if 'object_name' in locals() else '',
            error=f"处理报告时发生错误: {str(e)}",
            json_content=None
        ), 500


