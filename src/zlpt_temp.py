import logging
import os
from pathlib import Path

from jsonpath import jsonpath

from env_config_init import  REPORT_PATH

from typing import Callable, List, Dict, Any

from src.zlpt.login import LoginManager
from src.zlpt.api.knowledge_base import KnowledgeBase,Retrieve
from src.zlpt.api.project import Project

from src.label_studio_api import LabelStudioXMLGenerator, create_tasks
from src.label_studio_api.task import get_tasks_with_specific_choice
from src.label_studio_api.label_studio_client import LabelStudioLogin
from src.label_studio_api.ml_backed.prediction_creator import LabelStudioPredictionCreator
from utils.zl_to_label_studio import doc_slices_format_for_label_studio
from utils.pub_funs import save_json_file
from src.sql_funs import Environment_Crud, LabelStudioCrud
from check_chunk.checker_funcs import calculate_chunk_recall_metrics, calculate_similarity_recall_metrics
from check_chunk.checkers.AlignmentBasedChecker import AlignmentBasedChecker

logger = logging.getLogger(__name__)

__all__ = [
    "zlpt_login",
    "ls_login",
    "zlpt_create_knowledge_base",
    "zlpt_upload_files",
    "zlpt_get_chunk_all_by_doc_id",
    "ls_create_project",
    "ls_create_tasks",
    "cal_metric_by_chunk_id_fullmatch",
    "LabelStudioLogin",
    "label_by_prediction"

]
CHUNK_ID_PATH = '$.data.records..chunk_id'
CHUNK_TEXT_PATH = '$.data.records..chunk_text'


def zlpt_create_knowledge_base(know_client: KnowledgeBase, doc_name, chunk_size, chunk_overlap):
    """
    在紫鸾平台创建知识库

    Args:
        know_client (KnowledgeBase): 知识库客户端实例
        doc_name (str): 文档名称
        chunk_size (int): 切片大小
        chunk_overlap (int): 切片重叠大小

    Returns:
        str: 创建的知识库名称
    """
    name = f'{doc_name}_{chunk_size}_{chunk_overlap}'
    logger.info(f"创建知识库: {name}")
    try:
        res = know_client.knowledge_addOrUpdate(name)
        logger.info(f"知识库创建成功: {name}")
        logger.info(res)
        return name
    except Exception as e:
        logger.error(f"知识库创建失败: {e}")
        raise


def zlpt_upload_files(know_client: KnowledgeBase, file_lists, kno_id, content_code, chunk_size, chunk_overlap,
                      **kwargs):
    """
    上传文件到紫鸾平台的知识库中

    Args:
        know_client (KnowledgeBase): 知识库客户端实例
        file_lists (list): 文件路径
        kno_id (str): 知识库ID
        content_code (str): 内容编码
        chunk_size (int): 切片大小
        chunk_overlap (int): 切片重叠大小
        **kwargs: 其他可选参数

    Returns:
        tuple: 包含上传结果和数据ID的元组
    """
    logger.info(f"开始上传文件到知识库: {kno_id}")
    data_ids = []

    try:
        for file_path in file_lists:
            if os.path.isfile(file_path):
                logger.debug(f"正在上传文件: {file_path}")
                res = know_client.upload_attachment(file_path, content_code)
                data_ids.append(res['data'])
            else:
                logger.warning(f"文件 {file_path} 不存在")
                return False
        logger.info(f"文件上传完成，共上传 {len(file_lists)} 个文件\n上传的文件列表: {file_lists}\n开始更新文档信息")
        res = know_client.doc_addOrUpdate(kno_id, content_code, data_ids, chunk_size, chunk_overlap, **kwargs)
        logger.info("文档信息更新成功")
        return res
    except Exception as e:
        logger.error(f"文件上传过程中发生错误: {e}")
        raise e


def zlpt_get_chunk_all_by_doc_id(know_client, doc_id):
    """
      通过文档ID获取对应文档的名称和所有切片

      Args:
          know_client: 知识库客户端实例
          doc_id (str): 文档ID

      Returns:
          tuple: 包含文档名称和所有切片的元组
      """
    logger.info(f"获取文档 {doc_id} 的所有切片")
    try:
        doc_name, chunk_all = know_client.doc_get_chunk_all(doc_id)
        logger.info(f"成功获取文档 {doc_name} 的切片，共 {len(chunk_all)} 个")
        return doc_name, chunk_all
    except Exception as e:
        logger.error(f"获取文档切片失败: {e}")
        raise e


def ls_create_project(ls_user, title, QUESTION_JSON, description=''):
    """
    在Label Studio中创建项目并设置标签配置
    Args:
        title (str): 项目标题
        description (str, optional): 项目描述，默认为空字符串

    Returns:
        Project: 创建好的Label Studio项目对象
    """
    logger.info(f"在Label Studio中创建项目: {title}")
    try:
        label_config = LabelStudioXMLGenerator().generate_from_json(QUESTION_JSON)
        project = ls_user.create_project(
            title=title,
            description=description,
            label_config=label_config,
            show_instruction=True,
            enable_empty_annotation=False,
        )
        logger.info(f"Label Studio项目创建成功: {title}")
        return project
    except Exception as e:
        logger.error(f"Label Studio项目创建失败: {e}")
        raise e


def ls_create_tasks(know_client, project, doc_ids):
    # 根据doc_ids获取切片
    chunk_all = []
    try:
        for doc_id in doc_ids:
            doc_name, chunks = zlpt_get_chunk_all_by_doc_id(know_client, doc_id)
            chunk_all.extend(chunks)
        logger.info("开始创建Label Studio任务")
        tasks = doc_slices_format_for_label_studio(chunk_all)
        res = create_tasks(project, tasks)  # [task_id1,task_id2...]
        return res, len(chunk_all)
    except Exception as e:
        logger.error(f"创建Label Studio任务失败: {e}")
        raise e


def _process_question_chunk_data(
        project,
        question: str,
        kno_id: str,
        search_type: str,
        extract_zlpt_chunk_fn: Callable[[Dict], Any],
        extract_labeled_chunk_fn: Callable[[List[Dict]], Any],
        compute_metrics_fn: Callable[[Any, Any], Dict],
        retrieve_client
) -> Dict:
    """处理单个问题的 chunk 数据并计算指标"""
    try:
        zlpt_retrieve_data = retrieve_client.webKnowledgeRetrieve(search_type, question, kno_id)
        zlpt_records_count = len(zlpt_retrieve_data.get('data', {}).get('records', []))
        logger.debug(f"从知识平台获取到 {zlpt_records_count} 个切片，问题: {question}")

        labeled_tasks = get_tasks_with_specific_choice(project, question)  # project 已在外层传递
        logger.debug(f"从Label Studio获取到 {len(labeled_tasks)} 个已标注任务，问题: {question}")

        zlpt_chunks = extract_zlpt_chunk_fn(zlpt_retrieve_data)
        labeled_chunks = extract_labeled_chunk_fn(labeled_tasks)

        metrics = compute_metrics_fn(labeled_chunks, zlpt_chunks)
        logger.info(f"问题 [{question}] 的切片质量计算结果: {metrics}")
        return metrics

    except Exception as e:
        logger.error(f"处理问题 '{question}' 时发生异常：{e}", exc_info=True)
        return {"error": str(e)}


def _get_project(ls_user, project_id: str):
    """根据 project_id 或 project_name 获取 Label Studio 项目对象"""

    return ls_user.get_project(project_id)


def cal_metric_by_chunk_id_fullmatch(ls_user, project_id, kno_id: str, search_type: str,
                                     questions: List[Dict[str, Any]], file_name: str, retrieve_client
                                     ):
    def extract_zlpt_chunk_ids(data):
        return jsonpath(data, CHUNK_ID_PATH) or []

    def extract_labeled_chunk_ids(tasks):
        return [task['data']['chunk_id'] for task in tasks]

    logger.info(f"共找到 {len(questions)} 个问题需要处理")
    metric_all = {}
    project = _get_project(ls_user, project_id)
    logger.info(f"开始获取项目[{project.title}]的切片数据，知识ID:[{kno_id}]，搜索类型:[{search_type}]")
    logger.debug(f"成功获取项目: {project.title}")
    file_path = Path(REPORT_PATH) / kno_id / file_name
    file_path.parent.mkdir(parents=True, exist_ok=True)
    for question in questions:
        logger.info(f"正在处理问题: {question}")
        metrics = _process_question_chunk_data(
            project=project,
            question=question['question_content'],
            kno_id=kno_id,
            search_type=search_type,
            extract_zlpt_chunk_fn=extract_zlpt_chunk_ids,
            extract_labeled_chunk_fn=extract_labeled_chunk_ids,
            compute_metrics_fn=calculate_chunk_recall_metrics,
            retrieve_client=retrieve_client
        )
        metrics['type'] = question['question_type']
        metric_all[question['question_content']] = metrics

    save_json_file(metric_all, str(file_path))
    logger.info(f"所有问题的切片质量指标已保存至 {file_path} 文件")


def cal_metric_by_chunk_text_overlay_and_similarity(ls_user, project_id, kno_id: str, search_type: str,
                                                    questions: List[Dict[str, Any]], file_name: str, retrieve_client
                                                    ):
    ali_checker = AlignmentBasedChecker()
    project = _get_project(ls_user, project_id)
    metric_all = {}
    logger.info(f"开始获取项目[{project.title}]的切片数据，知识ID:[{kno_id}]，搜索类型:[{search_type}]")
    file_path = Path(REPORT_PATH) / kno_id / file_name
    logger.info(f"共找到 {len(questions)} 个问题需要处理")

    def extract_zlpt_chunk_texts(data):
        return jsonpath(data, CHUNK_TEXT_PATH) or []

    def extract_labeled_chunk_texts(tasks):
        return [task['data']['text'] for task in tasks]

    def cal_similarity(chunk_list1, chunk_list2):
        chunk_similarity_list = ali_checker.check_chunk_match(chunk_list1, chunk_list2)
        return calculate_similarity_recall_metrics(chunk_similarity_list, len(chunk_list2))

    for question in questions:
        logger.debug(f"正在处理问题: {question}")
        metrics = _process_question_chunk_data(
            project=project,
            question=question['question_content'],
            kno_id=kno_id,
            search_type=search_type,
            extract_zlpt_chunk_fn=extract_zlpt_chunk_texts,
            extract_labeled_chunk_fn=extract_labeled_chunk_texts,
            compute_metrics_fn=cal_similarity,
            retrieve_client=retrieve_client
        )
        metrics['type'] = question['question_type']
        metric_all[question['question_content']] = metrics

    save_json_file(metric_all, str(file_path))
    logger.info(f"所有问题的切片质量指标已保存至 {file_path} 文件")


def label_by_prediction(ls_user, project, question_json):
    """
    为项目中的所有任务创建预测标签
    
    Args:
        ls_user: Label Studio 用户实例
        project: Label Studio 项目实例
        question_json: 问题JSON配置
    
    Returns:
        list: 预测结果列表
    """
    prediction_creator = LabelStudioPredictionCreator(ls_user, question_json)
    tasks = project.get_tasks()

    predictions = []
    for task in tasks:
        try:
            result = prediction_creator.create_prediction_for_task(task, project)
            if result:
                predictions.append(result)
        except Exception as e:
            logger.error(f"处理任务 {task.id} 时发生错误: {str(e)}", exc_info=True)
            # TODO: 添加错误处理逻辑

    return predictions


def zlpt_login(zlpt_base_id=None, crud=None, knowledge_base_id=None):
    """
    初始化 ZLPT 登录管理器
    
    Args:
        zlpt_base_id: ZLPT 基础 ID
        crud: 数据库操作实例
        knowledge_base_id: 知识库 ID
    
    Returns:
        LoginManager 实例或 False（表示失败）
    """
    should_disconnect = False

    # 如果没有提供crud实例，则创建一个新的连接
    if crud is None:
        crud = Environment_Crud()
        crud.connect()
        should_disconnect = True

    try:
        # 如果提供了知识库ID，则从中获取zlpt_base_id
        if knowledge_base_id:
            kb_result = crud.get_knowledge_base(knowledge_id=knowledge_base_id)
            if not kb_result:
                return False
            zlpt_base_id = kb_result[0][11]

        # 获取环境列表信息
        env_result = crud.environment_list(zlpt_base_id=zlpt_base_id)
        if not env_result:
            return False

        # 转换环境信息为字典格式
        env_data = crud._environment_list_to_json(env_result[0])
        # 创建并返回登录管理器实例
        zlpt_user = LoginManager(
            env_data['zlpt_base_url'],
            env_data['username'],
            env_data['password'],
            env_data['domain'],
            env_data['key1'],
            env_data['key2_add'],
            env_data['pk']
        )
        return zlpt_user

    finally:
        # 如果函数内部创建了数据库连接，则在此关闭
        if should_disconnect:
            crud.disconnect()


def ls_login(url, api, label_studio_id, crud=None):
    ls_info = None
    if label_studio_id:
        if crud:
            ls_info = crud.label_studio_list(label_studio_id=label_studio_id)
        else:
            with LabelStudioCrud() as ls_crud:
                ls_info = ls_crud.label_studio_list(label_studio_id=label_studio_id)
        if ls_info:
            return LabelStudioLogin(url=ls_info[0][1], api_key=ls_info[0][2], label_studio_id=label_studio_id)
        else:
            logger.info(f"未找到ID为{label_studio_id}的Label Studio信息")
            return False
    else:
        return LabelStudioLogin(url, api, label_studio_id)
