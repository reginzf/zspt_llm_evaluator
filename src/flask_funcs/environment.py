from flask import Blueprint, request, jsonify
from src.sql_funs.environment_crud import Environment_Crud
import uuid

# 创建蓝图
environment_bp = Blueprint('environment', __name__)


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
