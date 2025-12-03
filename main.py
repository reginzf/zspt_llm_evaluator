from pprint import pprint

from src.core.login import LoginManager
from src.core.api.knowledge_base.retriveve import Retrieve
from src.core.format_func.zl_to_label_studio import retrieve_format_for_label_studio,doc_slices_format_for_label_studio
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
    from src.core.api.knowledge_base.knowledgeBasePage import KnowledgeBasePage
    knowledge_base_page = KnowledgeBasePage(login_manager)
    doc_id = "DOC_d61cdd48e2c845aabcf436bce49eba8d"
    # 获取doc所有的切片
    doc_name, chunk_all = knowledge_base_page.doc_get_chunk_all(doc_id)
    # 转换为label studio格式
    # for ele in chunk_all:
    #     pprint(ele)
    tasks = doc_slices_format_for_label_studio(doc_name, chunk_all)
    print(tasks)

    from model.label_studio.label_studio_client import label_studio_client
    from model.label_studio.task import create_tasks

    project = label_studio_client.get_projects(title='切片项目1')[0]
    create_tasks(project, tasks)


if __name__ == '__main__':
    main()
