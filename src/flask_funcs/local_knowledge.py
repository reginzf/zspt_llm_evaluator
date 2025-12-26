from pathlib import Path

from flask import Blueprint, request, jsonify, render_template_string
import os
import logging

from env_config_init import settings
from src.sql_funs.local_knowledge_crud import LocalKnowledgeCrud
from src.flask_funcs.reports.flask_local_knowledge_renderer import LocalKnowledgeRendererFlask

# 创建logger
logger = logging.getLogger(__name__)

# 创建蓝图
local_knowledge_bp = Blueprint('local_knowledge', __name__)

# 导入渲染器
from src.flask_funcs.reports.flask_local_knowledge_renderer import LocalKnowledgeRendererFlask

renderer = LocalKnowledgeRendererFlask()
@local_knowledge_bp.route('/local_knowledge/')
def local_knowledge():
    """获取本地知识目录结构，按列表展示"""
    try:
        # 获取在sql ai_local_knowledge表中的数据，和本地目录中第一级目录，按名称匹配
        # 如果有数据库中的数据则展示数据库的，否则展示本地目录的
        with LocalKnowledgeCrud() as crud:
            # 获取数据库中的本地知识列表
            db_knowledge_list = crud.get_local_knowledge()
            logger.info(f"获取数据库中的本地知识列表: {db_knowledge_list}")
            # 获取本地目录结构
            local_knowledge_path = settings.KNOWLEDGE_LOCAL_PATH
            local_directories = []
            if os.path.exists(local_knowledge_path) and os.path.isdir(local_knowledge_path):
                for item in os.listdir(local_knowledge_path):
                    item_path = os.path.join(local_knowledge_path, item)
                    if os.path.isdir(item_path):
                        local_directories.append(item)
                logger.info(f"获取本地目录结构: {local_directories}")
            else:
                logger.error(f"本地目录不存在: {local_knowledge_path}")
                raise FileExistsError

            # 创建本地知识渲染器并渲染页面

            html_content = renderer.render_local_knowledge_page(db_knowledge_list, local_directories)

        return html_content
    except Exception as e:
        logger.error(f"获取本地知识列表时发生错误: {str(e)}")
        return "页面加载错误", 500


@local_knowledge_bp.route('/local_knowledge_detail/<kno_id>/<kno_name>')
def local_knowledge_detail(kno_id, kno_name):
    """获取特定本地知识的详细信息"""
    try:
        with LocalKnowledgeCrud() as crud:
            # 获取本地知识详情
            knowledge_detail = crud.get_local_knowledge_detail(kno_id)
            logger.info(f"获取本地知识详情: {knowledge_detail}")
            if not knowledge_detail:
                return "未找到知识库信息", 404

            # 获取本地目录指定文件夹的文件名称
            folder_path = Path(settings.KNOWLEDGE_LOCAL_PATH) / kno_name
            local_files = []
            if os.path.exists(folder_path) and os.path.isdir(folder_path):
                for item in os.listdir(folder_path):
                    local_file = os.path.join(folder_path, item)
                    local_files.append(local_file)
                logger.info(f"获取本地目录下文件: {local_files}")
    except Exception as e:
        logger.error(f"获取本地知识详情时发生错误: {str(e)}")
        return "页面加载错误", 500
    return renderer.gen_knowledge_detail(local_files, knowledge_detail)


@local_knowledge_bp.route('/api/local_knowledge_detail/<kno_id>/<kno_name>')
def api_local_knowledge_detail(kno_id, kno_name):
    """API接口：获取特定本地知识的详细信息"""
    try:
        with LocalKnowledgeCrud() as crud:
            # 获取本地知识详情
            knowledge_detail = crud.get_local_knowledge_detail(kno_id)
            logger.info(f"获取本地知识详情: {knowledge_detail}")
            if not knowledge_detail:
                return jsonify({"error": "未找到知识库信息"}), 404

            # 获取本地目录指定文件夹的文件名称
            folder_path = Path(settings.KNOWLEDGE_LOCAL_PATH) / kno_name
            local_files = []
            if os.path.exists(folder_path) and os.path.isdir(folder_path):
                for item in os.listdir(folder_path):
                    local_file = os.path.join(folder_path, item)
                    local_files.append(local_file)
                logger.info(f"获取本地目录下文件: {local_files}")
    except Exception as e:
        logger.error(f"获取本地知识详情时发生错误: {str(e)}")
        return jsonify({"error": "页面加载错误"}), 500
    
    result = renderer.gen_knowledge_detail(local_files, knowledge_detail)
    return jsonify(result)


@local_knowledge_bp.route('/local_knowledge/upload', methods=['POST'])
def upload_local_knowledge():
    """上传文件到本地知识库"""
    try:
        # todo: 实现上传文件到本地知识库的逻辑
        # 获取上传的文件和知识库ID
        file = request.files.get('file')
        kno_id = request.form.get('kno_id')

        if not file or not kno_id:
            return jsonify({"status": "error", "message": "缺少文件或知识库ID"}), 400

        # 实现上传逻辑
        # 1. 保存文件到本地
        # 2. 更新数据库记录
        # 3. 返回成功信息

        # 临时返回成功信息
        return jsonify({"status": "success", "message": "文件上传成功"})
    except Exception as e:
        logger.error(f"上传文件时发生错误: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500
