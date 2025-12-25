from flask import Blueprint, request, jsonify
from src.sql_funs.knowledge_crud import KnowledgeCrud
import uuid
from env_config_init import settings
# 创建蓝图
knowledge_doc_bp = Blueprint('knowledge_doc', __name__)



@knowledge_doc_bp.route('/knowledge_doc/list', methods=['GET'])
def knowledge_doc_local_list():
    # 查看本地目录下文件夹
    pass

