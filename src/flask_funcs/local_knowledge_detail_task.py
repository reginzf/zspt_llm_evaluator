from flask import Blueprint, request, jsonify
from src.sql_funs import MetricTasksCRUD, LabelStudioCrud, QuestionsCRUD

import logging
from src.zlpt_temp import cal_metric_by_chunk_id_fullmatch, ls_user

logger = logging.getLogger(__name__)

# 创建蓝图 - 修改蓝图的URL前缀，使其与路由路径匹配
local_knowledge_detail_task_bp = Blueprint('task_bp', __name__)


def cal_metric(task_id, ls_user, project_id, knowledge_base_id, search_type, questions_list):
    cal_metric_by_chunk_id_fullmatch(ls_user, project_id, knowledge_base_id, search_type, questions_list)
    with MetricTasksCRUD() as mt_crud:
        success = mt_crud.metric_task_update(task_id, status='完成')
    if success:
        return jsonify({'success': True, 'message': '计算完成'})
    else:
        return jsonify({'success': False, 'message': '计算失败'})

@local_knowledge_detail_task_bp.route('/local_knowledge_detail/task/metric/list', methods=['GET'])
def get_metric_task_list():
    """
    获取指标任务列表
    """
    try:
        knowledge_id = request.args.get('knowledge_id')
        if not knowledge_id:
            return jsonify({"success": False, "message": "缺少knowledge_id参数"}), 400

        with MetricTasksCRUD() as mt_crud:
            # 查询指标任务表中与知识库相关的任务
            # 由于annotation_metric_tasks_crud.py已被删除，我们需要使用其他方式关联查询
            # 先获取标注任务信息
            from src.sql_funs.label_studio_crud import LabelStudioCrud
            with LabelStudioCrud() as ls_crud:
                annotation_tasks = ls_crud.annotation_task_list(local_knowledge_id=knowledge_id)

                # 构造返回数据
                result = []
                for task in annotation_tasks:
                    task_data = ls_crud._annotation_task_to_json(task)

                    # 查询对应的指标任务
                    metric_task = mt_crud.metric_task_get_by_id(task_data['task_id'])
                    if metric_task:
                        metric_task_data = mt_crud._metric_task_to_json(metric_task)

                        # 合并数据
                        combined_data = {
                            'task_id': task_data['task_id'],
                            'task_name': task_data['task_name'],
                            'annotation_type': metric_task_data.get('annotation_type'),
                            'status': metric_task_data.get('status', task_data.get('task_status', '初始化')),
                            'search_type': metric_task_data.get('search_type'),
                            'report_path': metric_task_data.get('report_path')
                        }
                    else:
                        # 如果没有对应的指标任务，则使用标注任务数据
                        combined_data = {
                            'task_id': task_data['task_id'],
                            'task_name': task_data['task_name'],
                            'annotation_type': task_data.get('annotation_type'),
                            'status': task_data.get('task_status', '初始化'),
                            'search_type': None,
                            'report_path': None
                        }

                    result.append(combined_data)

        return jsonify({"success": True, "data": result})
    except Exception as e:
        logger.error(f"获取指标任务列表时发生错误: {str(e)}")
        return jsonify({"success": False, "message": f"获取指标任务列表时发生错误: {str(e)}"}), 500


@local_knowledge_detail_task_bp.route('/local_knowledge_detail/task/metric/update_annotation', methods=['POST'])
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

        with MetricTasksCRUD() as mt_crud:
            if not mt_crud.metric_task_exists(task_id):
                success = mt_crud.metric_task_create(task_id=task_id, annotation_type=annotation_type, status='标注中')
            else:
                success = mt_crud.metric_task_update(task_id=task_id, annotation_type=annotation_type, status='标注中')
        if success:
            return jsonify({"success": True, "message": "更新标注方式成功"})
        else:
            return jsonify({"success": False, "message": "更新标注方式失败"}), 500

    except Exception as e:
        logger.error(f"更新标注方式时发生错误: {str(e)}")
        return jsonify({"success": False, "message": f"更新标注方式时发生错误: {str(e)}"}), 500


@local_knowledge_detail_task_bp.route('/local_knowledge_detail/task/metric/start_calculation', methods=['POST'])
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
        # 获取必要的参数
        with MetricTasksCRUD() as mt_crud, LabelStudioCrud() as ls_crud, QuestionsCRUD() as q_crud:
            # 获取任务的信息
            annotation_task = mt_crud.get_annotation_metric_tasks(task_id)
            if annotation_task:
                annotation_task_dict = mt_crud.view_annotation_metric_task_to_json(annotation_task[0])
            else:
                return jsonify({"success": False, "message": "未找到对应的标注任务"}), 404
            project_id = annotation_task_dict['label_studio_project_id']
            knowledge_base_id = annotation_task_dict['knowledge_base_id']
            question_set_id = annotation_task_dict['question_set_id']
            # 获取问题
            qs_set_config = q_crud.question_config_list(question_id=question_set_id)
            if qs_set_config:
                qs_set_type = qs_set_config[0][5]
            questions = q_crud.get_questions_by_type(qs_set_type, question_set_id=question_set_id)
            if questions:
                questions_list = [q_crud._question_to_json(q) for q in questions]
            # 更新任务状态为"计算中"并设置search_type
            success = mt_crud.metric_task_update(task_id=task_id, status='计算中', search_type=search_type)

        if success:
            # 这里可以启动后台异步计算任务
            cal_metric_by_chunk_id_fullmatch(ls_user, project_id, knowledge_base_id, search_type, questions_list)

            return jsonify({"success": True, "message": "质量计算已启动"})
        else:
            return jsonify({"success": False, "message": "启动计算失败"}), 500
    except Exception as e:
        logger.error(f"启动质量计算时发生错误: {str(e)}")
        return jsonify({"success": False, "message": f"启动质量计算时发生错误: {str(e)}"}), 500


@local_knowledge_detail_task_bp.route('/local_knowledge_detail/task/metric/get_report', methods=['GET'])
def get_report():
    """
    获取报告内容
    """
    try:
        task_id = request.args.get('task_id')
        if not task_id:
            return jsonify({"success": False, "message": "缺少task_id参数"}), 400

        # 获取指标任务信息
        with MetricTasksCRUD() as mt_crud:
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
