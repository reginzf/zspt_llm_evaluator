import os.path
import jsonpath
from utils.logger import logger

from env_config_init import settings, QUESTION_JSON, ZLPT_CHUNKS_DIR, LS_LABELED_CHUNKS_DIR, DOC_DIR
from zlpt.login import LoginManager
from zlpt.api.knowledge_base.retriveve import Retrieve
from zlpt.api.knowledge_base.knowledgeBase import KnowledgeBase

from label_studio.task import create_tasks
from label_studio.label_studio_client import label_studio_client
from label_studio.labels import LabelStudioXMLGenerator
from label_studio.annotator import Annotator, AnnotationGenerator, AnnotateToCreate

from utils.zl_to_label_studio import doc_slices_format_for_label_studio
from utils.questions import get_question_type_and_label
from utils.decorators import check
from utils.pub_funs import save_json_file

annotation_generator = AnnotationGenerator()
label_generator = LabelStudioXMLGenerator(grid_columns=2)


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


def zlpt_get_chunk_by_question(zlpt_user, kno_id, question):
    """
    根据问题从知识库中检索相关切片

    Args:
        zlpt_user: 紫鸾平台用户实例
        kno_id (str): 知识库ID
        question (str): 查询问题

    Returns:
        dict: 检索结果数据
    """
    retrieve = Retrieve(zlpt_user)
    retrieve_data = retrieve.webKnowledgeRetrieve('augmentedSearch', question, kno_id)
    return retrieve_data


@check(10, '检查是否完成学习', 20)
def zlpt_wait_learning(know_client, kno_id):
    logger.info(f"等待知识库 {kno_id} 完成学习")
    try:
        msgs = set(jsonpath.jsonpath(know_client.knowledge_doc_list(kno_id), '$.data.records..msg'))
        assert len(msgs) == 1 and msgs.pop() == '学习成功'
        logger.info(f"知识库 {kno_id} 学习完成")
    except Exception as e:
        logger.error(f"知识库学习检查失败: {e}")
        raise e


def ls_create_project(ls_user, title, description=''):
    """
    在Label Studio中创建项目并设置标签配置

    Args:
        ls_user: Label Studio用户实例
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


def label_chunks_by_chunk_id(annotator, question, chunks, to_name='text'):
    """
       根据切片ID对返回的切片进行标注

       Args:
           annotator: Annotator项目对象
           question (str): 查询问题
           chunks (list): 需要标注的切片列表
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
            result = annotator.task_annotate_create(target_task, annotate_to_create)
            success_count += 1
            logger.debug(f"成功标注切片: {chunk['chunk_id']}")
        except IndexError:
            logger.warning(f"未找到任务：{chunk['chunk_id']}")
            failed_count += 1
            continue
        except Exception as e:
            logger.error(f"标注切片 {chunk['chunk_id']} 时出错: {e}")
            failed_count += 1
            continue

    logger.info(f"标注完成 - 成功: {success_count}, 失败: {failed_count}")


def lzpt_init(name, chunk_size, chunk_overlap, doc_dir, knowledge_dict):
    """
    初始化紫鸾平台：登录、创建知识库、上传文件

    Args:
        name (str): 知识库名称
        chunk_size (int): 切片大小
        chunk_overlap (int): 切片重叠大小
        doc_dir (str): 目标文件路径
        knowledge_dict (dict): 存储知识库信息的字典

    Returns:
        tuple: 包含紫鸾平台用户、知识库ID、知识库根ID和文档ID的元组
    """
    logger.info(f"开始初始化紫鸾平台流程 - 知识库: {name}")
    # 登录紫鸾平台，完成文件上传
    try:
        # 登录紫鸾平台，完成文件上传
        zlpt_user = login_zlpt()
        know_client = KnowledgeBase(zlpt_user)
        # 创建知识库
        knowledge_name = zlpt_create_knowledge_base(know_client, name, chunk_size, chunk_overlap)
        # 获取知识库id
        kno_id = know_client.knowledge_list(knowledge_name)['data'][0]['knowledgeId']
        knowledge_dict[kno_id] = {'name': knowledge_name, 'chunk_size': chunk_size, 'chunk_overlap': chunk_overlap}
        # 获取知识库的根id
        kno_root_id = know_client.knowledge_content_tree(kno_id)['data'][0]['contentCode']
        # 上传文件
        res, filenames = zlpt_upload_files(know_client, doc_dir, kno_id, kno_root_id, chunk_size, chunk_overlap)

        zlpt_wait_learning(know_client, kno_id)
        logger.info("紫鸾平台初始化流程完成")
        return zlpt_user, know_client, kno_id, kno_root_id, filenames
    except Exception as e:
        logger.error(f"紫鸾平台初始化流程失败: {e}")
        raise


def ls_project_init(knowledge_dict, kno_id):
    """
    初始化Label Studio项目：创建项目、标签界面和任务

    Args:
        knowledge_dict (dict): 知识库信息字典
        kno_id (str): 知识库ID
        lzpt_doc_chunk_all (list): 所有文档切片数据

    Returns:
        tuple: 包含Label Studio用户和项目对象的元组
    """
    know_info = knowledge_dict[kno_id]
    name = know_info['name']

    ls_user = login_label_studio()
    project = ls_create_project(ls_user, name)
    return ls_user, project


def label_chunks(retrieve_client, annotator, search_type, kno_id):
    for question_dict in QUESTION_JSON['datas']:
        questions = question_dict['questions']
        for question in questions:
            retrieve_data = retrieve_client.webKnowledgeRetrieve(search_type, question, kno_id)
            chunks = retrieve_data['data']['records']
            label_chunks_by_chunk_id(annotator, question, chunks, 'text')


def zlpt_init_and_ls_label():
    # 初始化完整流程
    logger.info("=== 开始完整的初始化和标注流程 ===")
    try:
        chunk_size = settings.CHUNK_SIZE
        chunk_overlap = settings.CHUNK_OVERLAP
        knowledge_dict = {}

        logger.info(f"配置参数 - CHUNK_SIZE: {chunk_size}, CHUNK_OVERLAP: {chunk_overlap}")

        # 创建知识库和上传文件
        zlpt_user, know_client, kno_id, kno_root_id, filenames = lzpt_init(QUESTION_JSON['doc_name'], chunk_size,
                                                                           chunk_overlap, DOC_DIR, knowledge_dict)

        # 登录ls创建项目、label interface
        ls_user, project = ls_project_init(knowledge_dict, kno_id)

        # 获取知识库下的所有doc_id
        doc_ids = jsonpath.jsonpath(know_client.knowledge_doc_list(kno_id), '$.data.records..docId')
        logger.info(f"发现 {len(doc_ids)} 个文档")

        # 获取所有切片
        zlpt_get_chunk_all = []
        for doc_id in doc_ids:
            doc_name, zlpt_get_doc_chunk_all = zlpt_get_chunk_all_by_doc_id(know_client, doc_id)
            zlpt_get_chunk_all.extend(zlpt_get_doc_chunk_all)
            # 保存到本地
            file_path = os.path.join(ZLPT_CHUNKS_DIR, f"{doc_name}.json")
            save_json_file({"chunks": zlpt_get_doc_chunk_all}, file_path)
            logger.info(f"已保存切片数据到: {file_path}")

        # 创建任务
        logger.info("开始创建Label Studio任务")
        ls_create_tasks(project, zlpt_get_chunk_all)

        # 初始化项目标注器
        logger.info("初始化项目标注器")
        annotator = Annotator(project)

        # 初始化召回器
        logger.info("初始化召回器")
        retrieve_client = Retrieve(zlpt_user)

        # 召回并标注
        logger.info("开始召回并标注")
        label_chunks(retrieve_client, annotator, 'augmentedSearch', kno_id)

        # 查询所有任务，并保存到本地
        logger.info("导出任务数据")
        project_raw_data = project.export_tasks(export_type='JSON')
        file_path = os.path.join(LS_LABELED_CHUNKS_DIR, f"{QUESTION_JSON['doc_name']}.json")
        save_json_file(project_raw_data, file_path)
        logger.info(f"已保存标注数据到: {file_path}")

        logger.info("=== 完整流程执行完成 ===")
        return knowledge_dict, zlpt_user, ls_user, kno_id, project
    except Exception as e:
        logger.error(f"完整流程执行失败: {e}")
        raise
