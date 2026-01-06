from env_config_init import settings
from src.zlpt.api.knowledge_base import KnowledgeBase, Retrieve, SLICEIDENTIFIER
from src.zlpt.api.project import Project
from src.zlpt.login import LoginManager
import logging

logger = logging.getLogger(__name__)


def login_zlpt():
    """
    登录紫鸾平台并获取认证密钥

    Returns:
        LoginManager: 已登录的登录管理器实例
    """
    logger.info("开始登录紫鸾平台")
    login_manager = LoginManager(settings.ZLPT_BASE_URL)
    # 登陆平台
    try:
        login_manager.login(settings.USERNAME, settings.PASSWORD, settings.DOMAIN)
        login_manager.get_auth_key()
        logger.info("紫鸾平台登录成功")
    except Exception as e:
        logger.error(f"紫鸾平台登录失败: {e}")
        raise e
    # 切换项目
    return login_manager


zlpt_user = login_zlpt()
know_client = KnowledgeBase(zlpt_user)
project_client = Project(zlpt_user)
retrieve_client = Retrieve(zlpt_user)


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
