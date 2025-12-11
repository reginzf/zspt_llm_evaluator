import os.path
import jsonpath

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
from utils.pub_funs import save_chunk_all_to_json, save_json_file

annotation_generator = AnnotationGenerator()
label_generator = LabelStudioXMLGenerator(grid_columns=2)


def login_zlpt():
    """
    登录紫鸾平台并获取认证密钥

    Returns:
        LoginManager: 已登录的登录管理器实例
    """
    login_manager = LoginManager(settings.ZLPT_BASE_URL)
    login_manager.login(settings.USERNAME, settings.PASSWORD, settings.DOMAIN)
    login_manager.get_auth_key()
    return login_manager


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
    know_client.knowledge_addOrUpdate(name)
    return name


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
    data_ids = []
    filenames = []
    for file in os.listdir(doc_dir):
        file_path = os.path.join(doc_dir, file)
        if os.path.isfile(file_path):
            res = know_client.upload_attachment(file_path, content_code)
            data_ids.append(res['data'])
            filenames.append(file)

    res = know_client.doc_addOrUpdate(kno_id, content_code, data_ids, chunk_size, chunk_overlap, **kwargs)
    return res, filenames


def zlpt_get_chunk_all_by_doc_id(know_client, doc_id):
    """
      通过文档ID获取对应文档的名称和所有切片

      Args:
          know_client: 知识库客户端实例
          doc_id (str): 文档ID

      Returns:
          tuple: 包含文档名称和所有切片的元组
      """
    doc_name, chunk_all = know_client.doc_get_chunk_all(doc_id)
    return doc_name, chunk_all


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
    msgs = set(jsonpath.jsonpath(know_client.knowledge_doc_list(kno_id), '$.data.records..msg'))
    assert len(msgs) == 1 and msgs.pop() == '学习成功'


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
    label_config = LabelStudioXMLGenerator().generate_from_json(QUESTION_JSON)
    project = ls_user.create_project(
        title=title,
        description=description,
        label_config=label_config,
        show_instruction=True,
        enable_empty_annotation=False,
    )
    return project


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
    for chunk in chunks:
        target_filter = annotator.generate_filter_item(chunk['chunk_id'], t_filter, operator="equal")
        target_task = annotator.get_task_by_filter([target_filter])[0]
        # 创建标注
        annotation_data = [annotation_generator.generate_choice_annotation(q_type, to_name, [question])]
        annotate_to_create = AnnotateToCreate(
            annotation_data=annotation_data,
            lead_time=35.0,
            merge_existing=True  # 启用合并功能
        )
        result = annotator.task_annotate_create(target_task, annotate_to_create)
        print(result)


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
    return zlpt_user, know_client, kno_id, kno_root_id, filenames


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
    chunk_size = settings.CHUNK_SIZE
    chunk_overlap = settings.CHUNK_OVERLAP
    knowledge_dict = {}

    # 创建知识库和上传文件
    zlpt_user, know_client, kno_id, kno_root_id, filenames = lzpt_init(QUESTION_JSON['doc_name'], chunk_size,
                                                                       chunk_overlap, DOC_DIR, knowledge_dict)

    # 登录ls创建项目、label interface
    ls_user, project = ls_project_init(knowledge_dict, kno_id)

    # 获取知识库下的所有doc_id
    doc_ids = jsonpath.jsonpath(know_client.knowledge_doc_list(kno_id), '$.data.records..docId')
    # 获取所有切片
    zlpt_get_chunk_all = []
    for doc_id in doc_ids:
        doc_name, zlpt_get_doc_chunk_all = zlpt_get_chunk_all_by_doc_id(know_client, doc_id)
        zlpt_get_chunk_all.extend(zlpt_get_doc_chunk_all)
        # 保存到本地
        file_path = os.path.join(ZLPT_CHUNKS_DIR, f"{doc_name}.json")
        save_json_file({"chunks": zlpt_get_doc_chunk_all}, file_path)

    # 创建任务
    ls_create_tasks(project, zlpt_get_chunk_all)
    # 初始化项目标注器
    annotator = Annotator(project)
    # 初始化召回器
    retrieve_client = Retrieve(zlpt_user)
    # 召回并标注
    label_chunks(retrieve_client, annotator, 'augmentedSearch', kno_id)
    # 查询所有任务，并保存到本地
    project_raw_data = project.export_tasks(export_type='JSON')
    file_path = os.path.join(LS_LABELED_CHUNKS_DIR, f"{QUESTION_JSON['doc_name']}.json")
    save_json_file(project_raw_data, file_path)
    return knowledge_dict, zlpt_user, ls_user, kno_id, project
