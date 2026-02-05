from flask import Blueprint, request, jsonify
from src.sql_funs import MetricTasksCRUD, LabelStudioCrud, QuestionsCRUD
import datetime
import logging
from src.zlpt_temp import cal_metric_by_chunk_id_fullmatch, zlpt_login, Retrieve, ls_login
from concurrent.futures import ThreadPoolExecutor
from src.flask_funcs.common_utils import generate_unique_id
from src.zlpt_temp import cal_metric_by_chunk_text_overlay_and_similarity
from env_config_init import REPORT_PATH
from pathlib import Path

# 创建线程池执行器
executor = ThreadPoolExecutor(max_workers=5)

logger = logging.getLogger(__name__)

# 创建蓝图 - 修改蓝图的URL前缀，使其与路由路径匹配
local_knowledge_detail_task_bp = Blueprint('task_bp', __name__)


def cal_metric(zlpt_user, task_id, ls_user, project_id, knowledge_base_id, search_type, match_type, questions_list,
               file_name, metric_task_id):
    try:
        with MetricTasksCRUD() as mt_crud:
            retrieve_client = Retrieve(zlpt_user)
            report_id = generate_unique_id('rp', 8)
            mt_crud.report_create(report_id, search_type, file_name, task_id, '开始计算',None, match_type, metric_task_id)

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
            mt_crud.metric_task_update(metric_task_id, status="完成")
            mt_crud.report_update(report_id, status='计算完成')
        return True
    except Exception as e:
        print(f"cal_metric error: {e}")
        with MetricTasksCRUD() as mt_crud:
            mt_crud.metric_task_update(metric_task_id, status="失败")  # 设置为失败状态
        return False


@local_knowledge_detail_task_bp.route('/local_knowledge_detail/task/metric/create', methods=['POST'])
def create_metric_task():
    """
    创建指标任务
    """
    try:
        data = request.get_json()
        task_id = data.get('task_id')
        match_type = data.get('match_type')
        
        if not task_id or not match_type:
            return jsonify({"success": False, "message": "缺少必要参数"}), 400
            
        # 验证匹配方式
        valid_match_types = ['chunkIdMatch', 'chunkTextMatch']
        if match_type not in valid_match_types:
            return jsonify({"success": False, "message": "无效的匹配方式"}), 400
        metric_task_id = generate_unique_id('mt', 8)
        # 如果是切片语义匹配，需要知识库ID
        knowledge_base_id = None
        if match_type == 'chunkTextMatch':
            knowledge_base_id = data.get('knowledge_base_id')
            if not knowledge_base_id:
                return jsonify({"success": False, "message": "切片语义匹配需要指定知识库ID"}), 400
        
        with MetricTasksCRUD() as m_crud:
            # 创建指标任务，传递匹配方式
            success = m_crud.metric_task_create(
                metric_task_id=metric_task_id,
                task_id=task_id, 
                status='未开始',
                knowledge_base_id=knowledge_base_id,# 如果有的话
                match_type=match_type
            )
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
                if task[16]:
                    combined_data = {
                        'task_id': task[0],
                        'task_name': task[1],
                        'annotation_type': task[12],
                        'status': task[13],
                        'search_type': task[14],
                        'match_type': task[15],
                        'metric_task_id': task[16]
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
        metric_task_id = data.get('metric_task_id')  # 新增参数

        if not task_id or not search_type or not match_type or not metric_task_id:
            return jsonify({'success': False, 'message': '缺少必要参数'}), 400

        # 查询任务相关信息
        with LabelStudioCrud() as ls_crud:
            annotation_task_info = ls_crud.annotation_task_get_by_id(task_id=task_id)

        if not annotation_task_info:
            return jsonify({'success': False, 'message': '找不到指定的任务'}), 400
        project_id = annotation_task_info.get('label_studio_project_id')
        # 查询问题列表
        with QuestionsCRUD() as q_crud:
            questions_list = q_crud.questions_list(task_id=task_id)

        if not questions_list:
            return jsonify({'success': False, 'message': '没有找到相关问题'}), 400
        # 如果是chunkTextMatch，从ai_metric_tasks表中获取knowledge_base_id
        if match_type == 'chunkTextMatch':
            with MetricTasksCRUD() as mt_crud:
                metric_task_info = mt_crud.metric_task_list(metric_task_id=metric_task_id)
                if metric_task_info and len(metric_task_info) > 0:
                    knowledge_base_id = metric_task_info[0][5]
                else:
                    return jsonify({'success': False, 'message': '找不到对应的指标任务'}), 400
        else:
            # 对于chunkIdMatch，使用标注任务中的knowledge_base_id
            knowledge_base_id = annotation_task_info['knowledge_base_id']

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
                            match_type, questions_list, file_name, metric_task_id)

        return jsonify({'success': True, 'message': '计算任务已启动'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@local_knowledge_detail_task_bp.route('/local_knowledge_detail/task/metric/get_report', methods=['GET'])
def get_report():
    """
    获取报告内容
    """
    try:
        metric_task_id = request.args.get('metric_task_id')
        if not metric_task_id:
            return jsonify({"success": False, "message": "缺少metric_task_id参数"}), 400

        with MetricTasksCRUD() as mt_crud:
            report_list = mt_crud.report_list(metric_task_id=metric_task_id)
            if report_list:
                report_dict_list = [mt_crud._report_to_json(report) for report in report_list]
            else:
                report_dict_list = []
        return jsonify({
            "success": True,
            "data": report_dict_list,
        })
    except Exception as e:
        logger.error(f"获取报告时发生错误: {str(e)}")
        return jsonify({"success": False, "message": f"获取报告时发生错误: {str(e)}"}), 500


@local_knowledge_detail_task_bp.route('/local_knowledge_detail/task/metric/delete_report', methods=['DELETE'])
def delete_report():
    """
    删除报告
    """
    try:
        data = request.get_json()
        report_id = data.get('report_id')
        if not report_id:
            return jsonify({"success": False, "message": "缺少report_id参数"}), 400
        with MetricTasksCRUD() as mt_crud:
            # 获取报告信息以确定要删除的文件路径
            report_list = mt_crud.report_list(report_id=report_id)
            if not report_list:
                return jsonify({"success": False, "message": "报告不存在"}), 400
            report_info = mt_crud._report_to_json(report_list[0])
            # 获取关联的任务信息以获取知识库ID
            view_task_info = mt_crud.view_get_annotation_metric_tasks(task_id=report_info['task_id'])
            if not view_task_info:
                return jsonify({"success": False, "message": "无法获取任务信息"}), 400
            knowledge_base_id = view_task_info[0][5]
            file_path = Path(REPORT_PATH) / knowledge_base_id / report_info['filepath']
            # 尝试删除文件
            if file_path.exists():
                try:
                    file_path.unlink()  # 删除文件
                    logger.info(f"报告文件已删除: {file_path}")
                except Exception as e:
                    logger.error(f"删除报告文件时出错: {str(e)}")
            else:
                logger.warning(f"报告文件不存在: {file_path}")
            # 删除数据库记录
            success = mt_crud.report_delete(report_id)
            if success:
                return jsonify({"success": True, "message": "报告删除成功"})
            else:
                return jsonify({"success": False, "message": "报告删除失败"}), 500
    except Exception as e:
        logger.error(f"删除报告时发生错误: {str(e)}")
        return jsonify({"success": False, "message": f"删除报告时发生错误: {str(e)}"}), 500


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


@local_knowledge_detail_task_bp.route('/local_knowledge_detail/task/metric/get_task_info', methods=['GET'])
def get_task_info():
    """
    获取单个任务的详细信息
    """
    try:
        task_id = request.args.get('task_id')
        if not task_id:
            return jsonify({"success": False, "message": "缺少task_id参数"}), 400

        with MetricTasksCRUD() as mt_crud:
            task_info = mt_crud.view_get_annotation_metric_tasks(task_id=task_id)
            if not task_info:
                return jsonify({"success": False, "message": "找不到指定的任务"}), 404
            
            # 返回任务信息
            task_data = {
                'task_id': task_info[0][0],
                'task_name': task_info[0][1],
                'annotation_type': task_info[0][12],
                'status': task_info[0][13],
                'search_type': task_info[0][14],
                'match_type': task_info[0][15],
                'metric_task_id': task_info[0][16]
            }
            
        return jsonify({"success": True, "data": task_data})
    except Exception as e:
        logger.error(f"获取任务信息时发生错误: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": f"获取任务信息时发生错误: {str(e)}"}), 500


@local_knowledge_detail_task_bp.route('/local_knowledge_detail/task/metric/update_match_type', methods=['POST'])
def update_task_match_type():
    """
    更新任务的匹配方式信息
    """
    try:
        data = request.get_json()
        task_id = data.get('task_id')
        match_type = data.get('match_type')
        search_type = data.get('search_type')
        knowledge_base_id = data.get('knowledge_base_id')  # 仅在chunkTextMatch时需要

        if not task_id or not match_type or not search_type:
            return jsonify({"success": False, "message": "缺少必要参数"}), 400

        # 验证匹配方式
        valid_match_types = ['chunkIdMatch', 'chunkTextMatch']
        if match_type not in valid_match_types:
            return jsonify({"success": False, "message": "无效的匹配方式"}), 400

        # 验证召回方式
        valid_search_types = ['vectorSearch', 'hybridSearch', 'augmentedSearch']
        if search_type not in valid_search_types:
            return jsonify({"success": False, "message": "无效的召回方式"}), 400

        # 如果是切片语义匹配，需要知识库ID
        if match_type == 'chunkTextMatch' and not knowledge_base_id:
            return jsonify({"success": False, "message": "切片语义匹配需要指定知识库ID"}), 400

        with MetricTasksCRUD() as mt_crud:
            # 检查任务是否存在
            existing_task = mt_crud.metric_task_list(task_id=task_id)
            if not existing_task:
                # 如果任务不存在，创建新的指标任务记录
                metric_task_id = generate_unique_id('mt', 8)
                success = mt_crud.metric_task_create(
                    metric_task_id=metric_task_id,
                    task_id=task_id,
                    status='未开始',
                    knowledge_base_id=knowledge_base_id if match_type == 'chunkTextMatch' else None,
                    match_type=match_type,
                    search_type=search_type
                )
            else:
                # 如果任务存在，更新现有记录
                success = mt_crud.metric_task_update(
                    task_id=task_id,
                    match_type=match_type,
                    search_type=search_type,
                    knowledge_base_id=knowledge_base_id if match_type == 'chunkTextMatch' else None
                )

            if success:
                return jsonify({"success": True, "message": "任务匹配方式更新成功"})
            else:
                return jsonify({"success": False, "message": "更新任务匹配方式失败"}), 500

    except Exception as e:
        logger.error(f"更新任务匹配方式时发生错误: {str(e)}")
        return jsonify({"success": False, "message": f"更新任务匹配方式时发生错误: {str(e)}"}), 500


@local_knowledge_detail_task_bp.route('/local_knowledge_detail/task/metric/delete_task', methods=['DELETE'])
def delete_task():
    """
    删除指标任务及其相关报告
    """
    try:
        data = request.get_json()
        metric_task_id = data.get('metric_task_id')
        if not metric_task_id:
            return jsonify({"success": False, "message": "缺少metric_task_id参数"}), 400
        
        with MetricTasksCRUD() as mt_crud:
            # 首先查询该任务的所有报告
            reports = mt_crud.report_list(metric_task_id=metric_task_id)
            
            # 删除所有相关的报告文件和记录
            for report in reports:
                report_info = mt_crud._report_to_json(report)
                report_id = report_info['report_id']
                
                # 获取关联的任务信息以获取知识库ID
                view_task_info = mt_crud.view_get_annotation_metric_tasks(task_id=report_info['task_id'])
                if view_task_info:
                    knowledge_base_id = view_task_info[0][5]
                    file_path = Path(REPORT_PATH) / knowledge_base_id / report_info['filepath']
                    
                    # 尝试删除文件
                    if file_path.exists():
                        try:
                            file_path.unlink()  # 删除文件
                            logger.info(f"报告文件已删除: {file_path}")
                        except Exception as e:
                            logger.error(f"删除报告文件时出错: {str(e)}")
                    else:
                        logger.warning(f"报告文件不存在: {file_path}")
                    
                    # 删除数据库记录
                    mt_crud.report_delete(report_id)
                    logger.info(f"报告记录已删除: {report_id}")
            
            # 删除指标任务本身
            success = mt_crud.metric_task_delete(metric_task_id)
            if success:
                logger.info(f"指标任务删除成功: {metric_task_id}")
                return jsonify({"success": True, "message": "任务删除成功"})
            else:
                logger.error(f"指标任务删除失败: {metric_task_id}")
                return jsonify({"success": False, "message": "任务删除失败"}), 500
                
    except Exception as e:
        logger.error(f"删除任务时发生错误: {str(e)}")
        return jsonify({"success": False, "message": f"删除任务时发生错误: {str(e)}"}), 500


