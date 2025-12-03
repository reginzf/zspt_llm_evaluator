from src.core.login import LoginManager
from src.core.api.knowledge_base.retriveve import Retrieve
from src.core.format_func.zl_to_label_studio import retrieve_format_for_label_studio
from env_config_init import settings

BASE_URL = 'https://10.220.49.200'
USERNAME = "nrgtest"
PASSWORD = "Admin@123"
DOMAIN = "default"


def main():
    login_manager = LoginManager(settings.ZLPT_BASE_URL)
    login_manager.login(settings.USERNAME, settings.PASSWORD, settings.DOMAIN)
    login_manager.get_auth_key()
    retrieve_client = Retrieve(login_manager)
    res = retrieve_client.webKnowledgeRetrieve('vectorSearch', 'ospf中有哪些类型的报文',
                                               'KLB_f1b895e57a3e4851939483e11f84ee6a')
    tasks = retrieve_format_for_label_studio(res['data']['records'])

    from model.label_studio.label_studio_client import label_studio_client
    from model.label_studio.task import create_tasks
    project = label_studio_client.get_projects(title='切片项目1')[0]
    create_tasks(project, tasks)


if __name__ == '__main__':
    main()
