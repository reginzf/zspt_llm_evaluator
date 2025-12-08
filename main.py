import os.path
import time

from env_config_init import settings
from src.core.login import LoginManager
from src.core.api.knowledge_base.retriveve import Retrieve
from src.core.api.knowledge_base.knowledgeBase import KnowledgeBase
from src.core.format_func.zl_to_label_studio import doc_slices_format_for_label_studio
from src.core.questions import get_question_type_and_label
from model.label_studio.task import create_tasks
from model.label_studio.label_studio_client import label_studio_client
from model.label_studio.labels import LabelStudioXMLGenerator
from model.label_studio.annotator import Annotator, AnnotationGenerator
from utils.pub_funs import load_json_file, save_xml_file

BASE_URL = 'https://10.220.49.200'
USERNAME = "nrgtest"
PASSWORD = "Admin@123"
DOMAIN = "default"

QUESTION_JSON = load_json_file(r'D:\pyworkplace\git_place\ai-ken\tests\ospf\question.json')
annotation_generator = AnnotationGenerator()


def login_zlpt():
    login_manager = LoginManager(settings.ZLPT_BASE_URL)
    login_manager.login(settings.USERNAME, settings.PASSWORD, settings.DOMAIN)
    login_manager.get_auth_key()
    return login_manager


def login_label_studio():
    return label_studio_client


def zlpt_create_knowledge_base(know_client: KnowledgeBase, doc_name, chunk_size, chunk_overlap):
    name = f'{doc_name}_{chunk_size}_{chunk_overlap}'
    know_client.knowledge_addOrUpdate(name)
    return name


def zlpt_upload_files(know_client: KnowledgeBase, filepath, kno_id, content_code, chunk_size, chunk_overlap, **kwargs):
    data_id = know_client.upload_attachment(filepath, content_code)['data']
    res = know_client.doc_addOrUpdate(kno_id, content_code, [data_id], chunk_size, chunk_overlap, **kwargs)
    return res, data_id


def lzpt_get_chunk_all_by_docId(know_client, doc_id):
    # 通过doc_id获取对应文档的名称和所有切片
    doc_name, chunk_all = know_client.doc_get_chunk_all(doc_id)
    return doc_name, chunk_all


def zlpt_get_chunk_by_question(zlpt_user, kno_id, question):
    retrieve = Retrieve(zlpt_user)
    retrieve_data = retrieve.webKnowledgeRetrieve('augmentedSearch', question, kno_id)
    return retrieve_data


def ls_create_project(ls_user, title, description=''):
    # 返回label studio的Project对象
    label_config = LabelStudioXMLGenerator().generate_from_json(QUESTION_JSON)
    project = ls_user.create_project(
        title=title,
        description=description,
        label_config=label_config,
        show_instruction=True,
        enable_empty_annotation=False,
    )
    return project

def ls_create_label_interface(project,question_json):
    from label_studio_sdk._legacy import Project
    project:Project
    generator = LabelStudioXMLGenerator(grid_columns=2, gap="10px")
    # 示例：从文件加载
    xml_content = generator.generate_from_json(QUESTION_JSON)

def ls_create_tasks(project, chunk_all):
    # 转换为ls的格式
    tasks = doc_slices_format_for_label_studio(chunk_all)
    # 在ls上创建任务
    res = create_tasks(project, tasks)
    return res  # [task_id1,task_id2...]


def label_chunks_by_chunk_id(project, question, chunks):
    # 对返回的切片进行标注
    # 获取问题的类型和标签
    q_type, q_label = get_question_type_and_label
    t_filter = "filter:tasks:data.chunk_id"

    annotator = Annotator(project)
    for chunk in chunks:
        target_filter = annotator.generate_filter_item(chunk['chunk_id'], t_filter, operator="equal")
        annotation_generator.generate_choice_annotation(q_type, 'text')


def lzpt_init(name, chunk_size, chunk_overlap, target_path, knowledge_dict):
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
    zlpt_upload_files(know_client, target_path, kno_id, kno_root_id, chunk_size, chunk_overlap)
    doc_name = os.path.basename(target_path).split('.')[0]
    print(f'kno_id : {kno_id}')
    doc_id = know_client.knowledge_doc_list(kno_id, doc_name)['data']['records'][0]['docId']

    return zlpt_user, kno_id, kno_root_id, doc_id


def main():
    name, chunk_size, chunk_overlap = 'test', 500, 10
    target_path = r'D:\pyworkplace\git_place\ai-ken\tests\ospf\context\OSPFv2.txt'
    # knowledge_dict = {}
    #
    # zlpt_user, kno_id, kno_root_id, doc_id = lzpt_init(name, chunk_size, chunk_overlap, target_path,
    #                                                    knowledge_dict)
    # know_client = KnowledgeBase(zlpt_user)

    ls_user = login_label_studio()
    # 将切片全部创建到ls上
    know_client = KnowledgeBase(login_zlpt())
    kno_id = "KLB_07d5af8a8e1244af9fce796b5a627a1b"
    doc_id = "DOC_03968fee8f9f4e5b8a2a9c411c3ec537"
    project = ls_create_project(ls_user, f'{name}_{chunk_size}_{chunk_overlap}')
    # 为project创建label
    pass
    # 获取切片
    lzpt_get_doc_chunk_all = lzpt_get_chunk_all_by_docId(know_client, doc_id)
    # 创建任务
    ls_create_tasks(project, lzpt_get_doc_chunk_all)


if __name__ == '__main__':
    main()
