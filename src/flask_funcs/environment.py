from flask import Blueprint, request, jsonify
from src.sql_funs.environment_crud import Environment_Crud

# 创建蓝图
environment_bp = Blueprint('environment', __name__)


@environment_bp.route('/environment/create/', methods=['POST'])
def environment_create():
    """创建环境信息"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求数据为空"}), 400

        # 使用Environment_Crud创建环境信息
        env_crud = Environment_Crud('10.210.2.223', 5432, 'label_studio', 'labelstudio', 'Labelstudio123')
        env_crud.connect()
        
        result = env_crud.environment_create(**data)
        env_crud.disconnect()
        
        if result:
            return jsonify({"message": "环境信息添加成功"}), 200
        else:
            return jsonify({"error": "环境信息添加失败"}), 400
    except Exception as e:
        return jsonify({"error": f"创建环境信息时发生错误: {str(e)}"}), 500


@environment_bp.route('/environment/list/', methods=['GET'])
def environment_list():
    """获取环境信息列表"""
    try:
        # 获取查询参数
        query_params = request.args.to_dict()
        
        # 使用Environment_Crud查询环境信息
        env_crud = Environment_Crud('10.210.2.223', 5432, 'label_studio', 'labelstudio', 'Labelstudio123')
        env_crud.connect()
        
        result = env_crud.environment_list(**query_params) if query_params else env_crud.environment_list()
        env_crud.disconnect()
        
        return jsonify({"data": result}), 200
    except Exception as e:
        return jsonify({"error": f"获取环境信息列表时发生错误: {str(e)}"}), 500


@environment_bp.route('/environment/update/<string:zlpt_base_id>', methods=['PUT'])
def environment_update(zlpt_base_id):
    """更新环境信息"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求数据为空"}), 400

        # 使用Environment_Crud更新环境信息
        env_crud = Environment_Crud('10.210.2.223', 5432, 'label_studio', 'labelstudio', 'Labelstudio123')
        env_crud.connect()
        
        result = env_crud.environment_update(zlpt_base_id=zlpt_base_id, **data)
        env_crud.disconnect()
        
        if result:
            return jsonify({"message": "环境信息更新成功"}), 200
        else:
            return jsonify({"error": "环境信息更新失败"}), 400
    except Exception as e:
        return jsonify({"error": f"更新环境信息时发生错误: {str(e)}"}), 500


@environment_bp.route('/environment/delete/', methods=['DELETE'])
def environment_delete():
    """删除环境信息"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求数据为空"}), 400

        # 使用Environment_Crud删除环境信息
        env_crud = Environment_Crud('10.210.2.223', 5432, 'label_studio', 'labelstudio', 'Labelstudio123')
        env_crud.connect()
        
        result = env_crud.environment_delete(**data)
        env_crud.disconnect()
        
        if result:
            return jsonify({"message": "环境信息删除成功"}), 200
        else:
            return jsonify({"error": "环境信息删除失败"}), 400
    except Exception as e:
        return jsonify({"error": f"删除环境信息时发生错误: {str(e)}"}), 500