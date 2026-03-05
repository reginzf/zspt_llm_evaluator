from flask import Blueprint, request, jsonify
from src.sql_funs import LabelStudioCrud, QuestionsCRUD
import logging
from src.flask_funcs.reports.flask_annotation_tasks_renderer import render_annotation_tasks_page
from env_config_init import settings

logger = logging.getLogger(__name__)

# 创建蓝图
annotation_tasks_bp = Blueprint('annotation_tasks_bp', __name__)


@annotation_tasks_bp.route('/annotation_tasks', methods=['GET'])
def annotation_tasks_page():
    """
    标注任务管理页面
    """
    try:
        return render_annotation_tasks_page()
    except Exception as e:
        logger.error(f"访问标注任务管理页面时发生错误：{str(e)}")
        return f"<h1>页面加载错误：{str(e)}</h1>", 500


@annotation_tasks_bp.route('/api/annotation/tasks/list', methods=['GET'])
def get_annotation_task_list():
    """
    获取标注任务列表（支持分页、搜索、筛选）
    """
    try:
        # 获取查询参数
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        keyword = request.args.get('keyword', '')
        task_status = request.args.get('task_status', '')
        annotation_type = request.args.get('annotation_type', '')
        
        # 计算偏移量
        offset = (page - 1) * limit
        
        with LabelStudioCrud() as ls_crud:
            # 使用扩展视图查询，包含知识库名称和问题集名称
            tasks = ls_crud.view_annotation_task_extended_list(
                task_id=None,
                label_studio_env_id=None,
                local_knowledge_id=None
            )
            
            # 过滤数据
            filtered_tasks = []
            for task in tasks:
                task_dict = ls_crud._view_annotation_task_extended_list_to_json(task)
                
                # 应用筛选条件
                if keyword and keyword.lower() not in task_dict.get('task_name', '').lower():
                    continue
                if task_status and task_dict.get('task_status') != task_status:
                    continue
                if annotation_type and task_dict.get('annotation_type') != annotation_type:
                    continue
                
                filtered_tasks.append(task_dict)
            
            # 分页
            total = len(filtered_tasks)
            start_idx = offset
            end_idx = offset + limit
            paginated_tasks = filtered_tasks[start_idx:end_idx]
            
            return jsonify({
                "success": True,
                "data": {
                    "rows": paginated_tasks,
                    "total": total,
                    "page": page,
                    "limit": limit
                }
            })
            
    except Exception as e:
        logger.error(f"获取标注任务列表时发生错误：{str(e)}")
        return jsonify({
            "success": False,
            "message": f"获取任务列表时发生错误：{str(e)}"
        }), 500


@annotation_tasks_bp.route('/api/annotation/tasks/create', methods=['POST'])
def create_annotation_task():
    """
    创建标注任务
    """
    try:
        data = request.get_json()
        
        # 获取必要参数
        task_name = data.get('task_name')
        local_knowledge_id = data.get('local_knowledge_id')
        question_set_id = data.get('question_set_id')
        label_studio_env_id = data.get('label_studio_env_id')
        annotation_type = data.get('annotation_type', '')
        
        # 验证必填字段
        if not task_name or not local_knowledge_id or not question_set_id or not label_studio_env_id:
            return jsonify({
                "success": False,
                "message": "缺少必要参数"
            }), 400
        
        # 生成任务 ID
        import uuid
        task_id = str(uuid.uuid4())[:8]
        
        with LabelStudioCrud() as ls_crud:
            # 创建标注任务
            success = ls_crud.annotation_task_create(
                task_id=task_id,
                task_name=task_name,
                local_knowledge_id=local_knowledge_id,
                question_set_id=question_set_id,
                label_studio_env_id=label_studio_env_id,
                annotation_type=annotation_type,
                task_status='未开始'
            )
            
            if success:
                return jsonify({
                    "success": True,
                    "message": "任务创建成功",
                    "data": {"task_id": task_id}
                })
            else:
                return jsonify({
                    "success": False,
                    "message": "任务创建失败"
                }), 500
            
    except Exception as e:
        logger.error(f"创建标注任务时发生错误：{str(e)}")
        return jsonify({
            "success": False,
            "message": f"创建任务时发生错误：{str(e)}"
        }), 500


@annotation_tasks_bp.route('/api/annotation/tasks/update', methods=['PUT'])
def update_annotation_task():
    """
    更新标注任务
    """
    try:
        data = request.get_json()
        
        # 获取参数
        task_id = data.get('task_id')
        task_name = data.get('task_name')
        task_status = data.get('task_status')
        annotation_type = data.get('annotation_type')
        
        # 验证必填字段
        if not task_id:
            return jsonify({
                "success": False,
                "message": "缺少任务 ID"
            }), 400
        
        with LabelStudioCrud() as ls_crud:
            # 更新标注任务
            success = ls_crud.annotation_task_update(
                task_id=task_id,
                task_name=task_name,
                task_status=task_status,
                annotation_type=annotation_type
            )
            
            if success:
                return jsonify({
                    "success": True,
                    "message": "任务更新成功"
                })
            else:
                return jsonify({
                    "success": False,
                    "message": "任务更新失败"
                }), 500
            
    except Exception as e:
        logger.error(f"更新标注任务时发生错误：{str(e)}")
        return jsonify({
            "success": False,
            "message": f"更新任务时发生错误：{str(e)}"
        }), 500


@annotation_tasks_bp.route('/api/annotation/tasks/delete', methods=['DELETE'])
def delete_annotation_task():
    """
    删除标注任务
    """
    try:
        data = request.get_json()
        task_id = data.get('task_id')
        
        if not task_id:
            return jsonify({
                "success": False,
                "message": "缺少任务 ID"
            }), 400
        
        with LabelStudioCrud() as ls_crud:
            # 删除标注任务
            success = ls_crud.annotation_task_delete(task_id=task_id)
            
            if success:
                return jsonify({
                    "success": True,
                    "message": "任务删除成功"
                })
            else:
                return jsonify({
                    "success": False,
                    "message": "任务删除失败"
                }), 500
            
    except Exception as e:
        logger.error(f"删除标注任务时发生错误：{str(e)}")
        return jsonify({
            "success": False,
            "message": f"删除任务时发生错误：{str(e)}"
        }), 500


@annotation_tasks_bp.route('/api/local_knowledge/list', methods=['GET'])
def get_local_knowledge_list():
    """
    获取本地知识库列表
    """
    try:
        from src.sql_funs import LocalKnowledgeCrud
        
        with LocalKnowledgeCrud() as lk_crud:
            # 获取数据库中的本地知识列表
            knowledge_list = lk_crud.get_local_knowledge()
            
            result = []
            for kb in knowledge_list:
                result.append({
                    'knowledge_id': kb[1],  # kno_id
                    'knowledge_name': kb[2],  # kno_name
                    'kno_describe': kb[3] if len(kb) > 2 else '',
                    'kno_path': kb[4] if len(kb) > 3 else ''
                })
            
            return jsonify({
                "success": True,
                "data": result
            })
    except Exception as e:
        logger.error(f"获取本地知识库列表时发生错误：{str(e)}")
        return jsonify({
            "success": False,
            "message": f"获取知识库列表时发生错误：{str(e)}"
        }), 500


@annotation_tasks_bp.route('/api/questions/list', methods=['GET'])
def get_questions_list():
    """
    获取问题集列表
    """
    try:
        knowledge_id = request.args.get('knowledge_id')
        
        if not knowledge_id:
            return jsonify({
                "success": False,
                "message": "缺少 knowledge_id 参数"
            }), 400
        
        with QuestionsCRUD() as q_crud:
            # 使用 question_config_list 方法获取问题集列表
            questions = q_crud.question_config_list(knowledge_id=knowledge_id)
            
            result = []
            for q in questions:
                result.append({
                    'question_id': q[0],
                    'question_name': q[1],
                    'knowledge_id': q[2]
                })
            
            return jsonify({
                "success": True,
                "data": result
            })
            
    except Exception as e:
        logger.error(f"获取问题集列表时发生错误：{str(e)}")
        return jsonify({
            "success": False,
            "message": f"获取问题集列表时发生错误：{str(e)}"
        }), 500


@annotation_tasks_bp.route('/api/label_studio/environments/list', methods=['GET'])
def get_label_studio_environments():
    """
    获取 Label Studio 环境列表
    """
    try:
        with LabelStudioCrud() as ls_crud:
            environments = ls_crud.label_studio_list()
            
            result = []
            for env in environments:
                result.append(ls_crud._label_studio_to_json(env))
            
            return jsonify({
                "success": True,
                "data": result
            })
            
    except Exception as e:
        logger.error(f"获取 Label Studio 环境列表时发生错误：{str(e)}")
        return jsonify({
            "success": False,
            "message": f"获取环境列表时发生错误：{str(e)}"
        }), 500
