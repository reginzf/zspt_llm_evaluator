import jsonpath
from flask import Blueprint, request, jsonify
import logging
from src.sql_funs.environment_crud import Environment_Crud
from src.flask_funcs.common_utils import validate_required_fields
from src.zlpt_temp import zlpt_create_knowledge_base, zlpt_login
from src.zlpt.login import LoginManager
from src.zlpt.api.knowledge_base import KnowledgeBase

# 创建logger
logger = logging.getLogger(__name__)

# 创建蓝图
knowledge_base_bp = Blueprint('knowledge_base', __name__)


@knowledge_base_bp.route('/knowledge_base/list', methods=['GET'])
def knowledge_base_list():
    """获取知识库列表"""
    try:
        # 获取查询参数
        knowledge_id = request.args.get('knowledge_id')
        knowledge_name = request.args.get('knowledge_name')

        with Environment_Crud() as crud:
            knowledge_list = crud.get_knowledge_base(knowledge_id=knowledge_id, knowledge_name=knowledge_name)

        return jsonify({
            'success': True,
            'data': knowledge_list
        })
    except Exception as e:
        logger.error(f"获取知识库列表时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@knowledge_base_bp.route('/knowledge_base/create', methods=['POST'])
def knowledge_base_create():
    """创建知识库"""
    try:
        data = request.get_json()
        # 验证必要字段
        required_fields = ['knowledge_name', 'zlpt_base_id', "chunk_size", "chunk_overlap", "sliceidentifier"]
        missing_field = validate_required_fields(data, required_fields)
        if missing_field:
            return jsonify({'success': False, 'message': f'缺少必要字段: {missing_field}'}), 400

        knowledge_name = data['knowledge_name']
        chunk_size = data['chunk_size']
        chunk_overlap = data['chunk_overlap']
        zlpt_base_id = data['zlpt_base_id']
        with Environment_Crud() as crud:
            zlpt_user = zlpt_login(zlpt_base_id, crud)
            if not zlpt_user:
                return jsonify({'success': False, 'message': '知识库创建失败'}), 400
            know_client = KnowledgeBase(zlpt_user)
            zlpt_base_name, remote_kno_id = zlpt_create_knowledge_base(know_client, knowledge_name, chunk_size, chunk_overlap)
            
            # 检查远程 API 是否成功
            if not remote_kno_id:
                return jsonify({'success': False, 'message': '远程平台创建知识库失败，请检查环境配置和权限'}), 400
            
            kno_id = remote_kno_id
            data['knowledge_id'] = kno_id
            
            # 查询root_id (知识库内容的根目录)
            try:
                res = know_client.knowledge_content_tree(knowledgeId=kno_id)
                if res.get('code') == 200 and res.get('data'):
                    # 查找 plevel=0 的根节点
                    root_items = [item for item in res['data'] if item.get('plevel') == 0]
                    if root_items:
                        data["kno_root_id"] = root_items[0].get('contentCode', kno_id)
                    else:
                        data["kno_root_id"] = kno_id
                else:
                    # 如果查询失败，使用 knowledge_id 作为 root_id
                    data["kno_root_id"] = kno_id
            except Exception as e:
                logger.warning(f"查询知识库root_id失败: {e}，使用knowledge_id作为root_id")
                data["kno_root_id"] = kno_id

            logger.info(f'插入数据为：{data}')
            result = crud.knowledge_base_insert(**data)
            if result:
                return jsonify({
                    'success': True,
                    'message': '知识库创建成功',
                    'knowledge_id': kno_id
                })
            else:
                return jsonify({'success': False, 'message': '知识库创建失败'}), 400
    except Exception as e:
        logger.error(f"创建知识库时发生错误: {str(e)}")
        raise e


@knowledge_base_bp.route('/knowledge_base/update/<knowledge_id>', methods=['PUT'])
def knowledge_base_update(knowledge_id):
    """更新知识库"""
    try:
        data = request.get_json()

        with Environment_Crud() as crud:
            result = crud.knowledge_base_update(knowledge_id=knowledge_id, **data)

            if result:
                return jsonify({'success': True, 'message': '知识库更新成功'})
            else:
                return jsonify({'success': False, 'message': '知识库更新失败'}), 400
    except Exception as e:
        logger.error(f"更新知识库时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@knowledge_base_bp.route('/knowledge_base/delete/<knowledge_id>', methods=['DELETE'])
def knowledge_base_delete(knowledge_id):
    """删除知识库"""
    try:
        with Environment_Crud() as crud:
            result = crud.knowledge_base_delete(knowledge_id=knowledge_id)

            if result:
                return jsonify({'success': True, 'message': '知识库删除成功'})
            else:
                return jsonify({'success': False, 'message': '知识库删除失败'}), 400
    except Exception as e:
        logger.error(f"删除知识库时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
