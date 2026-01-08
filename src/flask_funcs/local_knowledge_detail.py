from pathlib import Path

import jsonpath
from flask import Blueprint, request, jsonify
import os
import logging
from env_config_init import settings
from src.sql_funs import LocalKnowledgeCrud, Environment_Crud, KnowledgePathCrud, LabelStudioCrud

from src.flask_funcs.common_utils import validate_required_fields, get_knowledge_base_binding_info, handle_file_upload, \
    generate_unique_id
from src.zlpt.zlpt_temp import know_client, zlpt_upload_files

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

        logger.info(f"开始同步本地知识库 {local_kno_id} 到知识库 {knowledge_id}")

        with LocalKnowledgeCrud() as l_crud, Environment_Crud() as e_crud, KnowledgePathCrud() as kp_crud:
            # 1、获取本地知识库的信息
            logger.info(f"获取本地知识库信息: {local_kno_id}")
            local_knowledge_list = l_crud.get_local_knowledge(kno_id=local_kno_id)
            if not local_knowledge_list:
                return jsonify({'success': False, 'message': f'未找到本地知识库: {local_kno_id}'}), 404

            local_knowledge_info = l_crud._local_knowledge_to_json(local_knowledge_list[0])
            logger.info(f"获取到本地知识库信息: {local_knowledge_info}")

            # 2、获取知识库的tree
            logger.info(f"获取知识库目录树: {knowledge_id}")
            knowledge_path_tree = kp_crud.generate_knowledge_path_tree(knowledge_id)
            logger.info(f"获取到知识库目录树，节点数量: {len(knowledge_path_tree)}")

            # 3、检查并创建目录（如果根目录中不存在对应目录）
            existing_names = [ele['kno_path_name'] for ele in knowledge_path_tree]
            logger.info(f"现有目录名称: {existing_names}")

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
                res,
                f'''$.data[?(@.contentName=="{local_knowledge_info['kno_path']}")]'''
            )

            if not content_code_result:
                logger.error(f"未找到目录 {local_knowledge_info['kno_path']} 的content_code")
                return jsonify({'success': False, 'message': '未找到目录的content_code'}), 500

            content_code = content_code_result[0]['contentCode']
            logger.info(f"获取到content_code: {content_code}")
            # 4、获取本地知识库的文件列表
            logger.info(f"获取本地知识库 {local_kno_id} 的文件列表")
            local_files = l_crud.get_local_knowledge_list(kno_id=local_kno_id)
            logger.info(f"获取到 {len(local_files)} 个本地文件")

            # 构建文件路径列表
            file_path_all = []
            for file in local_files:
                # file格式: (id, knol_id, knol_name, knol_describe, knol_path, ls_status, created_at, updated_at, kno_id)
                file_path = os.path.join(settings.KNOWLEDGE_LOCAL_PATH, local_knowledge_info['kno_path'], file[2])
                file_path_all.append(file_path)
            logger.info(f"构建文件路径列表: {file_path_all}")

            # 5、获取知识库配置信息
            logger.info(f"获取知识库 {knowledge_id} 的配置信息")
            knowledge_base_list = e_crud.get_knowledge_base(knowledge_id=knowledge_id)
            if not knowledge_base_list:
                return jsonify({'success': False, 'message': f'未找到知识库: {knowledge_id}'}), 404

            knowledge_base_info = e_crud._knowledge_base_to_json(knowledge_base_list[0])
            logger.info(
                f"获取到知识库配置信息: chunk_size={knowledge_base_info['chunk_size']}, chunk_overlap={knowledge_base_info['chunk_overlap']}")

            # 6、上传文件到知识库
            logger.info(f"开始上传文件到知识库，文件数量: {len(file_path_all)}")
            upload_result = zlpt_upload_files(
                know_client,
                file_path_all,
                knowledge_id,
                content_code,
                knowledge_base_info['chunk_size'],
                knowledge_base_info['chunk_overlap']
            )

            if not upload_result:
                logger.error("文件上传失败")
                return jsonify({'success': False, 'message': '文件上传失败'}), 500
            logger.info("文件上传完成")

            # 7、更新本地文件状态
            logger.info("开始更新本地文件状态")
            for file in local_files:
                update_result = l_crud.local_knowledge_list_update(file[1], ls_status=2)  # 状态2表示已完成
                if not update_result:
                    logger.warning(f"更新文件 {file[1]} 状态失败")
                else:
                    logger.info(f"成功更新文件 {file[1]} 状态为 2")
            
            # 8、将同步信息插入知识库路径表
            logger.info("将同步信息插入知识库路径表")
            file_sync_info = {file[1]: {'name': file[2], 'path': file[4], 'status': file[5]} for file in local_files}
            insert_result = kp_crud.knowledge_path_insert(
                kno_path_id=content_code,
                kno_path_name=local_knowledge_info['kno_path'],
                knowledge_id=knowledge_id,
                parent=None,
                doc_map=file_sync_info
            )
            if not insert_result:
                logger.warning("插入知识库路径信息失败")
            else:
                logger.info("成功插入知识库路径信息")
                
            logger.info(f"同步完成: 本地知识库 {local_kno_id} 到知识库 {knowledge_id}")

        return jsonify({
            'success': True,
            'message': f'知识库 {local_kno_id} 与 {knowledge_id} 同步成功'
        })

    except Exception as e:
        logger.error(f"同步知识库时发生错误: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': f'同步知识库时发生错误: {str(e)}'}), 500


# 新增Label-Studio标注功能相关路由
@local_knowledge_detail_bp.route('/local_knowledge_detail/label_studio/get_environments', methods=['GET'])
def get_label_studio_environments():
    """获取可用Label-Studio环境列表"""
    try:
        # 获取查询参数
        kno_id = request.args.get('kno_id')
        
        with LabelStudioCrud() as ls_crud:
            # 获取所有Label-Studio环境
            environments = ls_crud.label_studio_list()
            environment_list = [ls_crud._label_studio_to_json(env) for env in environments]
            
            # 检查当前知识库是否已绑定环境 - 这里需要根据实际数据库表结构实现
            # 临时实现，假设没有绑定关系表，返回None表示未绑定
            bound_environment = None
            
            # 如果有绑定关系表，这里应该查询绑定关系
            # 示例伪代码：
            # with BindingCrud() as binding_crud:
            #     binding_list = binding_crud.get_bindings(kno_id=kno_id)
            #     if binding_list:
            #         # 获取绑定的环境信息
            #         bound_ls_id = binding_list[0][2]  # 假设第三个字段是ls_id
            #         for env in environment_list:
            #             if env['label_studio_id'] == bound_ls_id:
            #                 bound_environment = env
            #                 break

            return jsonify({
                'success': True,
                'data': {
                    'environments': environment_list,
                    'bound_environment': bound_environment  # 如果有绑定则返回绑定的环境信息
                }
            })
    except Exception as e:
        logger.error(f"获取Label-Studio环境列表时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'获取环境列表时发生错误: {str(e)}'}), 500


@local_knowledge_detail_bp.route('/local_knowledge_detail/label_studio/bind_environment', methods=['POST'])
def bind_label_studio_environment():
    """绑定知识库与Label-Studio环境"""
    try:
        data = request.get_json()
        required_fields = ['kno_id', 'ls_id']
        missing_field = validate_required_fields(data, required_fields)
        if missing_field:
            return jsonify({'success': False, 'message': f'缺少必要字段: {missing_field}'}), 400

        kno_id = data['kno_id']
        ls_id = data['ls_id']

        # 这里需要实现绑定逻辑，将知识库ID与Label-Studio环境ID的绑定关系存储到数据库
        # 暂时简化实现，实际需要创建绑定表并实现绑定逻辑
        # 实际实现中需要查询绑定关系表并插入绑定记录

        # 检查环境是否存在
        with LabelStudioCrud() as ls_crud:
            env_list = ls_crud.label_studio_list(label_studio_id=ls_id)
            if not env_list:
                return jsonify({'success': False, 'message': '指定的Label-Studio环境不存在'}), 400

        # 绑定逻辑实现（待完善数据库表结构和绑定关系）
        # 这里应该插入绑定关系到数据库表
        # 示例伪代码：
        # with BindingCrud() as binding_crud:
        #     result = binding_crud.bind_knowledge_to_label_studio(kno_id, ls_id)

        return jsonify({
            'success': True,
            'message': '环境绑定成功'
        })
    except Exception as e:
        logger.error(f"绑定Label-Studio环境时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'绑定环境时发生错误: {str(e)}'}), 500


@local_knowledge_detail_bp.route('/local_knowledge_detail/label_studio/unbind_environment', methods=['POST'])
def unbind_label_studio_environment():
    """解绑知识库与Label-Studio环境"""
    try:
        data = request.get_json()
        required_fields = ['kno_id', 'ls_id']
        missing_field = validate_required_fields(data, required_fields)
        if missing_field:
            return jsonify({'success': False, 'message': f'缺少必要字段: {missing_field}'}), 400

        kno_id = data['kno_id']
        ls_id = data['ls_id']

        # 解绑逻辑实现（待完善数据库表结构和解绑关系）
        # 这里应该从数据库表中删除绑定关系
        # 示例伪代码：
        # with BindingCrud() as binding_crud:
        #     result = binding_crud.unbind_knowledge_to_label_studio(kno_id, ls_id)

        return jsonify({
            'success': True,
            'message': '环境解绑成功'
        })
    except Exception as e:
        logger.error(f"解绑Label-Studio环境时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'解绑环境时发生错误: {str(e)}'}), 500


@local_knowledge_detail_bp.route('/local_knowledge_detail/label_studio/create_annotation_project', methods=['POST'])
def create_annotation_project():
    """创建标注任务"""
    try:
        data = request.get_json()
        required_fields = ['name', 'knowledge_base_id', 'environment_id']
        missing_field = validate_required_fields(data, required_fields)
        if missing_field:
            return jsonify({'success': False, 'message': f'缺少必要字段: {missing_field}'}), 400

        name = data['name']
        knowledge_base_id = data['knowledge_base_id']
        environment_id = data['environment_id']
        question_set_id = data.get('question_set_id')  # 可选参数

        # 创建标注任务逻辑（待完善数据库表结构和任务创建逻辑）
        # 示例伪代码：
        # with AnnotationProjectCrud() as project_crud:
        #     project_id = generate_unique_id('project', 8)
        #     result = project_crud.create_annotation_project(project_id, name, knowledge_base_id, environment_id, question_set_id)

        return jsonify({
            'success': True,
            'message': '标注任务创建成功'
        })
    except Exception as e:
        logger.error(f"创建标注任务时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'创建标注任务时发生错误: {str(e)}'}), 500


@local_knowledge_detail_bp.route('/local_knowledge_detail/label_studio/get_project', methods=['GET'])
def get_annotation_projects():
    """获取标注任务列表"""
    try:
        kno_id = request.args.get('kno_id')

        # 获取标注任务列表逻辑（待完善数据库表结构和任务查询逻辑）
        # 示例伪代码：
        # with AnnotationProjectCrud() as project_crud:
        #     projects = project_crud.get_annotation_projects_by_knowledge_base(kno_id)

        # 模拟返回数据 - 修正数据结构以匹配前端期望
        projects = [
            {
                'id': 'project_1',
                'name': '示例标注任务',
                'knowledge_base_id': kno_id,
                'knowledge_base_name': '示例知识库',
                'environment_id': 'env_1',
                'question_set_id': 'qs_1',
                'question_set_name': '示例问题集',
                'annotated_count': 10,
                'total_count': 50,
                'status': 'in_progress'
            }
        ]

        return jsonify({
            'success': True,
            'data': projects
        })
    except Exception as e:
        logger.error(f"获取标注任务列表时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'获取任务列表时发生错误: {str(e)}'}), 500


@local_knowledge_detail_bp.route('/local_knowledge_detail/label_studio/update_project', methods=['PUT'])
def update_annotation_project():
    """更新标注任务信息"""
    try:
        data = request.get_json()
        required_fields = ['id', 'name']
        missing_field = validate_required_fields(data, required_fields)
        if missing_field:
            return jsonify({'success': False, 'message': f'缺少必要字段: {missing_field}'}), 400

        project_id = data['id']
        name = data['name']
        status = data.get('status')
        annotated_count = data.get('annotated_count')

        # 更新标注任务逻辑（待完善数据库表结构和任务更新逻辑）
        # 示例伪代码：
        # with AnnotationProjectCrud() as project_crud:
        #     result = project_crud.update_annotation_project(project_id, name, status, annotated_count)

        return jsonify({
            'success': True,
            'message': '标注任务更新成功'
        })
    except Exception as e:
        logger.error(f"更新标注任务时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'更新任务时发生错误: {str(e)}'}), 500


@local_knowledge_detail_bp.route('/local_knowledge_detail/label_studio/delete_project', methods=['DELETE'])
def delete_annotation_project():
    """删除标注任务"""
    try:
        data = request.get_json()
        required_fields = ['id']
        missing_field = validate_required_fields(data, required_fields)
        if missing_field:
            return jsonify({'success': False, 'message': f'缺少必要字段: {missing_field}'}), 400

        project_id = data['id']

        # 删除标注任务逻辑（待完善数据库表结构和任务删除逻辑）
        # 示例伪代码：
        # with AnnotationProjectCrud() as project_crud:
        #     result = project_crud.delete_annotation_project(project_id)

        return jsonify({
            'success': True,
            'message': '标注任务删除成功'
        })
    except Exception as e:
        logger.error(f"删除标注任务时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'删除任务时发生错误: {str(e)}'}), 500
