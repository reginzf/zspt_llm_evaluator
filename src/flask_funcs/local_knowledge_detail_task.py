from flask import Blueprint, request, jsonify
from src.sql_funs import MetricTasksCRUD, LabelStudioCrud, QuestionsCRUD
import datetime
import logging
from src.zlpt_temp import cal_metric_by_chunk_id_fullmatch, zlpt_login, Retrieve, ls_login
from concurrent.futures import ThreadPoolExecutor
from src.flask_funcs.common_utils import generate_unique_id
from src.zlpt_temp import cal_metric_by_chunk_text_overlay_and_similarity

# 创建线程池执行器
executor = ThreadPoolExecutor(max_workers=5)

logger = logging.getLogger(__name__)

# 创建蓝图 - 修改蓝图的URL前缀，使其与路由路径匹配
local_knowledge_detail_task_bp = Blueprint('task_bp', __name__)


def cal_metric(zlpt_user, task_id, ls_user, project_id, knowledge_base_id, search_type, match_type, questions_list,
               file_name):
    try:
        with MetricTasksCRUD() as mt_crud:
            retrieve_client = Retrieve(zlpt_user)
            report_id = generate_unique_id('rp', 8)
            mt_crud.report_create(report_id, search_type, file_name, task_id, '开始计算')

            # 根据匹配类型选择计算函数
        if match_type == 'chunkIdMatch':
            cal_metric_by_chunk_id_fullmatch(ls_user, project_id, knowledge_base_id, search_type, questions_list,
                                             file_name, retrieve_client=retrieve_client)
        elif match_type == 'chunkTextMatch':

            cal_metric_by_chunk_text_overlay_and_similarity(ls_user, project_id, knowledge_base_id, search_type,
                                                            questions_list,
                                                            file_name, retrieve_client=retrieve_client)
        else:
            raise ValueError(f"不支持的匹配类型: {match_type}")

        with MetricTasksCRUD() as mt_crud:
            # 更新任务状态为已完成
            mt_crud.metric_task_update(task_id, status="完成")
        return True
    except Exception as e:
        print(f"cal_metric error: {e}")
        with MetricTasksCRUD() as mt_crud:
            mt_crud.metric_task_update(task_id, status="失败")  # 设置为失败状态
        return False


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

        with MetricTasksCRUD() as mt_crud:
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
    try:
        data = request.get_json()
        task_id = data.get('task_id')
        search_type = data.get('search_type')
        match_type = data.get('match_type')  # 新增参数

        if not task_id or not search_type or not match_type:
            return jsonify({'success': False, 'message': '缺少必要参数'}), 400

        # 查询任务相关信息
        with LabelStudioCrud() as ls_crud:
            annotation_task_info = ls_crud.annotation_task_get_by_id(task_id=task_id)

        if not annotation_task_info:
            return jsonify({'success': False, 'message': '找不到指定的任务'}), 400

        knowledge_base_id = annotation_task_info['knowledge_base_id']
        # 从数据库获取project_id，如果没有则使用默认值
        project_id = annotation_task_info.get('label_studio_project_id')

        # 查询问题列表
        with QuestionsCRUD() as q_crud:
            questions_list = q_crud.questions_list(task_id=task_id)

        if not questions_list:
            return jsonify({'success': False, 'message': '没有找到相关问题'}), 400

        # 生成文件名
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        file_name = f'metric_{task_id}_{search_type}_{timestamp}.json'

        # 启动异步计算任务
        success = True
        if success:
            # 使用线程池异步执行计算任务
            ls_user = ls_login(None, None, annotation_task_info['label_studio_env_id'])
            zlpt_user = zlpt_login(None, None, knowledge_base_id)
            executor.submit(cal_metric, zlpt_user, task_id, ls_user, project_id, knowledge_base_id, search_type,
                            match_type, questions_list, file_name)

        return jsonify({'success': True, 'message': '计算任务已启动'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


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


@local_knowledge_detail_task_bp.route('/local_knowledge_detail/task/metric/completed_tasks', methods=['POST'])
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
