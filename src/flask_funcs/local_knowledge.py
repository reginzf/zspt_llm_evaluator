from pathlib import Path

from flask import Blueprint, request, jsonify, render_template_string
import os
import logging

import shutil
from env_config_init import settings
from src.sql_funs import LocalKnowledgeCrud

from src.flask_funcs.common_utils import     generate_unique_id

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
            html_content = renderer.render_local_knowledge_page(db_knowledge_list)

        return html_content
    except Exception as e:
        logger.error(f"获取本地知识列表时发生错误: {str(e)}")
        return "页面加载错误", 500


@local_knowledge_bp.route('/local_knowledge/create', methods=['POST'])
def local_knowledge_create():
    """创建本地知识库"""
    knowledge_path = None
    try:
        data = request.get_json()
        kno_name = data.get('kno_name')
        kno_describe = data.get('kno_describe', '')

        if not kno_name or not kno_name.strip():
            return jsonify({'success': False, 'message': '知识库名称不能为空'}), 400
        # 生成唯一ID作为知识库ID
        kno_id = generate_unique_id(prefix="kno", length=8)
        dir_filename = f"{kno_name.strip()}_{kno_id}"
        # 创建知识库目录
        knowledge_path = os.path.join(settings.KNOWLEDGE_LOCAL_PATH, dir_filename)

        # 检查目录是否已存在
        if os.path.exists(knowledge_path):
            return jsonify({'success': False, 'message': '知识库目录已存在'}), 400

        # 创建目录
        os.makedirs(knowledge_path, exist_ok=True)

        # 将相关信息写入数据库，状态为1（未开始）
        with LocalKnowledgeCrud() as crud:
            success = crud.local_knowledge_insert(
                kno_id=kno_id,
                kno_name=kno_name,  # 保存原始名称（可能包含空格等）
                kno_describe=kno_describe,
                kno_path=dir_filename,  # 存储目录名（已去除首尾空格）
                ls_status=1  # 状态为1，表示未开始
            )
            if success:
                return jsonify({
                    'success': True,
                    'message': '知识库创建成功',
                    'kno_id': kno_id
                })
            else:
                # 如果数据库插入失败，删除已创建的目录
                if os.path.exists(knowledge_path):
                    shutil.rmtree(knowledge_path)
                return jsonify({'success': False, 'message': '数据库操作失败'}), 500
    except Exception as e:
        logger.error(f"创建知识库时发生错误: {str(e)}")
        # 如果出现异常，确保清理已创建的目录
        if knowledge_path and os.path.exists(knowledge_path):
            shutil.rmtree(knowledge_path)
        return jsonify({'success': False, 'message': f'创建知识库时发生错误: {str(e)}'}), 500


@local_knowledge_bp.route('/local_knowledge/edit', methods=['POST'])  # 改为POST方法
def edit_local_knowledge():
    """更新本地知识库信息"""
    try:
        data = request.get_json()
        kno_id = data.get('kno_id')
        kno_name = data.get('kno_name')
        kno_describe = data.get('kno_describe')
        knowledge_domain = data.get('knowledge_domain')  # 新增字段
        domain_description = data.get('domain_description')  # 新增字段
        required_background = data.get('required_background', [])  # 新增字段，默认为空列表
        required_skills = data.get('required_skills', [])  # 新增字段，默认为空列表

        if not kno_id:
            return jsonify({'success': False, 'message': '缺少必要参数 kno_id'}), 400

        # 构建更新数据字典
        update_data = {
            'kno_name': kno_name,
            'kno_describe': kno_describe,
            'knowledge_domain': knowledge_domain,
            'domain_description': domain_description,
            'required_background': required_background,
            'required_skills': required_skills
        }
        # 过滤掉None值
        update_data = {k: v for k, v in update_data.items() if v is not None}

        with LocalKnowledgeCrud() as crud:
            success = crud.local_knowledge_update(kno_id, **update_data)

        if success:
            return jsonify({'success': True, 'message': '知识库更新成功'})
        else:
            return jsonify({'success': False, 'message': '知识库更新失败'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'更新知识库时发生错误: {str(e)}'}), 500


@local_knowledge_bp.route('/local_knowledge/delete/<kno_id>', methods=['DELETE'])
def delete_local_knowledge(kno_id):
    """删除主要的本地知识库记录"""
    try:
        with LocalKnowledgeCrud() as crud:
            # 先删除关联的文件记录
            # 获取该知识库下的所有文件
            local_files = crud.get_local_knowledge_file_list(kno_id=kno_id)
            for file_record in local_files:
                # 删除本地文件
                file_path = Path(settings.KNOWLEDGE_LOCAL_PATH) / file_record[4]  # knol_path 是第5列 (索引4)
                if file_path.exists():
                    file_path.unlink()

                # 删除数据库记录
                crud.local_knowledge_list_delete(knol_id=file_record[1])  # knol_id 是第2列 (索引1)
            # 删除知识库绑定记录
            bindings = crud.get_local_knowledge_bind(kno_id=kno_id)
            for binding in bindings:
                # 删除绑定记录
                query = "DELETE FROM ai_knowledge_bind WHERE kno_id = %s AND knowledge_id = %s"
                params = (kno_id, binding[2])  # knowledge_id 是第3列 (索引2)
                crud.execute_query(query, params)

            kno_full_path = os.path.join(settings.KNOWLEDGE_LOCAL_PATH, crud.get_local_knowledge(kno_id=kno_id)[0][4])
            # 删除本地目录
            if os.path.exists(kno_full_path):
                shutil.rmtree(kno_full_path)
                logger.info(f"本地知识库目录已删除: {kno_full_path}")

            # 删除主要知识库记录
            success = crud.local_knowledge_delete(kno_id=kno_id)

            if success:
                return jsonify({'success': True, 'message': '知识库删除成功'})
            else:
                return jsonify({'success': False, 'message': '知识库删除失败'}), 500
    except Exception as e:
        logger.error(f"删除知识库时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'删除知识库时发生错误: {str(e)}'}), 500


