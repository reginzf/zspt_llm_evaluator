from pprint import pprint

from label_studio_sdk.converter.imports.label_config import generate_label_config
from openai import project
from openpyxl.styles.builtins import title

from src.core.login import LoginManager
from src.core.api.knowledge_base.retriveve import Retrieve
from src.core.format_func.zl_to_label_studio import retrieve_format_for_label_studio, doc_slices_format_for_label_studio
from env_config_init import settings

BASE_URL = 'https://10.220.49.200'
USERNAME = "nrgtest"
PASSWORD = "Admin@123"
DOMAIN = "default"


def main():
    # 登录紫光云平台
    login_manager = LoginManager(settings.ZLPT_BASE_URL)
    login_manager.login(settings.USERNAME, settings.PASSWORD, settings.DOMAIN)
    login_manager.get_auth_key()
    # 获取指定doc下所有的切片
    from src.core.api.knowledge_base.knowledgeBase import KnowledgeBase
    knowledge_base_page = KnowledgeBase(login_manager)
    kno_id = 'KLB_869cb0ded2c64362a2b5ce722d2e91cf'
    doc_id = "DOC_cef4a72fac2045bc9c4c69de164be510"
    # 获取doc所有的切片,转换为label_studio的格式
    doc_name, chunk_all = knowledge_base_page.doc_get_chunk_all(doc_id)
    tasks = doc_slices_format_for_label_studio(doc_name, chunk_all)

    # 登录label studio
    from model.label_studio.label_studio_client import label_studio_client
    from model.label_studio.task import create_tasks
    # 创建任务
    # 根据问题配置文件创建标签
    from model.label_studio.labels import LabelStudioXMLGenerator
    from utils.pub_funs import load_json_file
    question_json = load_json_file(r'D:\pyworkplace\git_place\ai-ken\tests\ospf\question.json')
    # label_config = LabelStudioXMLGenerator().generate_from_json(question_json)
    # project = label_studio_client.create_project(
    #     title='ospf_chunk_test',
    #     description="自动标注",
    #     label_config=label_config,
    #     show_instruction=True,
    #     enable_empty_annotation=False,
    # )
    # create_tasks(project, tasks)
    project = label_studio_client.get_projects(title='ospf_chunk_test')[0]
    # 从紫鸾平台获取召回数据
    retrieve = Retrieve(login_manager)
    # 从question.json文件中获取问题和配置
    from src.core.questions import get_questions
    questions = get_questions(question_json, 'factual')
    # 按问题进行召回，并进行标注
    for question in questions['questions']:
        recall_data = retrieve.webKnowledgeRetrieve('augmentedSearch', question, kno_id)
        # 获取chunk_id，并执行标注
        for chunk_id in recall_data['data']['chunk_ids']:
            pass


if __name__ == '__main__':
    main()
