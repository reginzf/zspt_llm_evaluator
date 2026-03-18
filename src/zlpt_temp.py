import logging
import os
import tempfile
from pathlib import Path

from jsonpath import jsonpath


from typing import Callable, List, Dict, Any

from src.zlpt.login import LoginManager
from src.zlpt.api.knowledge_base import KnowledgeBase
from src.zlpt.api.project import Project

from src.label_studio_api import LabelStudioXMLGenerator, create_tasks
from src.label_studio_api.task import get_tasks_with_specific_choice
from src.label_studio_api.label_studio_client import LabelStudioLogin
from src.label_studio_api.ml_backed.prediction_creator import LabelStudioPredictionCreator
from src.utils.pub_funs import write_json_file
from src.sql_funs import Environment_Crud, LabelStudioCrud
from src.utils.minio_client import get_knowledge_files_client
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
# 模板定义
LABEL_STUDIO_TEMPLATE = {
    "text": "",
    # 自定义字段
    "size": None,
    "chunk_title": "",
    "chunk_id": "",
    "score": None,
    "metaData": None,
    "fileName": "",
    "start_at": None
}


def doc_slices_format_for_label_studio(records):
    """
    将文档切片转换为label studio 的格式
    :param doc_name:
    :param records:KnowledgeBasePage.doc_get_chunk_all的返回
    :return:
    """
    res = []
    print(records)
    for data in records:
        # 去掉title和固定字段，剩余为text

        item = LABEL_STUDIO_TEMPLATE.copy()
        item.update({
            "text": data["chunk_text"],
            # 自定义字段
            "size": data["chunk_size"],
            "chunk_title": data["chunk_title"],
            "chunk_id": data["chunk_id"],
            "score": None,
            "metaData": None,
            "fileName": data["doc_title"],
        })
        res.append(item)
    return res


def zlpt_create_knowledge_base(know_client: KnowledgeBase, doc_name, chunk_size, chunk_overlap):
    """
    在紫鸾平台创建知识库

    Args:
        know_client (KnowledgeBase): 知识库客户端实例
        doc_name (str): 文档名称
        chunk_size (int): 切片大小
        chunk_overlap (int): 切片重叠大小

    Returns:
        tuple: (知识库名称, 知识库ID)
    """
    name = f'{doc_name}_{chunk_size}_{chunk_overlap}'
    logger.info(f"创建知识库: {name}")
    try:
        # 使用实际观察到的API参数创建知识库
        res = know_client.knowledge_addOrUpdate(
            knowledgeName=name,
            description='',
            visibleRange=0,  # 组织内公开
            deptIdList=[],
            manageDeptIdList=['']  # 根部门管理
        )
        logger.info(f"知识库创建API响应: {res}")
        
        # 检查响应是否成功
        if not isinstance(res, dict):
            logger.error(f"API返回格式错误: {res}")
            return name, None
        
        # 处理授权错误
        if res.get('code') == 401 or 'Authorization Required' in str(res.get('message', '')):
            logger.error(f"远程平台授权失败: {res}")
            return name, None
        
        # 处理其他错误
        if res.get('code') != 200:
            logger.error(f"远程平台返回错误: {res}")
            return name, None
        
        # 从响应中提取知识库ID (data字段直接包含ID)
        kno_id = res.get('data')
        if not kno_id:
            logger.error(f"API响应中缺少知识库ID: {res}")
            return name, None
            
        logger.info(f"知识库创建成功: {name}, ID: {kno_id}")
        return name, kno_id
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
    failed_docs = []
    try:
        for doc_id in doc_ids:
            try:
                doc_name, chunks = zlpt_get_chunk_all_by_doc_id(know_client, doc_id)
                if chunks:
                    chunk_all.extend(chunks)
                else:
                    logger.warning(f"文档 {doc_id} 没有切片数据")
                    failed_docs.append(doc_id)
            except Exception as doc_e:
                logger.error(f"获取文档 {doc_id} 切片失败: {doc_e}")
                failed_docs.append(doc_id)
        
        if not chunk_all:
            raise ValueError(f"没有获取到任何切片数据，失败的文档: {failed_docs}")
        
        logger.info(f"开始创建Label Studio任务，共 {len(chunk_all)} 个切片")
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
    
    # 构建 MinIO 对象名称: reports/{knowledge_base_id}/{file_name}
    minio_object_name = f"reports/{kno_id}/{file_name}"
    
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

    # 使用临时文件保存 JSON，然后上传到 MinIO
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as tmp_file:
        tmp_file_path = tmp_file.name
    
    try:
        write_json_file(tmp_file_path, metric_all)
        
        # 上传到 MinIO
        minio_client = get_knowledge_files_client()
        upload_success = minio_client.upload_file(tmp_file_path, minio_object_name)
        
        if not upload_success:
            raise Exception(f"上传报告到 MinIO 失败: {minio_object_name}")
        
        logger.info(f"所有问题的切片质量指标已上传至 MinIO: {minio_object_name}")
    finally:
        # 清理临时文件
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)


def cal_metric_by_chunk_text_overlay_and_similarity(ls_user, project_id, kno_id: str, search_type: str,
                                                    questions: List[Dict[str, Any]], file_name: str, retrieve_client
                                                    ):
    ali_checker = AlignmentBasedChecker()
    project = _get_project(ls_user, project_id)
    metric_all = {}
    logger.info(f"开始获取项目[{project.title}]的切片数据，知识ID:[{kno_id}]，搜索类型:[{search_type}]")
    logger.info(f"共找到 {len(questions)} 个问题需要处理")
    
    # 构建 MinIO 对象名称: reports/{knowledge_base_id}/{file_name}
    minio_object_name = f"reports/{kno_id}/{file_name}"

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

    # 使用临时文件保存 JSON，然后上传到 MinIO
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as tmp_file:
        tmp_file_path = tmp_file.name
    
    try:
        write_json_file(tmp_file_path, metric_all)
        
        # 上传到 MinIO
        minio_client = get_knowledge_files_client()
        upload_success = minio_client.upload_file(tmp_file_path, minio_object_name)
        
        if not upload_success:
            raise Exception(f"上传报告到 MinIO 失败: {minio_object_name}")
        
        logger.info(f"所有问题的切片质量指标已上传至 MinIO: {minio_object_name}")
    finally:
        # 清理临时文件
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)


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


def zlpt_login(zlpt_base_id=None, crud=None, knowledge_base_id=None, project_id=None, auto_switch_project=True):
    """
    初始化 ZLPT 登录管理器

    Args:
        zlpt_base_id: ZLPT 基础 ID
        crud: 数据库操作实例
        knowledge_base_id: 知识库 ID
        project_id: 目标项目ID，如果不提供则自动选择第一个非default项目
        auto_switch_project: 是否自动切换到非default项目（默认True）

    Returns:
        LoginManager 实例或 False（表示失败）
    """
    should_disconnect = False
    login_manager = None

    # 如果没有提供crud实例，则创建一个新的连接
    if crud is None:
        crud = Environment_Crud()
        crud.connect()
        should_disconnect = True

    try:
        # 如果提供了知识库ID，则从中获取zlpt_base_id
        if knowledge_base_id:
            logger.info(f"正在通过知识库ID {knowledge_base_id} 获取ZLPT配置信息")
            kb_result = crud.get_knowledge_base(knowledge_id=knowledge_base_id)
            if not kb_result:
                logger.error(f"未找到知识库 {knowledge_base_id} 的信息")
                return False
            # 检查返回结果是否有足够的列
            if len(kb_result[0]) <= 11:
                logger.error(f"知识库 {knowledge_base_id} 的返回结果缺少zlpt_base_id字段")
                return False
            zlpt_base_id = kb_result[0][11]
            if not zlpt_base_id:
                logger.error(f"知识库 {knowledge_base_id} 的zlpt_base_id为空")
                return False

        if not zlpt_base_id:
            logger.error("zlpt_base_id不能为空")
            return False

        # 获取环境列表信息
        logger.info(f"正在获取ZLPT环境配置: base_id={zlpt_base_id}")
        env_result = crud.environment_list(zlpt_base_id=zlpt_base_id)
        if not env_result:
            logger.error(f"未找到zlpt_base_id {zlpt_base_id} 的环境信息")
            return False

        # 转换环境信息为字典格式
        env_data = crud._environment_list_to_json(env_result[0])
        if not env_data:
            logger.error("环境数据转换失败")
            return False

        # 检查必要的字段
        required_fields = ['zlpt_base_url', 'username', 'password', 'domain', 'key1', 'key2_add', 'pk']
        missing_fields = [field for field in required_fields if field not in env_data or env_data[field] is None]
        if missing_fields:
            logger.error(f"环境数据缺少必要字段: {', '.join(missing_fields)}")
            return False

        # 创建登录管理器实例
        logger.info(f"正在初始化LoginManager: url={env_data['zlpt_base_url']}, user={env_data['username']}")
        try:
            login_manager = LoginManager(
                env_data['zlpt_base_url'],
                env_data['username'],
                env_data['password'],
                env_data['domain'],
                env_data['key1'],
                env_data['key2_add'],
                env_data['pk']
            )
        except Exception as e:
            logger.error(f"LoginManager初始化失败: {str(e)}", exc_info=True)
            return False

        # 验证登录是否成功
        if not login_manager.auth_token:
            logger.error("登录失败：未能获取到认证token")
            return False

        logger.info(f"登录成功，当前项目: {login_manager.get_current_project() or 'default'}")

        # 如果需要，执行项目切换
        if auto_switch_project:
            logger.info("正在检查和切换项目...")
            project_switch_success = login_manager.project_switch(project_id)
            if not project_switch_success:
                logger.warning("项目切换失败，将继续使用当前项目")
            else:
                logger.info(f"项目切换完成，当前项目: {login_manager.get_current_project()}")
        elif project_id:
            # 指定了项目ID但不需要自动切换，直接切换
            logger.info(f"正在切换到指定项目: {project_id}")
            switch_result = login_manager.switch_to_project(project_id)
            if not switch_result:
                logger.error(f"切换到项目 {project_id} 失败")
                return False

        # 最终验证token有效性
        project_info = login_manager.verify_current_project()
        if project_info["is_default"] and auto_switch_project:
            logger.warning("当前仍为default项目，部分功能可能受限")

        logger.info("ZLPT登录流程完成")
        return login_manager

    except Exception as e:
        logger.error(f"zlpt_login执行失败: {str(e)}", exc_info=True)
        return False

    finally:
        # 如果函数内部创建了数据库连接，则在此关闭
        if should_disconnect:
            try:
                crud.disconnect()
                logger.debug("数据库连接已关闭")
            except Exception as e:
                logger.warning(f"关闭数据库连接时发生错误: {e}")


def ls_login(url, api, label_studio_id, crud=None):
    """
    登录Label Studio
    
    Args:
        url: Label Studio URL
        api: Label Studio API Key
        label_studio_id: Label Studio环境ID
        crud: 数据库操作实例
    
    Returns:
        LabelStudioLogin实例或False（表示失败）
    """
    ls_info = None
    if label_studio_id:
        if crud:
            ls_info = crud.label_studio_list(label_studio_id=label_studio_id)
        else:
            with LabelStudioCrud() as ls_crud:
                ls_info = ls_crud.label_studio_list(label_studio_id=label_studio_id)
        if ls_info:
            # 检查URL和API key是否有效
            ls_url = ls_info[0][1] if len(ls_info[0]) > 1 else None
            ls_api_key = ls_info[0][2] if len(ls_info[0]) > 2 else None
            
            if not ls_url:
                logger.error(f"Label Studio环境 {label_studio_id} 的URL为空")
                return False
            if not ls_api_key:
                logger.error(f"Label Studio环境 {label_studio_id} 的API Key为空")
                return False
            
            try:
                return LabelStudioLogin(url=ls_url, api_key=ls_api_key, label_studio_id=label_studio_id)
            except Exception as e:
                logger.error(f"Label Studio登录失败: {str(e)}", exc_info=True)
                return False
        else:
            logger.info(f"未找到ID为{label_studio_id}的Label Studio信息")
            return False
    else:
        if not url or not api:
            logger.error("Label Studio URL和API Key不能为空")
            return False
        try:
            return LabelStudioLogin(url, api, label_studio_id)
        except Exception as e:
            logger.error(f"Label Studio登录失败: {str(e)}", exc_info=True)
            return False
