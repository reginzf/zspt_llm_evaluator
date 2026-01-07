import uuid
import logging
from flask import Blueprint, request, jsonify

from src.flask_funcs.reports.flask_label_studio_env_renderer import LabelStudioEnvRendererFlask
from src.flask_funcs.reports.flask_environment_detail_renderer import EnvironmentDetailRendererFlask
from src.sql_funs.label_studio_crud import LabelStudioCrud
from src.flask_funcs.common_utils import validate_required_fields, execute_with_crud_operation

# 创建logger
logger = logging.getLogger(__name__)
# 创建蓝图
label_studio_env_bp = Blueprint('label_studio_env', __name__)


def _validate_required_fields(data, required_fields):
    """验证必要字段是否存在"""
    for field in required_fields:
        if field not in data:
            return field
    return None


def _execute_with_crud_operation(operation_func, success_message, error_message_prefix):
    """执行数据库操作的通用函数"""
    try:
        with LabelStudioCrud() as env_crud:
            result = operation_func(env_crud)
            if result:
                return jsonify({'success': True, 'message': success_message})
            else:
                return jsonify({'success': False, 'message': f'{error_message_prefix}失败'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'{error_message_prefix}时发生错误: {str(e)}'}), 500


@label_studio_env_bp.route('/label_studio_env/')
def label_studio_env():
    # 获取Label Studio环境列表数据
    try:
        with LabelStudioCrud() as env_crud:
            environment_data = env_crud.label_studio_list()
            environment_data = [env_crud._label_studio_to_json(env) for env in environment_data]
            logger.info(f"成功获取Label Studio环境列表数据，共{len(environment_data)}条记录\n{environment_data}")
    except Exception as e:
        environment_data = []
        logger.error(f"获取Label Studio环境列表数据时发生错误: {str(e)}")

    # 创建HTML渲染器
    renderer = LabelStudioEnvRendererFlask()

    # 渲染模板
    try:
        html_content = renderer.render_label_studio_env_page(environment_data)
    except Exception as e:
        logger.error(f"渲染Label Studio环境页面时发生错误: {str(e)}")
        return "页面渲染错误", 500
    return html_content


@label_studio_env_bp.route('/label_studio_env/create/', methods=['POST'])
def label_studio_env_create():
    data = request.get_json()

    # 检查必要字段（不包括label_studio_id，因为它将自动生成）
    required_fields = ['label_studio_url', 'label_studio_api_key']
    missing_field = validate_required_fields(data, required_fields)
    if missing_field:
        return jsonify({'success': False, 'message': f'缺少必要字段: {missing_field}'}), 400

    # 自动生成label_studio_id
    data['label_studio_id'] = 'ls_' + str(uuid.uuid4())[:8]

    def operation_func():
        with LabelStudioCrud() as env_crud:
            return env_crud.label_studio_create(**data)

    return execute_with_crud_operation(
        operation_func,
        'Label Studio环境创建成功',
        '创建Label Studio环境'
    )


@label_studio_env_bp.route('/label_studio_env/list/', methods=['GET'])
def label_studio_env_list():
    try:
        # 获取查询参数
        query_params = request.args.to_dict()

        # 使用上下文管理器自动处理连接和断开
        with LabelStudioCrud() as env_crud:
            result = env_crud.label_studio_list(**query_params)
            result = [env_crud._label_studio_to_json(env) for env in result]
            return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取Label Studio环境列表时发生错误: {str(e)}'}), 500


@label_studio_env_bp.route('/label_studio_env/update/', methods=['PUT'])
def label_studio_env_update():
    data = request.get_json()
    # 检查必要字段
    if not data:
        return jsonify({'success': False, 'message': '请求数据不能为空'}), 400
    # 检查必要字段
    required_fields = ['label_studio_id', 'label_studio_url', 'label_studio_api_key']
    missing_field = validate_required_fields(data, required_fields)
    if missing_field:
        return jsonify({'success': False, 'message': f'缺少必要字段: {missing_field}'}), 400
    label_studio_id = data.pop('label_studio_id')

    def operation_func():
        with LabelStudioCrud() as env_crud:
            return env_crud.label_studio_update(label_studio_id, **data)

    return execute_with_crud_operation(
        operation_func,
        'Label Studio环境更新成功',
        '更新Label Studio环境'
    )


@label_studio_env_bp.route('/label_studio_env/delete/', methods=['DELETE'])
def label_studio_env_delete():
    data = request.get_json()

    # 检查必要字段
    if not data or 'label_studio_id' not in data:
        return jsonify({'success': False, 'message': '缺少必要字段: label_studio_id'}), 400

    def operation_func():
        with LabelStudioCrud() as env_crud:
            return env_crud.label_studio_delete(label_studio_id=data['label_studio_id'])

    return execute_with_crud_operation(
        operation_func,
        'Label Studio环境删除成功',
        '删除Label Studio环境'
    )
