import uuid
import logging
from flask import Blueprint, request, jsonify

from src.flask_funcs.reports.flask_environment_renderer import EnvironmentRendererFlask
from src.flask_funcs.reports.flask_environment_detail_renderer import EnvironmentDetailRendererFlask
from src.sql_funs.environment_crud import Environment_Crud
from src.sql_funs.local_knowledge_crud import LocalKnowledgeCrud


# 创建logger
logger = logging.getLogger(__name__)
# 创建蓝图
environment_bp = Blueprint('environment', __name__)


@environment_bp.route('/environment/')
def environment():
    # 获取环境列表数据
    try:
        with Environment_Crud() as env_crud:
            environment_data = env_crud.environment_list()
            logger.info(f"成功获取环境列表数据，共{len(environment_data)}条记录")
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
def environment_create():
    data = request.get_json()

    # 检查必要字段（不包括zlpt_base_id，因为它将自动生成）
    required_fields = ['zlpt_name', 'zlpt_base_url', 'username', 'password']
    for field in required_fields:
        if field not in data:
            return jsonify({'success': False, 'message': f'缺少必要字段: {field}'}), 400

    # 自动生成zlpt_base_id
    data['zlpt_base_id'] = 'env_' + str(uuid.uuid4())[:8]

    try:
        with Environment_Crud() as env_crud:
            result = env_crud.environment_create(**data)
            if result:
                return jsonify({'success': True, 'message': '环境创建成功'})
            else:
                return jsonify({'success': False, 'message': '环境创建失败'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'创建环境时发生错误: {str(e)}'}), 500


@environment_bp.route('/environment/list/', methods=['GET'])
def environment_list():
    try:
        # 获取查询参数
        query_params = request.args.to_dict()

        # 使用上下文管理器自动处理连接和断开
        with Environment_Crud() as env_crud:
            result = env_crud.environment_list(**query_params)
            return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取环境列表时发生错误: {str(e)}'}), 500


@environment_bp.route('/environment/update/', methods=['PUT'])
def environment_update():
    data = request.get_json()
    # 检查必要字段
    if not data:
        return jsonify({'success': False, 'message': '请求数据不能为空'}), 400
    # 检查必要字段
    required_fields = ['zlpt_base_id', 'zlpt_name', 'zlpt_base_url', 'username', 'password']
    for field in required_fields:
        if field not in data:
            return jsonify({'success': False, 'message': f'缺少必要字段: {field}'}), 400
    zlpt_base_id = data.pop('zlpt_base_id')
    try:
        # 使用上下文管理器自动处理连接和断开
        with Environment_Crud() as env_crud:
            result = env_crud.environment_update(zlpt_base_id, **data)
            if result:
                return jsonify({'success': True, 'message': '环境更新成功'})
            else:
                return jsonify({'success': False, 'message': '环境更新失败'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'更新环境时发生错误: {str(e)}'}), 500


@environment_bp.route('/environment/delete/', methods=['DELETE'])
def environment_delete():
    data = request.get_json()

    # 检查必要字段
    if not data or 'zlpt_base_id' not in data:
        return jsonify({'success': False, 'message': '缺少必要字段: zlpt_base_id'}), 400

    try:
        # 使用上下文管理器自动处理连接和断开
        with Environment_Crud() as env_crud:
            result = env_crud.environment_delete(zlpt_base_id=data['zlpt_base_id'])
            if result:
                return jsonify({'success': True, 'message': '环境删除成功'})
            else:
                return jsonify({'success': False, 'message': '环境删除失败'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'删除环境时发生错误: {str(e)}'}), 500


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
        with LocalKnowledgeCrud() as knowledge_crud:
            knowledge_base_list = knowledge_crud.get_knowledge_base(zlpt_id=environment_detail[0])
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