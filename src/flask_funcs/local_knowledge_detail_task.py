from flask import Blueprint, request, jsonify, render_template
from src.sql_funs.metric_tasks_crud import MetricTasksCRUD
from src.sql_funs.label_studio_crud import LabelStudioCrud
import logging

logger = logging.getLogger(__name__)

# 创建蓝图
task_bp = Blueprint('task_bp', __name__, url_prefix='/local_knowledge_detail/task')

# 创建CRUD实例
mt_crud = MetricTasksCRUD()
ls_crud = LabelStudioCrud()


@task_bp.route('/local_knowledge_detail/task/metric/list', methods=['GET'])
def get_metric_task_list():
    """
    获取指标任务列表
    """
    try:
        knowledge_id = request.args.get('knowledge_id')
        if not knowledge_id:
            return jsonify({"success": False, "message": "缺少knowledge_id参数"}), 400

        # 获取标注任务列表
        annotation_tasks = ls_crud.annotation_task_list(local_knowledge_id=knowledge_id)
        
        # 获取指标任务列表
        metric_tasks = mt_crud.metric_task_list()
        metric_tasks_dict = {task[0]: task for task in metric_tasks} if metric_tasks else {}

        # 合并数据
        result = []
        if annotation_tasks:
            for task in annotation_tasks:
                task_id = task[0]  # task_id是第一个字段
                metric_task = metric_tasks_dict.get(task_id)
                
                task_data = {
                    'task_id': task_id,
                    'task_name': task[1] if len(task) > 1 else None,
                    'annotation_type': None,
                    'status': '初始化',  # 默认状态
                    'search_type': None,
                    'report_path': None
                }
                
                # 如果存在对应的指标任务，则使用指标任务的状态
                if metric_task:
                    task_data['annotation_type'] = metric_task[1]
                    task_data['status'] = metric_task[2]
                    task_data['search_type'] = metric_task[3]
                    task_data['report_path'] = metric_task[4]
                
                result.append(task_data)

        return jsonify({"success": True, "data": result})
    except Exception as e:
        logger.error(f"获取指标任务列表时发生错误: {str(e)}")
        return jsonify({"success": False, "message": f"获取指标任务列表时发生错误: {str(e)}"}), 500


@task_bp.route('/local_knowledge_detail/task/metric/update_annotation', methods=['POST'])
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

        # 检查任务是否存在，如果不存在则创建
        if not mt_crud.metric_task_exists(task_id):
            success = mt_crud.metric_task_create(task_id=task_id, annotation_type=annotation_type, status='标注中')
        else:
            success = mt_crud.metric_task_update(task_id=task_id, annotation_type=annotation_type, status='标注中')

        if success:
            return jsonify({"success": True, "message": "标注方式更新成功"})
        else:
            return jsonify({"success": False, "message": "更新失败"}), 500
    except Exception as e:
        logger.error(f"更新标注方式时发生错误: {str(e)}")
        return jsonify({"success": False, "message": f"更新标注方式时发生错误: {str(e)}"}), 500


@task_bp.route('/local_knowledge_detail/task/metric/start_calculation', methods=['POST'])
def start_calculation():
    """
    启动质量计算
    """
    try:
        data = request.get_json()
        task_id = data.get('task_id')
        search_type = data.get('search_type')

        if not task_id or not search_type:
            return jsonify({"success": False, "message": "缺少必要参数"}), 400

        # 更新任务状态为"计算中"并设置search_type
        success = mt_crud.metric_task_update(task_id=task_id, status='计算中', search_type=search_type)

        if success:
            # 这里可以启动后台异步计算任务
            # TODO: 实现异步质量评估算法
            return jsonify({"success": True, "message": "质量计算已启动"})
        else:
            return jsonify({"success": False, "message": "启动计算失败"}), 500
    except Exception as e:
        logger.error(f"启动质量计算时发生错误: {str(e)}")
        return jsonify({"success": False, "message": f"启动质量计算时发生错误: {str(e)}"}), 500


@task_bp.route('/local_knowledge_detail/task/metric/get_report', methods=['GET'])
def get_report():
    """
    获取报告内容
    """
    try:
        task_id = request.args.get('task_id')
        if not task_id:
            return jsonify({"success": False, "message": "缺少task_id参数"}), 400

        # 获取指标任务信息
        metric_task = mt_crud.metric_task_get_by_id(task_id)
        if not metric_task:
            return jsonify({"success": False, "message": "指标任务不存在"}), 404

        # 检查任务状态是否为完成
        status = metric_task[2] if len(metric_task) > 2 else None
        if status != '完成':
            return jsonify({"success": False, "message": f"任务状态为{status}，无法查看报告"}), 400

        # 获取报告路径
        report_path = metric_task[4] if len(metric_task) > 4 else None
        if not report_path:
            return jsonify({"success": False, "message": "报告尚未生成"}), 404

        # 这里可以返回报告内容或报告路径
        # TODO: 实现具体的报告获取逻辑
        return jsonify({
            "success": True, 
            "data": {
                "report_path": report_path,
                "status": status
            }
        })
    except Exception as e:
        logger.error(f"获取报告时发生错误: {str(e)}")
        return jsonify({"success": False, "message": f"获取报告时发生错误: {str(e)}"}), 500