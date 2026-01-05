from pathlib import Path

from flask import Blueprint, request, jsonify, render_template_string
import os
import logging
import uuid
from env_config_init import settings
from src.sql_funs.local_knowledge_crud import LocalKnowledgeCrud
from src.sql_funs.environment_crud import Environment_Crud
from src.flask_funcs.reports.flask_local_knowledge_renderer import LocalKnowledgeRendererFlask

# 创建logger
logger = logging.getLogger(__name__)

# 创建蓝图
local_knowledge_bp = Blueprint('local_knowledge', __name__)

# 导入渲染器
from src.flask_funcs.reports.flask_local_knowledge_renderer import LocalKnowledgeRendererFlask

renderer = LocalKnowledgeRendererFlask()


@local_knowledge_bp.route('/local_knowledge/')
def local_knowledge():
    """获取本地知识目录结构，按列表展示"""
    try:
        # 获取在sql ai_local_knowledge表中的数据，和本地目录中第一级目录，按名称匹配
        # 如果有数据库中的数据则展示数据库的，否则展示本地目录的
        with LocalKnowledgeCrud() as crud:
            # 获取数据库中的本地知识列表
            db_knowledge_list = crud.get_local_knowledge()
            logger.info(f"获取数据库中的本地知识列表: {db_knowledge_list}")
            # 获取本地目录结构
            local_knowledge_path = settings.KNOWLEDGE_LOCAL_PATH
            local_directories = []
            if os.path.exists(local_knowledge_path) and os.path.isdir(local_knowledge_path):
                for item in os.listdir(local_knowledge_path):
                    item_path = os.path.join(local_knowledge_path, item)
                    if os.path.isdir(item_path):
                        local_directories.append(item)
                logger.info(f"获取本地目录结构: {local_directories}")
            else:
                logger.error(f"本地目录不存在: {local_knowledge_path}")
                raise FileExistsError

            # 创建本地知识渲染器并渲染页面
            html_content = renderer.render_local_knowledge_page(db_knowledge_list, local_directories)

        return html_content
    except Exception as e:
        logger.error(f"获取本地知识列表时发生错误: {str(e)}")
        return "页面加载错误", 500


@local_knowledge_bp.route('/local_knowledge_detail/<kno_id>/<kno_name>')
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


@local_knowledge_bp.route('/api/local_knowledge_detail',methods=['POST'])
def api_local_knowledge_detail():
    data = request.get_json()
    kno_id = data.get('kno_id')
    kno_name = data.get('kno_name')
    """API接口：获取特定本地知识的详细信息"""
    try:
        with LocalKnowledgeCrud() as crud:
            # 获取本地知识列表详情（从ai_local_knowledge_list表）
            # 获取所有知识列表记录
            all_knowledge_list_records = crud.get_local_knowledge_list()
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


@local_knowledge_bp.route('/local_knowledge/upload', methods=['POST'])
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

            # 确保目录存在
            kno_path.mkdir(parents=True, exist_ok=True)

            success_count = 0
            failed_files = []

            for file in files:
                if file and file.filename:
                    # 验证文件类型（可以根据需要添加更多类型）
                    filename = file.filename

                    # 构建安全的文件路径
                    file_path = kno_path / filename
                    logger.info(f"获取知识库路径: {kno_path}")
                    # 检查是否已存在同名文件，如果存在则重命名
                    counter = 1
                    name, ext = file_path.stem, file_path.suffix
                    while file_path.exists():
                        new_filename = f"{name}_{counter}{ext}"
                        file_path = kno_path / new_filename
                        counter += 1

                    # 保存文件到本地文件夹
                    file.save(str(file_path))

                    # 生成新的知识文档ID
                    knol_id_new = f'knol_{str(uuid.uuid4())[:8]}'

                    # 在ai_local_knowledge_list表中新增一条记录
                    success = crud.local_knowledge_list_insert(
                        knol_id=knol_id_new,
                        knol_name=file_path.name,
                        knol_describe=f"上传到知识库 {knowledge_detail[1]} 的文件",
                        knol_path=str(file_path.relative_to(Path(settings.KNOWLEDGE_LOCAL_PATH))),
                        ls_status=1,  # 默认状态为1，表示已上传
                        kno_id=kno_id  # 关联到知识库ID
                    )

                    if success:
                        success_count += 1
                    else:
                        # 如果插入失败，删除已保存的文件
                        if file_path.exists():
                            file_path.unlink()
                        failed_files.append(file_path.name)

        if failed_files:
            message = f"成功上传 {success_count} 个文件，失败文件: {', '.join(failed_files)}"
            return jsonify({"status": "partial_success", "message": message, "success_count": success_count,
                            "failed_count": len(failed_files)})
        else:
            return jsonify({"status": "success", "message": f"成功上传 {success_count} 个文件"})
    except Exception as e:
        logger.error(f"上传文件时发生错误: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@local_knowledge_bp.route('/local_knowledge/delete/<knol_id>', methods=['DELETE'])
def delete_local_knowledge(knol_id):
    """删除本地知识库文件"""
    try:
        with LocalKnowledgeCrud() as crud:
            # 获取知识库文件信息 from ai_local_knowledge_list表
            knowledge_list_records = crud.get_local_knowledge_list(knol_id=knol_id)
            if not knowledge_list_records:
                return jsonify({"status": "error", "message": "未找到对应的文件记录"}), 404
            knowledge_list_record = knowledge_list_records[0]  # 获取第一个结果
            logger.info(f"获取知识库列表文件信息: {knowledge_list_record}")

            # 获取文件路径
            file_path = Path(settings.KNOWLEDGE_LOCAL_PATH) / knowledge_list_record[4]  # knol_path 是第5列 (索引4)

            # 检查文件是否存在
            if not file_path.exists():
                logger.warning(f"文件不存在: {file_path}")
                # 即使文件不存在，也继续删除数据库记录
            else:
                # 删除本地文件
                file_path.unlink()
                logger.info(f"已删除本地文件: {file_path}")

            # 删除数据库ai_local_knowledge_list表中knol_id对应的记录
            delete_success = crud.local_knowledge_list_delete(knol_id=knol_id)

            if delete_success:
                return jsonify({"status": "success", "message": "文件删除成功"})
            else:
                return jsonify({"status": "error", "message": "删除数据库记录失败"}), 500

    except Exception as e:
        logger.error(f"删除文件时发生错误: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@local_knowledge_bp.route('/local_knowledge/edit/<knol_id>', methods=['PUT'])
def edit_local_knowledge(knol_id):
    try:
        describe = request.form.get('knol_describe')

        if not describe:
            return jsonify({"status": "error", "message": "描述内容不能为空"}), 400

        with LocalKnowledgeCrud() as crud:
            # 更新ai_local_knowledge_list表的knol_describe字段
            success = crud.local_knowledge_list_update(
                knol_id=knol_id,
                knol_describe=describe
            )

            if success:
                return jsonify({"status": "success", "message": "文件描述更新成功"})
            else:
                return jsonify({"status": "error", "message": "更新文件描述失败"}), 500
    except Exception as e:
        logger.error(f"编辑文件描述时发生错误: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@local_knowledge_bp.route('/local_knowledge/bind', methods=['POST'])
def local_knowledge_bind():
    data = request.get_json()  # 获取请求数据
    # 验证必要参数
    required_fields = ['local_kno_id', 'kb_id', 'action']
    for field in required_fields:
        if field not in data:
            return jsonify({'success': False, 'message': f'缺少必要字段: {field}'}), 400
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
    with LocalKnowledgeCrud() as crud, Environment_Crud() as env_crud:
        # 获取绑定状态信息
        bindings = crud.get_local_knowledge_bind(kno_id=kno_id)
        if not bindings:
            return None
        
        # 构建返回数据，包含知识库名称
        binding_dict = crud._local_knowledge_bind_to_json(bindings[0])
        knowledge_id = binding_dict['knowledge_id']
        
        # 获取知识库名称
        knowledge_base = env_crud.get_knowledge_base(knowledge_id=knowledge_id)
        if not knowledge_base:
            return None
        
        binding_dict['knowledge_name'] = knowledge_base[0][1]
        return binding_dict


@local_knowledge_bp.route('/local_knowledge/bindings/<kno_id>', methods=['GET'])
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


@local_knowledge_bp.route('/local_knowledge/bindings', methods=['POST'])
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


@local_knowledge_bp.route('/local_knowledge/bindings/<kno_id>', methods=['POST'])
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


@local_knowledge_bp.route('/local_knowledge/sync', methods=['POST'])
def local_knowledge_sync():
    """同步本地知识库到知识库"""
    try:
        data = request.get_json()

        # 验证必要参数
        required_fields = ['local_kno_id', 'knowledge_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'缺少必要字段: {field}'}), 400

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


@local_knowledge_bp.route('/local_knowledge/update', methods=['PUT'])
def update_local_knowledge():
    """更新本地知识库信息"""
    try:
        data = request.get_json()
        kno_id = data.get('kno_id')
        kno_name = data.get('kno_name')
        kno_describe = data.get('kno_describe')

        if not kno_id:
            return jsonify({'success': False, 'message': '缺少知识库ID'}), 400

        with LocalKnowledgeCrud() as crud:
            # 更新知识库描述
            success = crud.local_knowledge_update(
                kno_id=kno_id,
                kno_name=kno_name,
                kno_describe=kno_describe
            )
            
            if success:
                return jsonify({'success': True, 'message': '知识库更新成功'})
            else:
                return jsonify({'success': False, 'message': '知识库更新失败'}), 500
    except Exception as e:
        logger.error(f"更新知识库时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'更新知识库时发生错误: {str(e)}'}), 500


@local_knowledge_bp.route('/local_knowledge/delete_main/<kno_id>', methods=['DELETE'])
def delete_main_local_knowledge(kno_id):
    """删除主要的本地知识库记录"""
    try:
        with LocalKnowledgeCrud() as crud:
            # 先删除关联的文件记录
            # 获取该知识库下的所有文件
            local_files = crud.get_local_knowledge_list(kno_id=kno_id)
            for file_record in local_files:
                # 删除本地文件
                file_path = Path(settings.KNOWLEDGE_LOCAL_PATH) / file_record[4]  # knol_path 是第5列 (索引4)
                if file_path.exists():
                    file_path.unlink()
                
                # 删除数据库记录
                crud.local_knowledge_list_delete(knol_id=file_record[1])  # knol_id 是第2列 (索引1)

            # 删除知识库绑定记录
            bindings = crud.get_local_knowledge_bind(kno_id=kno_id)
            for binding in bindings:
                # 删除绑定记录
                query = "DELETE FROM ai_knowledge_bind WHERE kno_id = %s AND knowledge_id = %s"
                params = (kno_id, binding[2])  # knowledge_id 是第3列 (索引2)
                crud.execute_query(query, params)

            # 删除主要知识库记录
            success = crud.local_knowledge_delete(kno_id=kno_id)

            if success:
                return jsonify({'success': True, 'message': '知识库删除成功'})
            else:
                return jsonify({'success': False, 'message': '知识库删除失败'}), 500
    except Exception as e:
        logger.error(f"删除知识库时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'删除知识库时发生错误: {str(e)}'}), 500
