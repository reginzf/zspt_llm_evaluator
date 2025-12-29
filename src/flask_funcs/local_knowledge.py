from pathlib import Path

from flask import Blueprint, request, jsonify, render_template_string
import os
import logging
import uuid
from env_config_init import settings
from src.sql_funs.local_knowledge_crud import LocalKnowledgeCrud
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
    """获取特定本地知识的详细信息"""
    try:
        with LocalKnowledgeCrud() as crud:
            # 获取本地知识详情
            knowledge_detail = crud.get_local_knowledge_detail(kno_id)
            logger.info(f"获取本地知识详情: {knowledge_detail}")
            if not knowledge_detail:
                return "未找到知识库信息", 404

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
        return "页面加载错误", 500
    return renderer.gen_knowledge_detail(local_files, knowledge_detail)


@local_knowledge_bp.route('/api/local_knowledge_detail/<kno_id>/<kno_name>')
def api_local_knowledge_detail(kno_id, kno_name):
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
