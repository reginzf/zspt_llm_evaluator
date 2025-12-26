from flask import Blueprint
import os
import logging

from env_config_init import REPORT_PATH
from utils.pub_funs import load_metric_data
from src.flask_funcs.reports.metrics_analyzer import analyze_metrics
from src.flask_funcs.reports.flask_metrics_dashboard_renderer import MetricsDashboardRenderer

# 创建logger
logger = logging.getLogger(__name__)

# 创建蓝图
local_knowledge_bp = Blueprint('local_knowledge', __name__)

# 导入渲染器
from src.flask_funcs.reports.flask_local_knowledge_renderer import LocalKnowledgeRendererFlask

@local_knowledge_bp.route('/local_knowledge/')
def local_knowledge():
    # todo 获取本地知识目录结构，按列表展示
    # 获取在sql ai_local_knowledge表中的数据，和本地目录中第一级目录，按名称匹配，如果有数据库中的数据则展示数据库的，否则展示本地目录的
    pass

