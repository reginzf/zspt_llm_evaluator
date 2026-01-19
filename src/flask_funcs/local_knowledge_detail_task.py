from flask import Blueprint, request, jsonify
from src.sql_funs import MetricTasksCRUD, LabelStudioCrud, QuestionsCRUD
import datetime
import logging
from src.zlpt_temp import cal_metric_by_chunk_id_fullmatch, ls_user
from concurrent.futures import ThreadPoolExecutor
from src.flask_funcs.common_utils import generate_unique_id

# 创建线程池执行器
executor = ThreadPoolExecutor(max_workers=5)

logger = logging.getLogger(__name__)

# 创建蓝图 - 修改蓝图的URL前缀，使其与路由路径匹配
local_knowledge_detail_task_bp = Blueprint('task_bp', __name__)


def cal_metric(task_id, ls_user, project_id, knowledge_base_id, search_type, questions_list, file_name):
    try:
        with MetricTasksCRUD() as mt_crud:
            report_id = generate_unique_id('rp', 8)
            success1 = mt_crud.report_create(report_id, search_type, file_name, task_id, '开始计算')
            cal_metric_by_chunk_id_fullmatch(ls_user, project_id, knowledge_base_id, search_type, questions_list,
                                             file_name)
            success2 = mt_crud.metric_task_update(task_id, status='完成')
            success1 = mt_crud.report_update(report_id, status='计算完成')
        if success1:
            logging.info(f'创建报告 {task_id} 成功')
        else:
            logging.error(f'创建报告 {task_id} 失败')
        if success2:
            logging.info(f'计算任务 {task_id} 已完成')
        else:
            logging.error(f'更新任务 {task_id} 状态失败')
    except Exception as e:
        logging.error(f'执行计算任务 {task_id} 时发生错误: {str(e)}')
        with MetricTasksCRUD() as mt_crud:
            mt_crud.metric_task_update(task_id, status='失败')
            mt_crud.report_update(report_id, status='计算失败', error_msg=str(e))


@local_knowledge_detail_task_bp.route('/local_knowledge_detail/task/metric/create', methods=['POST'])
def create_metric_task():
    """
    创建指标任务
    """
    try:
        data = request.get_json()
        task_id = data.get('task_id')
        annotation_type = data.get('annotation_type')  # 修改参数名为annotation_type，与前端一致
        if not task_id or not annotation_type:
            return jsonify({"success": False, "message": "缺少必要参数"}), 400
        with MetricTasksCRUD() as m_crud:
            success = m_crud.metric_task_create(task_id, status='未开始')  # 使用annotation_type参数
            if success:
                return jsonify({"success": True, "message": "创建任务成功"})
            else:
                return jsonify({"success": False, "message": "创建任务失败"}), 500
    except Exception as e:
        logger.error(f"创建指标任务时发生错误: {str(e)}")
        return jsonify({"success": False, "message": f"创建指标任务时发生错误: {str(e)}"}), 500


@local_knowledge_detail_task_bp.route('/local_knowledge_detail/task/metric/list', methods=['GET'])
def get_metric_task_list():
    """
    获取指标任务列表
    """
    try:
        knowledge_id = request.args.get('knowledge_id')
        if not knowledge_id:
            return jsonify({"success": False, "message": "缺少knowledge_id参数"}), 400

        with MetricTasksCRUD() as mt_crud, LabelStudioCrud() as ls_crud:
            metric_tasks = mt_crud.view_get_annotation_metric_tasks(local_knowledge_id=knowledge_id)
            result = []
            for task in metric_tasks:
                combined_data = {
                    'task_id': task[0],
                    'task_name': task[1],
                    'annotation_type': task[12],
                    'status': task[13]
                }
                result.append(combined_data)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        logger.error(f"获取指标任务列表时发生错误: {str(e)}")
        return jsonify({"success": False, "message": f"获取指标任务列表时发生错误: {str(e)}"}), 500


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
            annotation_task = mt_crud.view_get_annotation_metric_tasks(task_id)
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
            # 生成文件名
            time = datetime.datetime.now().strftime('%Y%m%d%H%M')
            file_name = f'{task_id}_{search_type}_{time}.json'
        if success:
            # 使用线程池异步执行计算任务
            executor.submit(cal_metric, task_id, ls_user, project_id, knowledge_base_id, search_type, questions_list,
                            file_name)
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

        with MetricTasksCRUD() as mt_crud:
            task_info = mt_crud.view_get_annotation_metric_tasks(task_id=task_id)
            if task_info:
                knowledge_base_id = task_info[0][5]
            report_list = mt_crud.report_list(task_id=task_id)
            if report_list:
                report_dict_list = [mt_crud._report_to_json(report) for report in report_list]
            else:
                report_dict_list = []
        return jsonify({
            "success": True,
            "data": report_dict_list,
            "knowledgeBaseId": knowledge_base_id
        })
    except Exception as e:
        logger.error(f"获取报告时发生错误: {str(e)}")
        return jsonify({"success": False, "message": f"获取报告时发生错误: {str(e)}"}), 500

@local_knowledge_detail_task_bp .route('/local_knowledge_detail/task/metric/completed_tasks', methods=['POST'])
def get_completed_annotation_tasks():
    """
    获取已完成的标注任务列表，用于创建指标任务
    """
    try:
        data = request.get_json()
        local_knowledge_id = data.get('local_knowledge_id')
        if not local_knowledge_id:
            return jsonify({"success": False, "message": "缺少local_knowledge_id参数"}), 400
        with LabelStudioCrud() as ls_crud:
            tasks = ls_crud.view_annotation_task_completed_list(local_knowledge_id=local_knowledge_id)
            task_list = []
            for task in tasks:
                task_list.append(ls_crud._view_annotation_task_completed_list_to_json(task))
        return jsonify({"success": True, "data": task_list})

    except Exception as e:
        logger.error(f"获取已完成的标注任务时发生错误: {str(e)}")
        return jsonify({"success": False, "message": f"获取已完成的标注任务时发生错误: {str(e)}"}), 500
