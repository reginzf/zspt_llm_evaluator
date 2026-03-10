import uuid
import logging
from flask import Blueprint, request, jsonify
from env_config_init import settings
from src.flask_funcs.reports.flask_environment_renderer import EnvironmentRendererFlask
from src.flask_funcs.reports.flask_environment_detail_renderer import EnvironmentDetailRendererFlask
from src.sql_funs.environment_crud import Environment_Crud
from src.flask_funcs.common_utils import validate_required_fields, execute_with_crud_operation
from src.zlpt.login import LoginManager

# 创建logger
logger = logging.getLogger(__name__)
# 创建蓝图
environment_bp = Blueprint('environment', __name__)


def _validate_required_fields(data, required_fields):
    """验证必要字段是否存在"""
    for field in required_fields:
        if field not in data:
            return field
    return None


def _execute_with_crud_operation(operation_func, success_message, error_message_prefix):
    """执行数据库操作的通用函数"""
    try:
        with Environment_Crud() as env_crud:
            result = operation_func(env_crud)
            if result:
                return jsonify({'success': True, 'message': success_message})
            else:
                return jsonify({'success': False, 'message': f'{error_message_prefix}失败'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'{error_message_prefix}时发生错误: {str(e)}'}), 500


@environment_bp.route('/environment/')
def environment():
    # 获取环境列表数据
    try:
        with Environment_Crud() as env_crud:
            environment_data = env_crud.environment_list()
            environment_data = [env_crud._environment_list_to_json(env) for env in environment_data]
            logger.info(f"成功获取环境列表数据，共{len(environment_data)}条记录\n{environment_data}")
        current_environment_id = ""  # 默认当前环境ID为空，可以根据需要设置
    except Exception as e:
        environment_data = []
        current_environment_id = ""
        logger.error(f"获取环境列表数据时发生错误: {str(e)}")

    # 创建HTML渲染器
    renderer = EnvironmentRendererFlask()

    # 渲染模板
    try:
        html_content = renderer.render_environment_page(environment_data, current_environment_id)
    except Exception as e:
        logger.error(f"渲染环境页面时发生错误: {str(e)}")
        return "页面渲染错误", 500

    return html_content


@environment_bp.route('/environment/create/', methods=['POST'])
@environment_bp.route('/api/environment/create/', methods=['POST'])
def environment_create():
    data = request.get_json()

    # 检查必要字段（不包括zlpt_base_id，因为它将自动生成）
    required_fields = ['zlpt_name', 'project_name', 'zlpt_base_url', 'username', 'password']
    missing_field = validate_required_fields(data, required_fields)
    if missing_field:
        return jsonify({'success': False, 'message': f'缺少必要字段: {missing_field}'}), 400

    # 自动生成zlpt_base_id
    data['zlpt_base_id'] = 'env_' + str(uuid.uuid4())[:8]
    # 补全加密配置
    data['key1'] = settings.KEY1
    data['key2_add'] = settings.KEY2_ADD
    data['pk'] = settings.PK
    # 尝试登录
    zlpt_user = LoginManager(
        data['zlpt_base_url'],
        data['username'],
        data['password'],
        data['domain'],
        data['key1'],
        data['key2_add'],
        data['pk']
    )
    # 获取用户ID和项目ID
    user_id,project_id = zlpt_user.login_unsafe()
    data['project_id'] = project_id
    # 写入数据库
    def operation_func():
        with Environment_Crud() as env_crud:
            return env_crud.environment_create(**data)

    return execute_with_crud_operation(
        operation_func,
        '环境创建成功',
        '创建环境',
        logger
    )


@environment_bp.route('/environment/list/', methods=['GET'])
@environment_bp.route('/api/environment/list/', methods=['GET'])
def environment_list():
    try:
        # 获取查询参数
        query_params = request.args.to_dict()

        # 使用上下文管理器自动处理连接和断开
        with Environment_Crud() as env_crud:
            result = env_crud.environment_list(**query_params)
            result = [env_crud._environment_list_to_json(env) for env in result]
            return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取环境列表时发生错误: {str(e)}'}), 500


@environment_bp.route('/environment/update/', methods=['PUT'])
@environment_bp.route('/api/environment/update/', methods=['PUT'])
def environment_update():
    data = request.get_json()
    # 检查必要字段
    if not data:
        return jsonify({'success': False, 'message': '请求数据不能为空'}), 400
    # 检查必要字段
    required_fields = ['zlpt_base_id', 'zlpt_name', 'project_name', 'zlpt_base_url', 'username', 'password']
    missing_field = validate_required_fields(data, required_fields)
    if missing_field:
        return jsonify({'success': False, 'message': f'缺少必要字段: {missing_field}'}), 400
    zlpt_base_id = data.pop('zlpt_base_id')

    def operation_func():
        with Environment_Crud() as env_crud:
            return env_crud.environment_update(zlpt_base_id, **data)

    return execute_with_crud_operation(
        operation_func,
        '环境更新成功',
        '更新环境',
        logger
    )


@environment_bp.route('/environment/delete/', methods=['DELETE'])
@environment_bp.route('/api/environment/delete/', methods=['DELETE'])
def environment_delete():
    data = request.get_json()

    # 检查必要字段
    if not data or 'zlpt_base_id' not in data:
        return jsonify({'success': False, 'message': '缺少必要字段: zlpt_base_id'}), 400

    def operation_func():
        with Environment_Crud() as env_crud:
            return env_crud.environment_delete(zlpt_base_id=data['zlpt_base_id'])

    return execute_with_crud_operation(
        operation_func,
        '环境删除成功',
        '删除环境',
        logger
    )


@environment_bp.route('/environment_detail/', methods=['GET'])
def environment_detail_page():
    # 获取查询参数中的zlpt_base_id
    zlpt_base_id = request.args.get('zlpt_base_id')

    if not zlpt_base_id:
        return "缺少zlpt_base_id参数", 400

    try:
        # 获取环境详情
        with Environment_Crud() as env_crud:
            environment_data = env_crud.environment_list(zlpt_base_id=zlpt_base_id)

            if not environment_data:
                return "未找到指定的环境", 404

            environment_detail = environment_data[0]  # 获取环境详情
            logger.info(f"{environment_detail}")
            # 根据zlpt_base_id获取关联的知识库列表

            knowledge_base_list = env_crud.get_knowledge_base(zlpt_base_id=environment_detail[0])
            knowledge_base_list = [env_crud._knowledge_base_to_json(kb) for kb in knowledge_base_list]
            # 过滤出与当前环境关联的知识库
            logger.info(f"成功获取环境列表数据，共{len(knowledge_base_list)}条记录")

        # 创建HTML渲染器
        renderer = EnvironmentDetailRendererFlask()

        # 渲染模板
        html_content = renderer.render_environment_detail_page(environment_detail, knowledge_base_list)

        return html_content

    except Exception as e:
        logger.error(f"渲染环境详情页面时发生错误: {str(e)}")
        return "页面渲染错误", 500


@environment_bp.route('/environment_detail_list', methods=['POST'])
@environment_bp.route('/api/environment_detail_list', methods=['POST'])
def environment_detail_list():
    try:
        data = request.get_json()  # 至少要包含zlpt_base_id，可选包含search_field和search_value
        logger.info(f"接收到环境详情列表请求，数据: {data}")

        if not data or 'zlpt_id' not in data:
            logger.warning("请求数据中缺少zlpt_id字段")
            return jsonify({'success': False, 'message': '缺少必要字段: zlpt_id'}), 400

        zlpt_id = data['zlpt_id']
        logger.info(f"获取环境ID: {zlpt_id}的知识库列表")

        with Environment_Crud() as env_crud:
            # 如果提供了搜索字段和值，则进行搜索
            if data and 'search_field' in data and 'search_value' in data:
                search_field = data['search_field']
                search_value = data['search_value']

                logger.info(f"执行搜索查询，搜索字段: {search_field}，搜索值: {search_value}")
                # 根据搜索字段构建查询条件
                search_params = {
                    'zlpt_id': zlpt_id,
                    f'{search_field}': search_value  # 使用模糊匹配
                }

                result = env_crud.get_knowledge_base(**search_params)
                logger.info(f"搜索查询完成，返回{len(result)}条记录")
            else:
                # 没有搜索条件时，只按zlpt_base_id查询
                logger.info("执行无搜索条件的查询")
                result = env_crud.get_knowledge_base(zlpt_id=zlpt_id)
                logger.info(f"查询完成，返回{len(result)}条记录")

            result = [env_crud._knowledge_base_to_json(kb) for kb in result]
            logger.info(f"成功获取环境详情列表数据，共{len(result)}条记录")
            return jsonify({'success': True, 'data': result})
    except Exception as e:
        logger.error(f"获取环境详情列表时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'获取环境列表时发生错误: {str(e)}'}), 500
