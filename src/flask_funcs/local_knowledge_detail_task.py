from flask import Blueprint, request, jsonify
from src.sql_funs import MetricTasksCRUD, LabelStudioCrud, QuestionsCRUD
import datetime
import logging
from src.zlpt_temp import cal_metric_by_chunk_id_fullmatch, ls_user
from concurrent.futures import ThreadPoolExecutor

# 创建线程池执行器
executor = ThreadPoolExecutor(max_workers=5)

logger = logging.getLogger(__name__)

# 创建蓝图 - 修改蓝图的URL前缀，使其与路由路径匹配
local_knowledge_detail_task_bp = Blueprint('task_bp', __name__)


def cal_metric(task_id, ls_user, project_id, knowledge_base_id, search_type, questions_list, file_name):
    try:
        cal_metric_by_chunk_id_fullmatch(ls_user, project_id, knowledge_base_id, search_type, questions_list, file_name)
        with MetricTasksCRUD() as mt_crud:
            success = mt_crud.metric_task_update(task_id, status='完成')
        if success:
            logging.info(f'计算任务 {task_id} 已完成')
        else:
            logging.error(f'更新任务 {task_id} 状态失败')
    except Exception as e:
        logging.error(f'执行计算任务 {task_id} 时发生错误: {str(e)}')
        with MetricTasksCRUD() as mt_crud:
            mt_crud.metric_task_update(task_id, status='失败')


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
            annotation_tasks = ls_crud.view_annotation_task_extended_list(local_knowledge_id=knowledge_id)
            # 构造返回数据
            result = []
            for task in annotation_tasks:
                task_id = task[0]
                # 查询对应的指标任务
                metric_task = mt_crud.metric_task_get_by_id(task_id)
                if metric_task:
                    metric_task_data = mt_crud._metric_task_to_json(metric_task)
                    combined_data = {
                        'task_id': task_id,
                        'task_name': task[1],
                        'annotation_type': task[12],
                        'status': metric_task_data['status'],
                        'search_type': metric_task_data['search_type']
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
            # 生成文件名
            time = datetime.datetime.now().strftime('%Y%m%d%H%M')
            file_name = f'{task_id}_{search_type}_{time}.json'
            # 更新任务记录中的报告路径
            success = mt_crud.metric_task_update(task_id=task_id, status='计算中', search_type=search_type,
                                                 report_path=file_name)
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
