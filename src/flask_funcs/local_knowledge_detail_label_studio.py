from flask import Blueprint, request, jsonify
import logging

from src.flask_funcs.common_utils import validate_required_fields, generate_unique_id
from src.sql_funs import LabelStudioCrud, Environment_Crud, LocalKnowledgeCrud, QuestionsCRUD, KnowledgeCrud, \
    KnowledgePathCrud, MetricTasksCRUD
from src.zlpt_temp import ls_create_project, ls_create_tasks, label_by_prediction, zlpt_login, \
    KnowledgeBase, ls_login
from concurrent.futures import ThreadPoolExecutor

# 导入LLM标注功能
from src.llm.llm_interface import llm_annotation_interface

# 创建线程池执行器
executor = ThreadPoolExecutor(max_workers=5)
# 创建logger
logger = logging.getLogger(__name__)

# 创建蓝图
local_knowledge_label_studio_bp = Blueprint('local_knowledge_label_studio', __name__)


def _label_by_prediction(ls_user, project, task, question_json):
    res = label_by_prediction(ls_user, project, question_json)
    logger.info(f"预测任务结束返回: {res}")
    with LabelStudioCrud() as ls_crud, MetricTasksCRUD() as mt_crud:
        ls_crud.annotation_task_update(task_id=task['task_id'], annotated_chunks=len(res), task_status='已完成')
        mt_crud.metric_task_create(task['task_id'], '未开始')


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
        required_fields = ['name', 'knowledge_base_id', 'label_studio_id', 'question_set_id', 'knowledge_base_id']
        missing_field = validate_required_fields(data, required_fields)
        if missing_field:
            return jsonify({'success': False, 'message': f'缺少必要字段: {missing_field}'}), 400

        task_name = data['name']
        local_knowledge_id = data['local_knowledge_id']
        label_studio_env_id = data['label_studio_id']
        question_set_id = data['question_set_id']
        knowledge_base_id = data['knowledge_base_id']

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
                knowledge_base_id=knowledge_base_id,
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
    """获取标注任务列表"""
    try:
        data = request.get_json()
        kno_id = data.get('kno_id')

        # 获取标注任务列表逻辑（从数据库查询）

        with LabelStudioCrud() as ls_crud, LocalKnowledgeCrud() as lk_crud, QuestionsCRUD() as q_crud, Environment_Crud() as e_crud:
            tasks = ls_crud.annotation_task_list(local_knowledge_id=kno_id)

            # 转换为前端期望的格式
            projects = []
            for task in tasks:
                task_data = ls_crud._annotation_task_to_json(task)

                # 获取知识库和问题集的名称
                # 获取知识库名称
                knowledge_base_id = task_data.get('knowledge_base_id')
                kb_name = '未知知识库'
                if knowledge_base_id:
                    kb_result = e_crud.get_knowledge_base(knowledge_id=knowledge_base_id)
                    if kb_result and len(kb_result) > 0:
                        kb_name = kb_result[0][1]  # 知识库名称通常在第二个字段
                    else:
                        # 如果从ai_knowledge_base表找不到，尝试从ai_local_knowledge表获取
                        local_kb_result = lk_crud.get_local_knowledge(kno_id=knowledge_base_id)
                        if local_kb_result and len(local_kb_result) > 0:
                            kb_name = local_kb_result[0][2]  # 知识库名称字段

                # 获取问题集名称
                question_set_id = task_data.get('question_set_id')
                qs_name = '未知问题集'
                if question_set_id:
                    qs_result = q_crud.question_config_list(question_id=question_set_id)
                    if qs_result and len(qs_result) > 0:
                        qs_name = qs_result[0][1]  # 问题集名称通常在第二个字段

                projects.append({
                    'task_id': task_data.get('task_id'),
                    'name': task_data.get('task_name'),
                    'knowledge_base_id': knowledge_base_id,
                    'knowledge_base_name': kb_name,
                    'environment_id': task_data.get('label_studio_env_id'),
                    'question_set_id': question_set_id,
                    'question_set_name': qs_name,
                    'total_chunks': task_data.get('total_chunks'),
                    'annotated_chunks': task_data.get('annotated_chunks'),
                    'task_status': task_data.get('task_status')
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


@local_knowledge_label_studio_bp.route('/local_knowledge_detail/label_studio/sync_project', methods=['POST'])
def sync_annotation_project():
    """同步标注任务 - 从数据库获取任务信息"""
    try:
        data = request.get_json()
        required_fields = ['task_id']
        missing_field = validate_required_fields(data, required_fields)
        if missing_field:
            return jsonify({'success': False, 'message': f'缺少必要字段: {missing_field}'}), 400
        task_id = data['task_id']

        # 从ai_annotation_tasks表查询任务信息
        with LabelStudioCrud() as ls_crud, QuestionsCRUD() as q_crud, KnowledgeCrud() as k_crud, KnowledgePathCrud() as kp_crud:
            # 查询指定任务ID的信息
            tasks = ls_crud.annotation_task_list(task_id=task_id)
            if not tasks:
                return jsonify({'success': False, 'message': '未找到指定的标注任务'}), 404
            # 获取第一个匹配的任务
            task = tasks[0]
            task_data = ls_crud._annotation_task_to_json(task)
            # 提取需要的字段
            task_name = task_data['task_name']
            local_knowledge_id = task_data.get('local_knowledge_id')
            question_set_id = task_data.get('question_set_id')
            label_studio_env_id = task_data.get('label_studio_env_id')
            label_studio_project_id = task_data.get('label_studio_project_id')
            knowledge_base_id = task_data.get('knowledge_base_id')

            ls_user = ls_login(None, None, label_studio_env_id, ls_crud)
            if not ls_user:
                return jsonify({'success': False, 'message': 'label studio环境信息查询失败'}), 500
            # 如果没project_id则创建project
            if not label_studio_project_id:
                question_json = q_crud.generate_question_json_by_qs_set_id(question_set_id)
                project = ls_create_project(ls_user, f'{task_name}_{task_id}', question_json)
                label_studio_project_id = project.id
                ls_crud.annotation_task_update(task_id, label_studio_project_id=label_studio_project_id)
            else:
                project = ls_user.get_project(label_studio_project_id)
            # 获取紫鸾平台知识库中的切片
            # 获取kno_path_id
            kno_path_id = kp_crud.get_knowledge_path_list(knowledge_id=knowledge_base_id)
            if kno_path_id:
                kno_path_id = kno_path_id[0][0]
            # 获取目录下的doc_id
            doc_ids = k_crud.knowledge_list(kno_path_id=kno_path_id)
            if doc_ids:
                doc_ids = [doc_id[0] for doc_id in doc_ids]
            # 根据doc_id和knowledge_base_id获取切片,并上传到label-studio
            zlpt_user = zlpt_login(None, None, knowledge_base_id)
            know_client = KnowledgeBase(zlpt_user)
            task_ids, total_chunks = ls_create_tasks(know_client, project, doc_ids)
            # 将对应task_id设置为已同步
            result = ls_crud.annotation_task_update(task_id, task_status='已同步', total_chunks=total_chunks)
        if not result:
            return jsonify({'success': False, 'message': '任务信息更新失败'}), 500
        return jsonify({
            'success': True,
            'message': '任务信息获取成功',
            'data': {
                'task_id': task_id,
                'local_knowledge_id': local_knowledge_id,
                'question_set_id': question_set_id,
                'label_studio_env_id': label_studio_env_id,
                'label_studio_project_id': label_studio_project_id,
                'total_chunks': total_chunks
            }
        })
    except Exception as e:
        logger.error(f"同步标注任务时发生错误: {str(e)}")
        raise e
        return jsonify({'success': False, 'message': f'同步标注任务时发生错误: {str(e)}'}), 500


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
        with LabelStudioCrud() as ls_crud:
            tasks = ls_crud.view_annotation_task_extended_list(label_studio_env_id=env_id, local_knowledge_id=kno_id)
            # 转换为前端期望的格式
            projects = []
            for task in tasks:
                projects.append(ls_crud._view_annotation_task_extended_list_to_json(task))
        return jsonify({
            'success': True,
            'data': projects
        })
    except Exception as e:
        logger.error(f"获取环境标注任务列表时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'获取环境标注任务列表时发生错误: {str(e)}'}), 500


@local_knowledge_label_studio_bp.route('/local_knowledge_detail/label_studio/update_annotation', methods=['POST'])
def update_annotation():
    """
    更新标注方式
    """
    try:
        data = request.get_json()
        task_id = data.get('task_id')
        annotation_type = data.get('annotation_type')

        if not task_id or not annotation_type:
            return jsonify({"success": False, "message": "缺少必要参数"}), 400
        with LabelStudioCrud() as ls_crud, QuestionsCRUD() as q_crud:
            # 检查任务是否存在
            task = ls_crud.annotation_task_get_by_id(task_id)
            if not task:
                return jsonify({"success": False, "message": "任务不存在"}), 400
            success = ls_crud.annotation_task_update(task_id=task_id, annotation_type=annotation_type,
                                                     task_status="标注中")
            if annotation_type in ['mlb', 'llm']:
                label_studio_env_id = task['label_studio_env_id']
                ls_user = ls_login(None, None, label_studio_env_id, ls_crud)
                if not ls_user:
                    return jsonify({'success': False, 'message': 'label studio环境信息查询失败'}), 500
                label_studio_project_id = ls_crud.annotation_task_get_by_id(task_id)['label_studio_project_id']
                project = ls_user.get_project(label_studio_project_id)

                question_json = q_crud.generate_question_json_by_qs_set_id(question_set_id=task['question_set_id'])
                if annotation_type == 'mlb':
                    executor.submit(_label_by_prediction, ls_user, project, task, question_json)
                elif annotation_type == 'llm':
                    # 使用LLM进行自动标注
                    # 查询domain信息
                    logger.info(f"查询标注任务扩展列表，task_id: {task_id}")
                    task_extended_list = ls_crud.view_annotation_task_extended_list(task_id=task_id)
                    logger.info(f"获取到的扩展任务列表: {task_extended_list}")
                    if task_extended_list and len(task_extended_list) > 0:
                        local_knowledge_id = task_extended_list[0][2]
                        logger.info(f"提取的local_knowledge_id: {local_knowledge_id}")
                    else:
                        logger.error(f"未找到任务扩展信息，task_id: {task_id}")
                        return jsonify({"success": False, "message": "未找到任务扩展信息"}), 400
                    executor.submit(_llm_annotation_process,  project, task, question_json, local_knowledge_id)
            else:
                # 使用手动方式标注，直接返回
                pass
        if success:
            return jsonify({"success": True, "message": "更新标注方式成功"})
        else:
            return jsonify({"success": False, "message": "更新标注方式失败"}), 500
    except Exception as e:
        logger.error(f"更新标注方式时发生错误: {str(e)}")
        return jsonify({"success": False, "message": f"更新标注方式时发生错误: {str(e)}"}), 500


def _llm_annotation_process( project, task, question_json, local_knowledge_id):
    """
    LLM标注处理函数
    """
    try:
        logger.info(f"开始LLM标注任务: {task['task_id']}")
        # 获取领域配置
        with LocalKnowledgeCrud() as lk_crud:
            kno_info = lk_crud.get_local_knowledge(kno_id=local_knowledge_id)[0]
            domain_config = {
                "knowledge_domain": kno_info[8],
                "domain_description": kno_info[9],
                "required_background": kno_info[10],
                "required_skills": kno_info[11]
            }
        
        # 获取项目中的所有任务
        ls_tasks = project.get_tasks()
        ls_tasks = ls_tasks[:10]
        # 遍历项目中的每个任务，对每个任务执行LLM标注
        annotated_count = 0
        for ls_task in ls_tasks:
            # 处理任务ID - ls_task可能是一个对象或字典
            if hasattr(ls_task, 'id'):
                task_id = ls_task.id
            else:
                task_id = ls_task.get('id')
            
            # 处理任务数据 - ls_task可能是一个对象或字典
            if hasattr(ls_task, 'data'):
                text_data = getattr(ls_task, 'data', {}).get('text', '')
            else:
                text_data = ls_task.get('data', {}).get('text', '')
            
            logger.info(f"正在处理任务 {task_id}，文本长度: {len(text_data)}")
            
            result = llm_annotation_interface.annotate_single_slice(
                domain_config=domain_config,
                questions_config=question_json,
                slice_text=text_data
            )
            
            logger.info(f"LLM返回结果: {result}")
            
            if result != "无匹配" and isinstance(result, dict):
                logger.info(f"处理LLM结果: {result}")
                # 根据LLM返回的结果创建标注
                annotations = []
                
                # 遍历LLM返回的结果，创建标注对象
                for question_type, selected_indices in result.items():
                    logger.info(f"处理问题类型: {question_type}, 选中索引: {selected_indices}")
                    if isinstance(selected_indices, list):
                        # 从question_json的datas中获取该类型问题的完整列表
                        # question_json结构为{"doc_name": "...", "datas": [{"type": "...", "questions": [...]}]}
                        question_type_data = next((item for item in question_json.get('datas', []) if item['type'] == question_type), None)
                        logger.info(f"找到问题类型数据: {question_type_data}")
                        if question_type_data and 'questions' in question_type_data:
                            selected_questions = []
                            for idx in selected_indices:
                                logger.info(f"处理索引: {idx}, 问题总数: {len(question_type_data['questions'])}")
                                if isinstance(idx, int) and idx < len(question_type_data['questions']):
                                    selected_questions.append(question_type_data['questions'][idx])
                                else:
                                    logger.warning(f"无效的索引或超出范围: {idx}")
                            
                            # 创建标注结果
                            if selected_questions:
                                annotation_result = {
                                    "value": {
                                        "choices": selected_questions
                                    },
                                    "id": f"llm_{question_type}_{task_id}",
                                    "from_name": question_type,
                                    "to_name": "text",
                                    "type": "choices",
                                    "origin": "prediction"
                                }
                                annotations.append(annotation_result)
                                logger.info(f"创建标注结果: {annotation_result}")
                
                # 如果有标注结果，则在Label Studio中创建预测
                if annotations:
                    logger.info(f"准备创建预测，预测数量: {len(annotations)}")
                    # 直接使用project对象创建预测
                    try:
                        # 创建预测
                        prediction_result = project.create_prediction(
                            task_id=task_id,
                            result=annotations,
                            # score表示模型置信度，可选参数
                            model_version="LLM_Auto_Annotator_v1"
                        )
                        
                        if prediction_result:
                            logger.info(f"为任务 {task_id} 成功创建了LLM预测，预测ID: {prediction_result.get('id')}")
                            annotated_count += 1
                        else:
                            logger.error(f"为任务 {task_id} 创建LLM预测失败")
                    except Exception as e:
                        logger.error(f"为任务 {task_id} 创建LLM预测时发生异常: {str(e)}")
                else:
                    logger.info(f"任务 {task_id} 没有有效预测结果")
            else:
                logger.info(f"跳过任务 {task_id}，LLM结果无效: {result}")

        # 更新任务状态为已完成
        with LabelStudioCrud() as ls_crud:
            ls_crud.annotation_task_update(task_id=task['task_id'], annotated_chunks=annotated_count, task_status='已完成')

        logger.info(f"LLM标注任务完成: {task['task_id']}，共标注了 {annotated_count} 个任务")
    except Exception as e:
        logger.error(f"LLM标注过程发生错误: {str(e)}")
        # 更新任务状态为错误
        with LabelStudioCrud() as ls_crud:
            ls_crud.annotation_task_update(task_id=task['task_id'], task_status='标注错误')
