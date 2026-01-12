from flask import Blueprint, request, jsonify
import logging

from src.flask_funcs.common_utils import validate_required_fields, generate_unique_id
from src.sql_funs import LabelStudioCrud, Environment_Crud, LocalKnowledgeCrud, QuestionsCRUD

# 创建logger
logger = logging.getLogger(__name__)

# 创建蓝图
local_knowledge_label_studio_bp = Blueprint('local_knowledge_label_studio', __name__)


@local_knowledge_label_studio_bp.route('/local_knowledge_detail/label_studio/get_environments', methods=['POST'])
def get_label_studio_environments():
    """获取可用Label-Studio环境列表 """
    try:
        # 从请求体获取JSON数据
        data = request.get_json()
        kno_id = data.get('kno_id')

        with LabelStudioCrud() as ls_crud:
            # 获取所有Label-Studio环境
            environments = ls_crud.label_studio_list()
            environment_list = [ls_crud._label_studio_to_json(env) for env in environments]
            logger.info(f"获取环境列表: {environment_list}")
            # 检查当前知识库是否已绑定环境
            bound_environments = None
            res = ls_crud.label_studio_bind_get(kno_id)
            if res:
                bound_environments = [ls_crud._label_studio_bind_to_json(ele) for ele in res]
            logger.info(f"获取已绑定环境列表: {bound_environments}")
            # 为每个环境计算任务数量
            for env in environment_list:
                env['task_count'] = ls_crud.annotation_task_count_by_env(env['label_studio_id'])
            return jsonify({
                'success': True,
                'data': {
                    'environments': environment_list,
                    'bound_environments': bound_environments  # 如果有绑定则返回绑定的环境信息
                }
            })
    except Exception as e:
        logger.error(f"获取Label-Studio环境列表时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'获取环境列表时发生错误: {str(e)}'}), 500


@local_knowledge_label_studio_bp.route('/local_knowledge_detail/label_studio/bind_environment', methods=['POST'])
def bind_label_studio_environment():
    """绑定知识库与Label-Studio环境"""
    try:
        data = request.get_json()
        required_fields = ['kno_id', 'ls_id']
        missing_field = validate_required_fields(data, required_fields)
        if missing_field:
            return jsonify({'success': False, 'message': f'缺少必要字段: {missing_field}'}), 400

        kno_id = data['kno_id']
        ls_id = data['ls_id']

        with LabelStudioCrud() as ls_crud:
            result = ls_crud.label_studio_bind_create(kno_id=kno_id, label_studio_id=ls_id, bind_status=2)
            if not result:
                return jsonify({'success': False, 'message': '环境绑定失败'}), 400

        return jsonify({
            'success': True,
            'message': '环境绑定成功'
        })
    except Exception as e:
        logger.error(f"绑定Label-Studio环境时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'绑定环境时发生错误: {str(e)}'}), 500


@local_knowledge_label_studio_bp.route('/local_knowledge_detail/label_studio/unbind_environment', methods=['POST'])
def unbind_label_studio_environment():
    """解绑知识库与Label-Studio环境"""
    try:
        data = request.get_json()
        required_fields = ['kno_id', 'ls_id']
        missing_field = validate_required_fields(data, required_fields)
        if missing_field:
            return jsonify({'success': False, 'message': f'缺少必要字段: {missing_field}'}), 400

        kno_id = data['kno_id']
        ls_id = data['ls_id']

        with LabelStudioCrud() as ls_crud:
            result = ls_crud.label_studio_bind_delete(kno_id=kno_id, label_studio_id=ls_id)
            if not result:
                return jsonify({'success': False, 'message': '环境解绑失败'}), 400

        return jsonify({
            'success': True,
            'message': '环境解绑成功'
        })
    except Exception as e:
        logger.error(f"解绑Label-Studio环境时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'解绑环境时发生错误: {str(e)}'}), 500


@local_knowledge_label_studio_bp.route('/local_knowledge_detail/label_studio/create_annotation_project',
                                       methods=['POST'])
def create_annotation_project():
    """创建标注任务"""
    try:
        data = request.get_json()
        required_fields = ['name', 'knowledge_base_id', 'label_studio_id', 'question_set_id']
        missing_field = validate_required_fields(data, required_fields)
        if missing_field:
            return jsonify({'success': False, 'message': f'缺少必要字段: {missing_field}'}), 400

        task_name = data['name']
        local_knowledge_id = data['knowledge_base_id']
        label_studio_env_id = data['label_studio_id']
        question_set_id = data['question_set_id']

        # 验证本地知识库ID是否一致，如果提供的话
        if 'local_knowledge_id' in data:
            provided_local_knowledge_id = data['local_knowledge_id']
            if provided_local_knowledge_id != local_knowledge_id:
                logger.warning(
                    f"参数不一致: local_knowledge_id={provided_local_knowledge_id}, knowledge_base_id={local_knowledge_id}")

        # 生成任务ID
        task_id = generate_unique_id('task', 8)

        # 创建标注任务记录
        with LabelStudioCrud() as ls_crud:
            result = ls_crud.annotation_task_create(
                task_id=task_id,
                task_name=task_name,
                local_knowledge_id=local_knowledge_id,
                question_set_id=question_set_id,
                label_studio_env_id=label_studio_env_id,
                total_chunks=0,
                annotated_chunks=0,
                task_status='未开始'
            )

        if result:
            return jsonify({
                'success': True,
                'message': '标注任务创建成功',
                'task_id': task_id
            })
        else:
            return jsonify({
                'success': False,
                'message': '标注任务创建失败'
            })
    except Exception as e:
        logger.error(f"创建标注任务时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'创建标注任务时发生错误: {str(e)}'}), 500


@local_knowledge_label_studio_bp.route('/local_knowledge_detail/label_studio/get_project', methods=['POST'])
def get_annotation_projects():
    """获取标注任务列表 (新版本，使用JSON格式)"""
    try:
        data = request.get_json()
        kno_id = data.get('kno_id')

        # 获取标注任务列表逻辑（从数据库查询）

        with LabelStudioCrud() as ls_crud, LocalKnowledgeCrud() as lk_crud, QuestionsCRUD() as q_crud:
            tasks = ls_crud.annotation_task_list(local_knowledge_id=kno_id)

            # 转换为前端期望的格式
            projects = []
            for task in tasks:
                task_data = ls_crud._annotation_task_to_json(task)

                # 获取知识库和问题集的名称
                # kb_name = get_knowledge_base_name(task_data['local_knowledge_id'])
                kb_name = lk_crud.get_local_knowledge(kno_id=task_data['local_knowledge_id'])[0][2]
                # qs_name = get_question_set_name(task_data['question_set_id'])
                qs_name = q_crud.question_config_list(question_id=task_data['question_set_id'])[0][1]
                projects.append({
                    'task_id': task_data['task_id'],
                    'name': task_data['task_name'],
                    'knowledge_base_id': task_data['local_knowledge_id'],
                    'knowledge_base_name': kb_name,
                    'environment_id': task_data['label_studio_env_id'],
                    'question_set_id': task_data['question_set_id'],
                    'question_set_name': qs_name,
                    'total_chunks': task_data['total_chunks'],
                    'annotated_chunks': task_data['annotated_chunks'],
                    'task_status': task_data['task_status']
                })

        return jsonify({
            'success': True,
            'data': projects
        })
    except Exception as e:
        logger.error(f"获取标注任务列表时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'获取任务列表时发生错误: {str(e)}'}), 500


@local_knowledge_label_studio_bp.route('/local_knowledge_detail/label_studio/update_project', methods=['PUT'])
def update_annotation_project():
    """更新标注任务信息"""
    try:
        data = request.get_json()
        required_fields = ['id', 'name']
        missing_field = validate_required_fields(data, required_fields)
        if missing_field:
            return jsonify({'success': False, 'message': f'缺少必要字段: {missing_field}'}), 400

        task_id = data['id']
        task_name = data['name']
        task_status = data.get('task_status', data.get('status'))
        annotated_chunks = data.get('annotated_chunks', data.get('annotated_count'))

        # 更新标注任务记录
        with LabelStudioCrud() as ls_crud:
            result = ls_crud.annotation_task_update(
                task_id=task_id,
                task_name=task_name,
                task_status=task_status,
                annotated_chunks=annotated_chunks
            )

        if result:
            return jsonify({
                'success': True,
                'message': '标注任务更新成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '标注任务更新失败'
            })
    except Exception as e:
        logger.error(f"更新标注任务时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'更新任务时发生错误: {str(e)}'}), 500


@local_knowledge_label_studio_bp.route('/local_knowledge_detail/label_studio/delete_project', methods=['DELETE'])
def delete_annotation_project():
    """删除标注任务"""
    try:
        data = request.get_json()
        required_fields = ['id']
        missing_field = validate_required_fields(data, required_fields)
        if missing_field:
            return jsonify({'success': False, 'message': f'缺少必要字段: {missing_field}'}), 400

        task_id = data['id']

        # 删除标注任务记录
        with LabelStudioCrud() as ls_crud:
            result = ls_crud.annotation_task_delete(task_id=task_id)

        if result:
            return jsonify({
                'success': True,
                'message': '标注任务删除成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '标注任务删除失败'
            })
    except Exception as e:
        logger.error(f"删除标注任务时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'删除任务时发生错误: {str(e)}'}), 500


@local_knowledge_label_studio_bp.route('/local_knowledge_detail/label_studio/knowledge/bound_list', methods=['POST'])
def get_bound_knowledge_list():
    """获取环境已绑定的知识库列表"""
    try:
        data = request.get_json()
        env_id = data.get('env_id')
        local_knowledge_id = data.get('local_knowledge_id')

        if not env_id:
            return jsonify({'success': False, 'message': '缺少env_id参数'}), 400

        if not local_knowledge_id:
            return jsonify({'success': False, 'message': '缺少local_knowledge_id参数'}), 400

        # 从绑定表查询已绑定的知识库
        with LocalKnowledgeCrud() as lk_crud, Environment_Crud() as e_crud:
            # 查询绑定关系
            result = lk_crud.get_local_knowledge_bind(kno_id=local_knowledge_id)
            if result:
                binds = [lk_crud._local_knowledge_bind_to_json(ele) for ele in result if ele[3] == 2]
            else:
                binds = []
            # 获取相关的知识库信息
            knowledge_list = []
            for bind in binds:
                bind_info = e_crud.get_knowledge_base(knowledge_id=bind['knowledge_id'])
                if bind_info:
                    knowledge_list.append({
                        'knowledge_id': bind_info[0][0],
                        'knowledge_name': bind_info[0][1],
                        'status': 2
                    })

        return jsonify({
            'success': True,
            'data': knowledge_list
        })
    except Exception as e:
        logger.error(f"获取绑定知识库列表时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'获取绑定知识库列表时发生错误: {str(e)}'}), 500


@local_knowledge_label_studio_bp.route('/local_knowledge_detail/label_studio/questionset/available', methods=['POST'])
def get_available_questionsets():
    """获取可用的问题集列表"""
    try:
        data = request.get_json()
        knowledge_id = data.get('knowledge_id')

        if not knowledge_id:
            return jsonify({'success': False, 'message': '缺少knowledge_id参数'}), 400

        # 从问题集表查询对应知识库的问题集
        from src.sql_funs import QuestionsCRUD
        with QuestionsCRUD() as crud:
            result = crud.question_config_list(knowledge_id=knowledge_id)

            if result:
                question_sets = []
                for qs in result:
                    question_sets.append({
                        'question_id': qs[0],
                        'question_name': qs[1],
                        'question_set_type': qs[5],
                        'question_count': qs[6]
                    })
        return jsonify({
            'success': True,
            'data': question_sets
        })
    except Exception as e:
        logger.error(f"获取可用问题集列表时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'获取可用问题集列表时发生错误: {str(e)}'}), 500


@local_knowledge_label_studio_bp.route('/local_knowledge_detail/label_studio/get_tasks_by_environment',
                                       methods=['POST'])
def get_tasks_by_environment():
    """获取特定环境下的标注任务列表"""
    try:
        data = request.get_json()
        env_id = data.get('env_id')
        kno_id = data.get('kno_id')

        if not env_id or not kno_id:
            return jsonify({'success': False, 'message': '缺少必要参数'}), 400

        # 查询特定环境和知识库下的标注任务
        with LabelStudioCrud() as ls_crud, LocalKnowledgeCrud() as lk_crud, QuestionsCRUD() as q_crud:
            tasks = ls_crud.annotation_task_list(local_knowledge_id=kno_id, label_studio_env_id=env_id)

            # 转换为前端期望的格式
            projects = []
            for task in tasks:
                task_data = ls_crud._annotation_task_to_json(task)

                # 获取知识库和问题集的名称
                # kb_name = get_knowledge_base_name(task_data['local_knowledge_id'])
                kb_name = lk_crud.get_local_knowledge(kno_id=task_data['local_knowledge_id'])[0][2]
                # qs_name = get_question_set_name(task_data['question_set_id'])
                qs_name = q_crud.question_config_list(question_id=task_data['question_set_id'])[0][1]
                projects.append({
                    'task_id': task_data['task_id'],
                    'name': task_data['task_name'],
                    'knowledge_base_id': task_data['local_knowledge_id'],
                    'knowledge_base_name': kb_name,
                    'environment_id': task_data['label_studio_env_id'],
                    'question_set_id': task_data['question_set_id'],
                    'question_set_name': qs_name,
                    'total_chunks': task_data['total_chunks'],
                    'annotated_chunks': task_data['annotated_chunks'],
                    'task_status': task_data['task_status']
                })

        return jsonify({
            'success': True,
            'data': projects
        })
    except Exception as e:
        logger.error(f"获取环境标注任务列表时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'获取环境标注任务列表时发生错误: {str(e)}'}), 500
