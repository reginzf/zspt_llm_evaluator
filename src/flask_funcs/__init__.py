"""
Flask功能模块包
"""
from .home import home_bp
from .environment import environment_bp
from .report_list import report_list_bp
from .static_routes import static_bp
from .knowledge_doc import knowledge_doc_bp
from .local_knowledge import local_knowledge_bp
from .knowledge_base import knowledge_base_bp
from .local_knowledge_detail import local_knowledge_detail_bp
from .label_studio_env import label_studio_env_bp
from .local_knowledge_question import local_knowledge_question_bp
from .common_utils import *