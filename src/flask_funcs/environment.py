from flask import Blueprint, render_template
from src.sql_funs.environment_crud import Environment_Crud
from env_config_init import REPORT_PATH

# 创建蓝图
home_bp = Blueprint('app', __name__)


@home_bp.route('/environment/create/', methods=['POST'])
def environment_create():
    with Environment_Crud() as crud:
        crud.create_environment()