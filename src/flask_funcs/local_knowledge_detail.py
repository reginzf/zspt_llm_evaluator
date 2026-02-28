import jsonpath
import tempfile

import os
import logging
from flask import Blueprint, request, jsonify

from src.sql_funs import LocalKnowledgeCrud, Environment_Crud, KnowledgePathCrud, KnowledgeCrud
from src.flask_funcs.common_utils import validate_required_fields, get_knowledge_base_binding_info, handle_file_upload, \
    generate_unique_id
from src.zlpt_temp import zlpt_upload_files, zlpt_login, KnowledgeBase
from src.utils.minio_client import MinIOClient

# 创建logger
logger = logging.getLogger(__name__)

# 创建蓝图
local_knowledge_detail_bp = Blueprint('local_knowledge_detail', __name__)

UPLOAD_DIR = 'knowledge-files'


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
            all_knowledge_list_records = crud.get_local_knowledge_file_list(kno_id=kno_id)
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
                            "kno_describe": record[3],  # kno_describe
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
                                "kno_describe": record[3],  # kno_describe
                                "knol_path": record[4],  # knol_path
                                "ls_status": record[5],  # ls_status
                                "created_at": record[6],  # created_at
                                "updated_at": record[7],  # updated_at
                            }
                            filtered_knowledge_list.append(filtered_record)




    except Exception as e:
        logger.error(f"获取本地知识详情时发生错误: {str(e)}")
        return jsonify({"error": "页面加载错误"}), 500

    # 直接返回过滤后的知识列表详情，因为这是前端需要的数据格式
    return jsonify(filtered_knowledge_list)


@local_knowledge_detail_bp.route('/local_knowledge/upload', methods=['POST'])
def upload_local_knowledge():
    """上传文件到本地知识库（仅使用MinIO存储）"""
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

            # 使用MinIO存储：kno_path作为MinIO中的前缀
            target_path = knowledge_detail[4]  # kno_path作为MinIO前缀
            logger.info(f"使用MinIO存储，前缀: {target_path}")

            # 使用通用的文件上传处理函数（强制使用MinIO）
            result = handle_file_upload(files, str(target_path),
                                        {'kno_id': kno_id, 'knowledge_detail': knowledge_detail},
                                        use_minio=True)

            # 更新结果到sql
            success_file_names = result['success_file_names']
            for success_file_name in success_file_names:
                logger.info(f"更新知识列表: {success_file_name}")
                # MinIO模式下存储相对路径（前缀）
                knol_path = str(target_path) + '/' + success_file_name

                crud.local_knowledge_list_insert(generate_unique_id('knol', 8),
                                                 success_file_name, '', knol_path, 1, kno_id)

            return jsonify({"status": "success",
                            "message": f"{result['message']} (存储方式: MinIO)",
                            "storage_type": "minio"})
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


@local_knowledge_detail_bp.route('/local_knowledge_detail/sync', methods=['POST'])
def local_knowledge_sync():
    """同步本地知识库到知识库（支持MinIO和本地文件）"""
    temp_files = []  # 记录临时文件用于清理

    try:
        data = request.get_json()
        # 验证必要参数
        required_fields = ['local_kno_id', 'knowledge_id']
        missing_field = validate_required_fields(data, required_fields)
        if missing_field:
            return jsonify({'success': False, 'message': f'缺少必要字段: {missing_field}'}), 400

        local_kno_id = data['local_kno_id']
        knowledge_id = data['knowledge_id']
        logger.info(f"开始同步本地知识库 {local_kno_id} 到知识库 {knowledge_id}")

        # 获取本地知识库信息和相关数据
        sync_data = _prepare_sync_data(local_kno_id, knowledge_id)
        if isinstance(sync_data, tuple):  # 错误情况
            return sync_data

        # 记录需要清理的临时文件
        temp_files = sync_data.get('temp_files', [])

        zlpt_user = zlpt_login(None, None, knowledge_id)
        know_client = KnowledgeBase(zlpt_user)
        # 上传文件到知识库
        upload_result = _upload_files_to_knowledge_base(sync_data, know_client)
        if not upload_result:
            logger.error("文件上传失败")
            return jsonify({'success': False, 'message': '文件上传失败'}), 500

        # 更新本地文件状态
        _update_local_file_status(sync_data['local_files'], sync_data['uploaded_files'], knowledge_id)

        # 更新数据库记录
        _update_database_records(sync_data, know_client)

        logger.info(f"同步完成: 本地知识库 {local_kno_id} 到知识库 {knowledge_id}")
        return jsonify({
            'success': True,
            'message': f'知识库 {local_kno_id} 与 {knowledge_id} 同步成功'
        })

    except Exception as e:
        logger.error(f"同步知识库时发生错误: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': f'同步知识库时发生错误: {str(e)}'}), 500
    finally:
        # 清理临时文件
        if temp_files:
            _cleanup_temp_files(temp_files)


def _prepare_sync_data(local_kno_id, knowledge_id):
    """准备同步数据，包括本地知识库信息、文件列表、目标知识库配置等"""
    try:
        with LocalKnowledgeCrud() as lk_crud, KnowledgePathCrud() as kp_crud, Environment_Crud() as e_crud:
            # 获取本地知识库信息
            logger.info(f"获取本地知识库信息: {local_kno_id}")
            local_knowledge_comprehensive = lk_crud.get_local_knowledge_with_bindings(local_kno_id)
            if not local_knowledge_comprehensive:
                return jsonify({'success': False, 'message': f'未找到本地知识库: {local_kno_id}'}), 404

            # 获取第一个记录作为本地知识库信息
            local_knowledge_comprehensive = local_knowledge_comprehensive[0]
            local_knowledge_info = {
                'kno_id': local_knowledge_comprehensive[0],
                'kno_name': local_knowledge_comprehensive[1],
                'kno_describe': local_knowledge_comprehensive[2],
                'kno_path': local_knowledge_comprehensive[3]
            }
            logger.info(f"获取到本地知识库信息: {local_knowledge_info}")

            # 获取本地知识库的文件列表
            logger.info(f"获取本地知识库 {local_kno_id} 的文件列表")
            local_files = lk_crud.get_local_knowledge_file_list(kno_id=local_kno_id)
            logger.info(f"获取到 {len(local_files)} 个本地文件")
            # 获取已经上传的文件列表
            uploaded_files = lk_crud.get_local_knowledge_file_upload(knowledge_base_id=knowledge_id)
            uploaded_files = [file[1] for file in uploaded_files]

            # 构建文件路径列表
            file_path_all = []
            temp_files_created = []  # 记录创建的临时文件

            for file in local_files:
                if file[2] not in uploaded_files:
                    # MinIO文件：需要先下载到临时目录
                    file_storage_path = file[4]  # knol_path字段
                    temp_path = _download_minio_file_to_temp(file_storage_path)
                    if temp_path:
                        file_path_all.append(temp_path)
                        temp_files_created.append(temp_path)
                    else:
                        logger.warning(f"无法下载MinIO文件: {file_storage_path}")

            logger.info(f"构建文件路径列表: {file_path_all}")
            # 获取知识库配置信息
            logger.info(f"获取知识库 {knowledge_id} 的配置信息")
            knowledge_base_list = e_crud.get_knowledge_base(knowledge_id=knowledge_id)
            if not knowledge_base_list:
                return jsonify({'success': False, 'message': f'未找到知识库: {knowledge_id}'}), 404

            knowledge_base_info = e_crud._knowledge_base_to_json(knowledge_base_list[0])
            logger.info(
                f"获取到知识库配置信息: chunk_size={knowledge_base_info['chunk_size']}, "
                f"chunk_overlap={knowledge_base_info['chunk_overlap']}")

            # 获取知识库目录树
            logger.info(f"获取知识库目录树: {knowledge_id}")
            knowledge_path_tree = kp_crud.generate_knowledge_path_tree(knowledge_id)
            logger.info(f"获取到知识库目录树，节点数量: {len(knowledge_path_tree)}")

            # 检查并创建目录（如果根目录中不存在对应目录）
            existing_names = [ele['kno_path_name'] for ele in knowledge_path_tree]
            logger.info(f"现有目录名称: {existing_names}")
            zlpt_user = zlpt_login(knowledge_base_info['zlpt_base_id'], e_crud)
            know_client = KnowledgeBase(zlpt_user)
            if local_knowledge_info['kno_path'] not in existing_names:
                logger.info(f"目录 {local_knowledge_info['kno_path']} 不存在，创建中...")
                create_dir_result = know_client.knowledge_content_add_or_update(
                    knowledgeId=knowledge_id,
                    contentName=local_knowledge_info['kno_path'],
                    parentContentCode=None  # 创建在根目录
                )
                if not create_dir_result or create_dir_result.get('code') != 200:
                    logger.error(f"创建目录失败: {create_dir_result}")
                    return jsonify({'success': False, 'message': '创建知识库目录失败'}), 500
                logger.info(f"目录 {local_knowledge_info['kno_path']} 创建成功")
            else:
                logger.info(f"目录 {local_knowledge_info['kno_path']} 已存在")

            # 获取目录的content_code
            logger.info(f"获取目录 {local_knowledge_info['kno_path']} 的content_code")
            res = know_client.knowledge_content_tree(knowledgeId=knowledge_id)
            if not res or res.get('code') != 200:
                logger.error(f"获取知识库目录树失败: {res}")
                return jsonify({'success': False, 'message': '获取知识库目录树失败'}), 500

            content_code_result = jsonpath.jsonpath(
                res, f'''$.data[?(@.contentName=="{local_knowledge_info['kno_path']}")]''')

            if not content_code_result:
                logger.error(f"未找到目录 {local_knowledge_info['kno_path']} 的content_code")
                return jsonify({'success': False, 'message': '未找到目录的content_code'}), 500

            content_code = content_code_result[0]['contentCode']
            logger.info(f"获取到content_code: {content_code}")

            return {
                'local_knowledge_info': local_knowledge_info,
                'local_files': local_files,
                'uploaded_files': uploaded_files,
                'file_path_all': file_path_all,
                'temp_files': temp_files_created,  # 返回临时文件列表用于清理
                'knowledge_base_info': knowledge_base_info,
                'content_code': content_code,
                'knowledge_id': knowledge_id
            }

    except Exception as e:
        logger.error(f"准备同步数据时发生错误: {str(e)}", exc_info=True)
        raise


def _upload_files_to_knowledge_base(sync_data, know_client):
    """上传文件到知识库"""
    logger.info(f"开始上传文件到知识库，文件数量: {len(sync_data['file_path_all'])}")
    upload_result = zlpt_upload_files(
        know_client,
        sync_data['file_path_all'],
        sync_data['knowledge_id'],
        sync_data['content_code'],
        sync_data['knowledge_base_info']['chunk_size'],
        sync_data['knowledge_base_info']['chunk_overlap']
    )
    logger.info("文件上传完成")
    return upload_result


def _update_local_file_status(local_files, uploaded_files, knowledge_id):
    """更新本地文件状态为已同步"""
    logger.info("开始更新本地文件状态")
    with LocalKnowledgeCrud() as l_crud:
        for file in local_files:
            if file[2] not in uploaded_files:
                update_result = l_crud.local_knowledge_list_update(file[1], ls_status=0)  # 状态0表示已同步
                l_crud.local_knowledge_file_upload_insert(file[1], knowledge_id, 0)
                if not update_result:
                    logger.warning(f"更新文件 {file[1]} 状态失败")
                else:
                    logger.info(f"成功更新文件 {file[1]} 状态为 0")


def _download_minio_file_to_temp(minio_path):
    """从MinIO下载文件到临时目录
    
    Args:
        minio_path: MinIO中的文件路径
        
    Returns:
        str: 临时文件路径，失败返回None
    """

    try:
        # 获取MinIO客户端
        minio_client = MinIOClient(bucket_name=UPLOAD_DIR)

        # 从路径中提取对象名称
        object_name = minio_path.lstrip('/')

        # 创建临时文件
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.basename(object_name))
        temp_file.close()

        # 下载文件
        if minio_client.download_file(object_name, temp_file.name):
            logger.info(f"成功下载MinIO文件: {object_name} -> {temp_file.name}")
            return temp_file.name
        else:
            # 下载失败，清理临时文件
            try:
                os.unlink(temp_file.name)
            except:
                pass
            return None

    except Exception as e:
        logger.error(f"下载MinIO文件失败: {e}")
        return None


def _cleanup_temp_files(file_paths):
    """清理临时文件
    
    Args:
        file_paths: 临时文件路径列表
    """
    import os

    for file_path in file_paths:
        try:
            if os.path.exists(file_path) and 'tmp' in file_path.lower():
                os.unlink(file_path)
                logger.info(f"清理临时文件: {file_path}")
        except Exception as e:
            logger.warning(f"清理临时文件失败 {file_path}: {e}")


def _update_database_records(sync_data, know_client):
    """更新数据库记录，包括知识路径表和知识表"""
    with KnowledgePathCrud() as kp_crud_inner, KnowledgeCrud() as k_crud:
        k_p_result = kp_crud_inner.get_knowledge_path_list(kno_path_id=sync_data['content_code'])
        if k_p_result:
            logger.info("将同步信息更新到知识库路径表")
            k_p_result = k_p_result[0]
            file_sync_info = k_p_result[4]
            for file in sync_data['local_files']:
                file_sync_info[file[1]] = {'name': file[2], 'path': file[4], 'status': file[5]}
            logger.info(f"更新后的文件同步信息: {file_sync_info}")
            result = kp_crud_inner.knowledge_path_update(
                kno_path_id=sync_data['content_code'],
                doc_map=file_sync_info
            )
        else:
            logger.info("将同步信息插入知识库路径表")
            file_sync_info = {file[1]: {'name': file[2], 'path': file[4], 'status': file[5]} for file in
                              sync_data['local_files']}
            result = kp_crud_inner.knowledge_path_insert(
                kno_path_id=sync_data['content_code'],
                kno_path_name=sync_data['local_knowledge_info']['kno_path'],
                knowledge_id=sync_data['knowledge_id'],
                parent=None,
                doc_map=file_sync_info
            )
        if not result:
            logger.warning("插入知识库路径信息失败")
        else:
            logger.info("成功插入知识库路径信息")
        # 更新ai_knowledge表
        doc_records = know_client.knowledge_doc_list(sync_data['knowledge_id'], contentCode=sync_data['content_code'],
                                                     size=100)
        for doc_record in doc_records['data']['records']:
            k_crud.knowledge_insert(doc_record['docId'], doc_record['docName'], doc_record['fileFormat'],
                                    doc_record['description'], doc_record['docName'], sync_data['content_code'],
                                    sync_data['knowledge_id'])


@local_knowledge_detail_bp.route('/local_knowledge_doc/delete/<knol_id>', methods=['DELETE'])
def delete_local_knowledge_file(knol_id):
    """删除本地知识库中的单个文件（仅支持MinIO存储）"""
    try:
        with LocalKnowledgeCrud() as crud:
            # 获取文件记录信息
            file_records = crud.get_local_knowledge_file_list(knol_id=knol_id)
            if not file_records:
                return jsonify({'status': 'error', 'message': '未找到对应的文件记录'}), 404

            file_record = file_records[0]  # 获取第一个结果
            # file_record 结构: (id, knol_id, knol_name, knol_describe, knol_path, ls_status, created_at, updated_at, kno_id)
            knol_path_str = file_record[4]  # knol_path 是第5列 (索引4)
            knol_name = file_record[2]  # knol_name 是第3列 (索引2)
            knowledge_id = file_record[8]  # kno_id 是第9列 (索引8)

            # 获取知识库路径信息以构建完整文件路径
            knowledge_list = crud.get_local_knowledge(kno_id=knowledge_id)
            if not knowledge_list:
                return jsonify({'status': 'error', 'message': '未找到对应的主知识库信息'}), 404

            knowledge_detail = knowledge_list[0]
            knowledge_path = knowledge_detail[4]  # kno_path 是第5列 (索引4)

            # 构建MinIO中的对象名称
            object_name = f"{knowledge_path}/{knol_name}"
            
            # 从MinIO删除文件
            minio_client = MinIOClient(bucket_name=UPLOAD_DIR)
            delete_success = minio_client.delete_file(object_name)
            
            if delete_success:
                logger.info(f"MinIO文件已删除: {object_name}")
            else:
                logger.warning(f"MinIO文件删除失败: {object_name}")

            # 删除数据库记录
            success = crud.local_knowledge_list_delete(knol_id=knol_id)

            if success:
                return jsonify({'status': 'success', 'message': '文件删除成功'})
            else:
                return jsonify({'status': 'error', 'message': '文件删除失败'}), 500
    except Exception as e:
        logger.error(f"删除文件时发生错误: {str(e)}")
        return jsonify({'status': 'error', 'message': f'删除文件时发生错误: {str(e)}'}), 500


@local_knowledge_detail_bp.route('/local_knowledge_doc/edit/<knol_id>', methods=['PUT'])
def edit_local_knowledge_file(knol_id):
    """编辑本地知识库中的单个文件（仅支持编辑描述）"""
    try:
        # 从请求中获取新的描述
        knol_describe = request.form.get('knol_describe')

        with LocalKnowledgeCrud() as crud:
            # 更新数据库记录
            success = crud.local_knowledge_list_update(knol_id=knol_id, knol_describe=knol_describe)

            if success:
                return jsonify({'status': 'success', 'message': '文件描述更新成功'})
            else:
                return jsonify({'status': 'error', 'message': '文件描述更新失败'}), 500
    except Exception as e:
        logger.error(f"更新文件描述时发生错误: {str(e)}")
        return jsonify({'status': 'error', 'message': f'更新文件描述时发生错误: {str(e)}'}), 500
