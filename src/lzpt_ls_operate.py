import os.path
import jsonpath
from utils.logger import logger

from env_config_init import settings, QUESTION_JSON, ZLPT_CHUNKS_DIR, LS_LABELED_CHUNKS_DIR, DOC_DIR, KNOWLEDGE_PATH, \
    REPORT_PATH
from zlpt.login import LoginManager
from zlpt.api.knowledge_base import Retrieve
from zlpt.api.knowledge_base import KnowledgeBase

from label_studio_api import create_tasks
from label_studio_api import label_studio_client
from label_studio_api import LabelStudioXMLGenerator
from label_studio_api.annotator import Annotator, AnnotationGenerator, AnnotateToCreate
from label_studio_api.ml_backed.prediction_creator import LabelStudioPredictionCreator

from utils.zl_to_label_studio import doc_slices_format_for_label_studio
from utils.questions import get_question_type_and_label
from utils.decorators import check
from utils.pub_funs import save_json_file, load_json_file
from typing import List, Dict, Any, Optional, Callable
from label_studio_api.task import get_tasks_with_specific_choice
from check_chunk.checker_funcs import calculate_chunk_recall_metrics, calculate_similarity_recall_metrics

annotation_generator = AnnotationGenerator()
label_generator = LabelStudioXMLGenerator(grid_columns=2)
chunk_size = settings.CHUNK_SIZE
chunk_overlap = settings.CHUNK_OVERLAP


def login_zlpt():
    """
    登录紫鸾平台并获取认证密钥

    Returns:
        LoginManager: 已登录的登录管理器实例
    """
    logger.info("开始登录紫鸾平台")
    login_manager = LoginManager(settings.ZLPT_BASE_URL)
    try:
        login_manager.login(settings.USERNAME, settings.PASSWORD, settings.DOMAIN)
        login_manager.get_auth_key()
        logger.info("紫鸾平台登录成功")
        return login_manager
    except Exception as e:
        logger.error(f"紫鸾平台登录失败: {e}")
        raise


zlpt_user = login_zlpt()
know_client = KnowledgeBase(zlpt_user)
retrieve_client = Retrieve(zlpt_user)


def login_label_studio():
    """
     获取Label Studio客户端实例

     Returns:
         label_studio_client: Label Studio客户端实例
     """
    return label_studio_client


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
        know_client.knowledge_addOrUpdate(name)
        logger.info(f"知识库创建成功: {name}")
        return name
    except Exception as e:
        logger.error(f"知识库创建失败: {e}")
        raise


def zlpt_upload_files(know_client: KnowledgeBase, doc_dir, kno_id, content_code, chunk_size, chunk_overlap, **kwargs):
    """
    上传文件到紫鸾平台的知识库中

    Args:
        know_client (KnowledgeBase): 知识库客户端实例
        doc_dir (str): 文件路径
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
    filenames = []
    try:
        for file in os.listdir(doc_dir):
            file_path = os.path.join(doc_dir, file)
            if os.path.isfile(file_path):
                logger.debug(f"正在上传文件: {file}")
                res = know_client.upload_attachment(file_path, content_code)
                data_ids.append(res['data'])
                filenames.append(file)

        logger.info(f"文件上传完成，共上传 {len(filenames)} 个文件")
        logger.debug(f"上传的文件列表: {filenames}")

        logger.info("开始更新文档信息")
        res = know_client.doc_addOrUpdate(kno_id, content_code, data_ids, chunk_size, chunk_overlap, **kwargs)
        logger.info("文档信息更新成功")
        return res, filenames
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


def _save_chunks_locally(doc_name, chunks):
    """将切片数据保存至本地"""
    file_path = os.path.join(ZLPT_CHUNKS_DIR, f"{doc_name}.json")
    save_json_file({"chunks": chunks}, file_path)
    logger.info(f"已保存切片数据到: {file_path}")


def zlpt_get_chunk_save(doc_ids):
    zlpt_get_chunk_all = []
    for doc_id in doc_ids:
        doc_name, zlpt_get_doc_chunk_all = zlpt_get_chunk_all_by_doc_id(know_client, doc_id)
        zlpt_get_chunk_all.extend(zlpt_get_doc_chunk_all)
        _save_chunks_locally(doc_name, zlpt_get_doc_chunk_all)
    return zlpt_get_chunk_all


def zlpt_get_chunk_by_question(kno_id, question):
    """
    根据问题从知识库中检索相关切片

    Args:
        kno_id (str): 知识库ID
        question (str): 查询问题

    Returns:
        dict: 检索结果数据
    """
    retrieve_data = retrieve_client.webKnowledgeRetrieve('augmentedSearch', question, kno_id)
    return retrieve_data


@check(10, '检查是否完成学习', 20)
def zlpt_wait_learning(know_client, kno_id):
    logger.info(f"等待知识库 {kno_id} 完成学习")
    try:
        msgs = set(jsonpath.jsonpath(know_client.knowledge_doc_list(kno_id), '$.data.records..msg'))
        assert len(msgs) == 1 and msgs.pop() == '学习成功'
        logger.info(f"知识库 {kno_id} 学习完成")
    except AssertionError as ae:
        logger.error(f"知识库学习状态不符合预期: {ae}")
        raise ae
    except Exception as e:
        logger.error(f"知识库学习检查失败: {e}")
        raise e


ls_user = login_label_studio()
prediction_c = LabelStudioPredictionCreator(ls_user)


def ls_create_project(title, description=''):
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


def ls_create_tasks(project, chunk_all):
    """
    将切片数据转换为Label Studio任务格式并创建任务

    Args:
        project: Label Studio项目对象
        chunk_all (list): 所有切片数据列表

    Returns:
        list: 创建的任务ID列表
    """
    # 转换为ls的格式
    tasks = doc_slices_format_for_label_studio(chunk_all)
    # 在ls上创建任务
    res = create_tasks(project, tasks)
    return res  # [task_id1,task_id2...]


def ls_save_data(project_id):
    project = _get_project('', project_id)
    logger.info("导出任务数据")
    project_raw_data = project.export_tasks(export_type='JSON')
    file_path = os.path.join(LS_LABELED_CHUNKS_DIR, f"{QUESTION_JSON['doc_name']}.json")
    save_json_file(project_raw_data, file_path)


def label_chunks_by_chunk_id(annotator, question, chunks, to_name='text', prediction=False):
    """
       根据切片ID对返回的切片进行标注

       Args:
           annotator: Annotator项目对象
           question (str): 查询问题
           chunks (list): 需要标注的切片列表
           to_name (str): 目标字段名，默认为 'text'
           prediction (bool): 是否作为预测写入，默认为 False（即写入标注）
       """
    q_type, q_label = get_question_type_and_label(QUESTION_JSON, question)
    t_filter = "filter:tasks:data.chunk_id"

    logger.info(f"开始标注问题: {question}, 类型: {q_type}")

    success_count = 0
    failed_count = 0

    for chunk in chunks:
        target_filter = annotator.generate_filter_item(chunk['chunk_id'], t_filter, operator="equal")
        try:
            target_task = annotator.get_task_by_filter([target_filter])[0]
            # 创建标注
            annotation_data = [annotation_generator.generate_choice_annotation(q_type, to_name, [question])]
            annotate_to_create = AnnotateToCreate(
                annotation_data=annotation_data,
                lead_time=35.0,
                merge_existing=True  # 启用合并功能
            )
            if prediction:
                result = annotator.task_prediction_create(target_task, annotate_to_create)
            else:
                result = annotator.task_annotate_create(target_task, annotate_to_create)

            success_count += 1
            logger.debug(f"成功标注切片: {chunk['chunk_id']},{result}")
        except IndexError:
            logger.warning(f"未找到任务：{chunk['chunk_id']}")
            failed_count += 1
            continue
        except Exception as e:
            logger.error(f"标注切片 {chunk['chunk_id']} 时出错: {e}")
            failed_count += 1
            continue
    logger.info(f"标注完成 - 成功: {success_count}, 失败: {failed_count}")


def zlpt_create_project():
    logger.info("===step 1: 紫鸾知识库创建和文件上传 ===")
    try:
        logger.info(f"配置参数 - CHUNK_SIZE: {chunk_size}, CHUNK_OVERLAP: {chunk_overlap}")
        # 创建知识库
        knowledge_name = zlpt_create_knowledge_base(know_client, QUESTION_JSON['doc_name'], chunk_size, chunk_overlap)
        # 获取知识库id
        kno_id = know_client.knowledge_list(knowledge_name)['data'][0]['knowledgeId']
        knowledge_dict = {'kno_id': kno_id, 'name': knowledge_name, 'chunk_size': chunk_size,
                          'chunk_overlap': chunk_overlap}
        # 获取知识库的根id
        kno_root_id = know_client.knowledge_content_tree(kno_id)['data'][0]['contentCode']
        # 上传文件
        zlpt_upload_files(know_client, DOC_DIR, kno_id, kno_root_id, chunk_size, chunk_overlap)
        # 等待学习完成
        zlpt_wait_learning(know_client, kno_id)
        logger.info("紫鸾平台初始化流程完成")
        # 获取知识库下的所有doc_id
        doc_ids = jsonpath.jsonpath(know_client.knowledge_doc_list(kno_id), '$.data.records..docId')
        knowledge_dict['doc_ids'] = doc_ids
        logger.info(f"发现 {len(doc_ids)} 个文档")
        # 保存knowledge_dict到本地
        save_json_file(knowledge_dict, KNOWLEDGE_PATH)
        logger.info(f"保存知识库信息到: {KNOWLEDGE_PATH}\n{knowledge_dict}")
    except Exception as e:
        logger.error(f"紫鸾平台初始化流程失败: {e}")
        raise


def ls_create_project_and_tasks():
    logger.info("===step 2: label studio的项目、任务创建 ===")
    # 加载配置文件
    knowledge_dict = load_json_file(KNOWLEDGE_PATH)
    doc_ids = knowledge_dict['doc_ids']
    # 获取所有切片
    chunk_all = zlpt_get_chunk_save(doc_ids)
    # 创建项目
    project = ls_create_project(f'{knowledge_dict["name"]}')
    knowledge_dict['project_id'] = project.id
    # 创建任务
    logger.info("开始创建Label Studio任务")
    ls_create_tasks(project, chunk_all)
    save_json_file(knowledge_dict, KNOWLEDGE_PATH)


# 开始标注
def label_by_retrieve(kno_id, project_id, search_type, prediction=False):
    """
    通过 召回 进行标记或预测
    :param kno_id: 知识库ID
    :param project_id: Label Studio项目ID
    :param search_type: 检索方式，如 augmentedSearch、vectorSearch 等
    :param prediction: 是否将结果写入预测而非标注，默认为 False
    :return:
    """
    logger.info("初始化项目标注器")
    project = _get_project('', project_id)
    annotator = Annotator(project)

    # 召回并标注
    logger.info("开始召回并标注")
    for idx, question_dict in enumerate(QUESTION_JSON.get('datas', [])):
        questions = question_dict.get('questions', [])
        for q_idx, question in enumerate(questions):
            logger.debug(f"[{idx}-{q_idx}] Processing question: {question}")
            try:
                retrieve_data = retrieve_client.webKnowledgeRetrieve(search_type, question, kno_id)
            except Exception as e:
                logger.warning(f"Web knowledge retrieval failed for question '{question}': {e}")
                # todo 异常处理
                continue
            chunks = (
                retrieve_data.get("data", {})
                .get("records", [])
            )
            if not isinstance(chunks, list):
                logger.warning(f"Unexpected data type for 'records' in retrieved data for question '{question}'")
                continue
            label_chunks_by_chunk_id(annotator, question, chunks, 'text', prediction)


def label_by_prediction(project_id, task_ids: list = None):
    project = _get_project('', project_id)
    if not task_ids:
        task_ids = project.get_tasks_ids()
    logger.info(f"开始为项目 {project_id} 处理 {len(task_ids)} 个任务的预测标注")
    predictions = []
    for task_id in task_ids:
        try:
            task_data = project.get_task(task_id)
            res = prediction_c.create_prediction_for_task(task_data, project)
            predictions.append(res)
        except Exception as e:
            logger.error(f"处理任务 {task_id} 时发生错误: {str(e)}")
            # todo 添加错误处理逻辑
            continue
    return predictions


def label_by_llm(project_id, task_ids: list = None):
    logger.info("初始化项目标注器")
    project = _get_project('', project_id)
    # annotator = Annotator(project)
    for task_id in task_ids:
        try:
            task_data = project.get_task(task_id)
            # todo 根据llm获得每个chunk的预测结果，进行标注
        except Exception as e:
            logger.error(f"处理任务 {task_id} 时发生错误: {str(e)}")
            # todo 添加错误处理逻辑
            continue


# 计算metric相关的方法：

CHUNK_ID_PATH = '$.data.records..chunk_id'
CHUNK_TEXT_PATH = '$.data.records..chunk_text'


def _get_project(project_name: str, project_id: Optional[str]):
    """根据 project_id 或 project_name 获取 Label Studio 项目对象"""
    if project_id:
        return ls_user.get_project(project_id)
    projects = ls_user.get_projects(title=project_name)
    if not projects:
        raise ValueError(f"No project found with name '{project_name}'")
    return projects[0]


def _extract_questions() -> List[str]:
    """从全局 QUESTION_JSON 中提取所有问题"""
    questions = []
    for qs in jsonpath.jsonpath(QUESTION_JSON, '$..datas..questions') or []:
        questions.extend(qs)
    return questions


def _process_question_chunk_data(
        project,
        question: str,
        kno_id: str,
        search_type: str,
        extract_zlpt_chunk_fn: Callable[[Dict], Any],
        extract_labeled_chunk_fn: Callable[[List[Dict]], Any],
        compute_metrics_fn: Callable[[Any, Any], Dict]
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


def cal_metric_by_chunk_id_fullmatch(project_name: str, kno_id: str, search_type: str,
                                     project_id=None):
    """
    获取指定search_type的召回和label studio下已标注的数据，计算metric
    :param project_name: 在label studio上的项目名称
    :param kno_id: 在紫鸾知识平台上的知识库id
    :param search_type: 搜索类型，可选值为 vectorSearch(向量检索) | hybridSearch(混合检索) | augmentedSearch(增强检索)
    :param project_id: Label Studio项目ID（可选）
    :return:
    """
    project = _get_project(project_name, project_id)
    logger.info(f"开始获取项目[{project.title}]的切片数据，知识ID:[{kno_id}]，搜索类型:[{search_type}]")
    logger.debug(f"成功获取项目: {project.title}")
    file_path = REPORT_PATH / f'metric_chunk_id_{search_type}_{chunk_size}_{chunk_overlap}.json'
    questions = _extract_questions()
    logger.info(f"共找到 {len(questions)} 个问题需要处理")

    metric_all = {}

    def extract_zlpt_chunk_ids(data):
        return jsonpath.jsonpath(data, CHUNK_ID_PATH) or []

    def extract_labeled_chunk_ids(tasks):
        return [task['data']['chunk_id'] for task in tasks]

    for question in questions:
        logger.info(f"正在处理问题: {question}")
        # 获取当前问题的类型
        question_type = None
        for q_data in QUESTION_JSON.get('datas', []):
            if question in q_data.get('questions', []):
                question_type = q_data.get('type')
                break
        
        metrics = _process_question_chunk_data(
            project=project,
            question=question,
            kno_id=kno_id,
            search_type=search_type,
            extract_zlpt_chunk_fn=extract_zlpt_chunk_ids,
            extract_labeled_chunk_fn=extract_labeled_chunk_ids,
            compute_metrics_fn=calculate_chunk_recall_metrics
        )
        metrics['type'] = question_type
        metric_all[question] = metrics

    save_json_file(metric_all, file_path)
    logger.info(f"所有问题的切片质量指标已保存至 {file_path} 文件")


def cal_metric_by_chunk_text_overlay_and_similarity(project_name: str, kno_id: str, search_type: str,
                                                    project_id: Optional[str] = None):
    from check_chunk.checkers.AlignmentBasedChecker import AlignmentBasedChecker
    ali_checker = AlignmentBasedChecker()
    project = _get_project(project_name, project_id)
    logger.info(f"开始获取项目[{project.title}]的切片数据，知识ID:[{kno_id}]，搜索类型:[{search_type}]")
    file_path = REPORT_PATH / f'metric_similarity_{search_type}_{chunk_size}_{chunk_overlap}.json'
    questions = _extract_questions()
    logger.info(f"共找到 {len(questions)} 个问题需要处理")

    metric_all = {}

    def extract_zlpt_chunk_texts(data):
        return jsonpath.jsonpath(data, CHUNK_TEXT_PATH) or []

    def extract_labeled_chunk_texts(tasks):
        return [task['data']['text'] for task in tasks]

    def cal_similarity(chunk_list1, chunk_list2):
        chunk_similarity_list = ali_checker.check_chunk_match(chunk_list1, chunk_list2)
        return calculate_similarity_recall_metrics(chunk_similarity_list, len(chunk_list2))

    for question in questions:
        logger.debug(f"正在处理问题: {question}")
        metrics = _process_question_chunk_data(
            project=project,
            question=question,
            kno_id=kno_id,
            search_type=search_type,
            extract_zlpt_chunk_fn=extract_zlpt_chunk_texts,
            extract_labeled_chunk_fn=extract_labeled_chunk_texts,
            compute_metrics_fn=cal_similarity
        )
        metric_all[question] = metrics

    save_json_file(metric_all, file_path)
    logger.info(f"所有问题的切片质量指标已保存至 {file_path} 文件")
