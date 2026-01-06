from pathlib import Path

from flask import Blueprint, request, jsonify, render_template_string
import os
import logging
import uuid
from env_config_init import settings
from src.sql_funs.local_knowledge_crud import LocalKnowledgeCrud
from src.sql_funs.environment_crud import Environment_Crud
from src.flask_funcs.reports.flask_local_knowledge_renderer import LocalKnowledgeRendererFlask
from src.flask_funcs.common_utils import validate_required_fields, get_knowledge_base_binding_info, handle_file_upload, \
    generate_unique_id

# 创建logger
logger = logging.getLogger(__name__)

# 创建蓝图
local_knowledge_detail_bp = Blueprint('local_knowledge_detail', __name__)




@local_knowledge_detail_bp.route('/local_knowledge_detail/<kno_id>/<kno_name>')
def local_knowledge_detail(kno_id, kno_name):
    """获取特定本地知识的详细信息页面"""
    try:
        with LocalKnowledgeCrud() as crud:
            # 获取本地知识详情
            knowledge_list = crud.get_local_knowledge(kno_id=kno_id)
            logger.info(f"获取本地知识详情: {knowledge_list}")
            if not knowledge_list or len(knowledge_list) == 0:
                return "未找到知识库信息", 404

            knowledge_detail = knowledge_list[0]  # 获取第一个结果
            # 将元组转换为字典格式，以便模板使用
            knowledge_detail_dict = {
                "kno_id": knowledge_detail[1],  # kno_id 是第二个字段
                "kno_name": knowledge_detail[2],  # kno_name 是第三个字段
                "kno_describe": knowledge_detail[3],  # kno_describe 是第四个字段
                "kno_path": knowledge_detail[4],  # kno_path 是第五个字段
                "ls_status": knowledge_detail[5],  # ls_status 是第六个字段
                "created_at": knowledge_detail[6],  # created_at 是第七个字段
                "updated_at": knowledge_detail[7]  # updated_at 是第八个字段
            }

            # 渲染新的详情页面模板
            from flask import render_template
            import os
            css_path = f"/static/css/local_knowledge.css?version={os.urandom(4).hex()}"
            detail_css_path = f"/static/css/local_knowledge_detail.css?version={os.urandom(4).hex()}"
            js_url = f"/static/js/local_knowledge.js?version={os.urandom(4).hex()}"
            detail_js_url = f"/static/js/local_knowledge_detail.js?version={os.urandom(4).hex()}"

            return render_template('local_knowledge_detail.html',
                                   knowledge_detail=knowledge_detail_dict,
                                   title=f'{knowledge_detail_dict["kno_name"]} - 本地知识库详情',
                                   heading=f'{knowledge_detail_dict["kno_name"]} 详情',
                                   css_path=css_path,
                                   detail_css_path=detail_css_path,
                                   js_url=js_url,
                                   detail_js_url=detail_js_url)

    except Exception as e:
        logger.error(f"获取本地知识详情时发生错误: {str(e)}")
        return "页面加载错误", 500


@local_knowledge_detail_bp.route('/api/local_knowledge_detail', methods=['POST'])
def api_local_knowledge_detail():
    data = request.get_json()
    kno_id = data.get('kno_id')
    kno_name = data.get('kno_name')
    """API接口：获取特定本地知识的详细信息"""
    try:
        with LocalKnowledgeCrud() as crud:
            # 获取本地知识列表详情（从ai_local_knowledge_list表）
            # 获取所有知识列表记录
            all_knowledge_list_records = crud.get_local_knowledge_list(kno_id=kno_id)
            logger.info(f"获取本地知识列表详情: {all_knowledge_list_records}")

            # 首先尝试使用kno_id过滤
            filtered_knowledge_list = []
            if all_knowledge_list_records:
                for record in all_knowledge_list_records:
                    # record格式: (id, knol_id, knol_name, knol_describe, knol_path, ls_status, created_at, updated_at, kno_id)
                    if len(record) > 8 and record[8] == kno_id:  # record[8] 是kno_id字段
                        # 重构数据格式，使其包含所需字段
                        filtered_record = {
                            "knol_id": record[1],  # knol_id
                            "kno_name": record[2],  # knol_name
                            "kno_describe": record[3],  # knol_describe
                            "knol_path": record[4],  # knol_path
                            "ls_status": record[5],  # ls_status
                            "created_at": record[6],  # created_at
                            "updated_at": record[7],  # updated_at
                            "kno_id": record[8]
                        }
                        filtered_knowledge_list.append(filtered_record)

            # 如果没找到记录，尝试使用kno_name来查找对应的kno_id
            if not filtered_knowledge_list:
                # 先通过kno_name在ai_local_knowledge表中查找真正的kno_id
                knowledge_records = crud.get_local_knowledge(kno_name=kno_name)
                if knowledge_records:
                    # 获取正确的kno_id
                    correct_kno_id = knowledge_records[0][1]  # 第二个字段是kno_id
                    logger.info(f"使用kno_name '{kno_name}'查找到正确的kno_id: {correct_kno_id}")
                    # 再次尝试过滤
                    for record in all_knowledge_list_records:
                        if len(record) > 8 and record[8] == correct_kno_id:
                            # 重构数据格式
                            filtered_record = {
                                "knol_id": record[1],  # knol_id
                                "kno_name": record[2],  # knol_name
                                "kno_describe": record[3],  # knol_describe
                                "knol_path": record[4],  # knol_path
                                "ls_status": record[5],  # ls_status
                                "created_at": record[6],  # created_at
                                "updated_at": record[7],  # updated_at
                                "kno_id": record[8]
                            }
                            filtered_knowledge_list.append(filtered_record)

            # 获取本地目录指定文件夹的文件名称
            folder_path = Path(settings.KNOWLEDGE_LOCAL_PATH) / kno_name
            local_files = []
            if os.path.exists(folder_path) and os.path.isdir(folder_path):
                for item in os.listdir(folder_path):
                    local_file = os.path.join(folder_path, item)
                    local_files.append(local_file)
                logger.info(f"获取本地目录下文件: {local_files}")
    except Exception as e:
        logger.error(f"获取本地知识详情时发生错误: {str(e)}")
        return jsonify({"error": "页面加载错误"}), 500

    # 直接返回过滤后的知识列表详情，因为这是前端需要的数据格式
    return jsonify(filtered_knowledge_list)


@local_knowledge_detail_bp.route('/local_knowledge/upload', methods=['POST'])
def upload_local_knowledge():
    """上传文件到本地知识库"""
    try:
        # 获取上传的文件列表和本地知识库的id
        files = request.files.getlist('files')  # 获取多个文件
        kno_id = request.form.get('kno_id')

        # 检查参数
        if not files or not kno_id:
            return jsonify({"status": "error", "message": "缺少文件或知识库ID"}), 400

        # 根据本地知识库id 获取知识库信息
        with LocalKnowledgeCrud() as crud:
            knowledge_list = crud.get_local_knowledge(kno_id=kno_id)
            if not knowledge_list:
                return jsonify({"status": "error", "message": "未找到对应的知识库"}), 404
            knowledge_detail = knowledge_list[0]  # 获取第一个结果
            logger.info(f"获取知识库信息: {knowledge_detail}")
            # 根据知识库中对应名称和kno_path获取文件夹的路径
            kno_path = Path(settings.KNOWLEDGE_LOCAL_PATH) / knowledge_detail[4]

            # 使用通用的文件上传处理函数
            result = handle_file_upload(files, kno_path, {'kno_id': kno_id, 'knowledge_detail': knowledge_detail})
            # 更新结果到sql
            success_file_names = result['success_file_names']
            for success_file_name in success_file_names:
                logger.info(f"更新知识列表: {success_file_name}")
                crud.local_knowledge_list_insert(generate_unique_id('knol', 8), success_file_name, '', str(kno_path), 1,
                                                 kno_id)
            return jsonify({"status": "success", "message": result['message']})
    except Exception as e:
        logger.error(f"上传文件时发生错误: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@local_knowledge_detail_bp.route('/local_knowledge/bind', methods=['POST'])
def local_knowledge_bind():
    data = request.get_json()  # 获取请求数据
    # 验证必要参数
    required_fields = ['local_kno_id', 'kb_id', 'action']
    missing_field = validate_required_fields(data, required_fields)
    if missing_field:
        return jsonify({'success': False, 'message': f'缺少必要字段: {missing_field}'}), 400

    local_kno_id = data['local_kno_id']  # ai_local_knowledge的kno_id
    kb_id = data['kb_id']  # ai_knowledge_base的knowledge_id
    action = data['action']  # #action 操作 bind、unbind、update
    status = data.get('status', None)  # status 可选参数，默认为None

    if action not in ['bind', 'unbind', 'update']:
        return jsonify({
            'success': False,
            'message': f'无效的操作: {action}'
        }), 400
    try:
        with LocalKnowledgeCrud() as crud:
            success = crud.local_knowledge_bind_func(local_kno_id, kb_id, action, status)
            if success:
                return jsonify({
                    'success': True,
                    'message': f'{action}本地知识库 {local_kno_id} 知识库 {kb_id}成功'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': f' {action}本地知识库 {local_kno_id} 知识库 {kb_id}失败'
                }), 500

    except Exception as e:
        logger.error(f"绑定知识库时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'绑定知识库时发生错误: {str(e)}'}), 500


def _get_binding_info(kno_id):
    """获取绑定信息的辅助函数"""
    return get_knowledge_base_binding_info(kno_id, LocalKnowledgeCrud, Environment_Crud)


@local_knowledge_detail_bp.route('/local_knowledge/bindings/<kno_id>', methods=['GET'])
def get_local_knowledge_bindings_by_id(kno_id):
    """获取特定本地知识库的绑定状态 - 通过URL参数"""
    try:
        binding_info = _get_binding_info(kno_id)
        if binding_info is None:
            return jsonify([]), 200
        return jsonify(binding_info), 200
    except Exception as e:
        logger.error(f"获取绑定状态时发生错误: {str(e)}")
        return jsonify({'error': '获取绑定状态失败'}), 500


@local_knowledge_detail_bp.route('/local_knowledge/bindings', methods=['POST'])
def get_local_knowledge_bindings():
    """获取特定本地知识库的绑定状态 - 通过POST请求体"""
    data = request.get_json()
    kno_id = data.get('kno_id', None)
    try:
        data = request.get_json()
        kno_id = data.get('kno_id', None)
        binding_info = _get_binding_info(kno_id)
        if binding_info is None:
            return jsonify([]), 200
        return jsonify(binding_info), 200
    except Exception as e:
        logger.error(f"获取绑定状态时发生错误: {str(e)}")
        return jsonify({'error': '获取绑定状态失败'}), 500


@local_knowledge_detail_bp.route('/local_knowledge/bindings/<kno_id>', methods=['POST'])
def get_local_knowledge_bindings_count(kno_id):
    """获取特定本地知识库的绑定数量"""
    try:
        with LocalKnowledgeCrud() as crud:
            # 获取绑定状态信息
            bindings = crud.get_local_knowledge_bind(kno_id=kno_id)
            if not bindings:
                return jsonify({'count': 0}), 200

            # 计算绑定数量
            count = len(bindings) if isinstance(bindings, list) else 1
            return jsonify({'count': count}), 200
    except Exception as e:
        logger.error(f"获取绑定数量时发生错误: {str(e)}")
        return jsonify({'error': '获取绑定数量失败'}), 500

@local_knowledge_detail_bp.route('/local_knowledge/sync', methods=['POST'])
def local_knowledge_sync():
    """同步本地知识库到知识库"""
    try:
        data = request.get_json()

        # 验证必要参数
        required_fields = ['local_kno_id', 'knowledge_id']
        missing_field = validate_required_fields(data, required_fields)
        if missing_field:
            return jsonify({'success': False, 'message': f'缺少必要字段: {missing_field}'}), 400

        local_kno_id = data['local_kno_id']
        knowledge_id = data['knowledge_id']

        # TODO
        # 1. 获取本地知识库文件列表 local_knowledge_file_list
        with LocalKnowledgeCrud() as l_crud, Environment_Crud() as e_curd:
            local_files = l_crud.get_local_knowledge_list(kno_id=local_kno_id, ls_status=1)
            knowledge_base_info = e_curd.get_knowledge_base(knowledge_id=knowledge_id)
            # 2. 获取知识库，查询文件夹列表，获取有没有对应名称的文件夹，如果没有则创建，返回文件夹id

        # 3. 将local_knowledge_file_list中的文件上传到对应文件夹id 中，使用知识库的配置
        # 4. 更新本地知识库状态为同步中
        # 5. 新建一个查询进程定时查询知识库中文件的状态，如果同步成功则更新本地知识库状态为同步成功，否则更新为同步失败

        with LocalKnowledgeCrud() as crud:
            # 获取本地知识库文件
            local_files = crud.get_local_knowledge_list(kno_id=local_kno_id)

            if not local_files:
                return jsonify({'success': False, 'message': '本地知识库中没有文件'}), 400

        # 这里应该有实际的同步逻辑
        # 例如，调用知识库API或执行其他同步操作

        return jsonify({
            'success': True,
            'message': f'知识库 {local_kno_id} 与 {knowledge_id} 同步成功'
        })

    except Exception as e:
        logger.error(f"同步知识库时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'同步知识库时发生错误: {str(e)}'}), 500

