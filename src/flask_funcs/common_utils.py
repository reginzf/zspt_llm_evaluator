"""
通用Flask路由工具函数模块
提供多个Flask路由文件中重复使用的通用功能
"""
import os
import logging
from flask import jsonify
from pathlib import Path
from env_config_init import settings


def validate_required_fields(data, required_fields):
    """
    验证必要字段是否存在
    
    Args:
        data: 请求数据字典
        required_fields: 必需字段列表
        
    Returns:
        str or None: 如果缺少字段返回字段名，否则返回None
    """
    for field in required_fields:
        if field not in data:
            return field
    return None


def execute_with_crud_operation(operation_func, success_message, error_message_prefix, logger=None):
    """
    执行数据库操作的通用函数
    
    Args:
        operation_func: 执行数据库操作的函数
        success_message: 成功消息
        error_message_prefix: 错误消息前缀
        logger: 日志记录器
        
    Returns:
        Flask响应对象
    """
    try:
        result = operation_func()
        if result:
            response = jsonify({'success': True, 'message': success_message})
        else:
            response = jsonify({'success': False, 'message': f'{error_message_prefix}失败'}), 400
    except Exception as e:
        error_msg = f'{error_message_prefix}时发生错误: {str(e)}'
        if logger:
            logger.error(error_msg)
        response = jsonify({'success': False, 'message': error_msg}), 500
    
    return response


def get_directory_structure(base_path, file_extension=None):
    """
    获取目录结构的通用函数
    
    Args:
        base_path: 基础路径
        file_extension: 文件扩展名过滤器（如'.json'）
        
    Returns:
        dict: 目录结构字典
    """
    directory_structure = {}
    
    if os.path.exists(base_path):
        for item in os.listdir(base_path):
            item_path = os.path.join(base_path, item)
            if os.path.isdir(item_path):
                # 如果是目录，获取该目录下的指定类型文件
                if file_extension:
                    files = [f for f in os.listdir(item_path) if f.endswith(file_extension)]
                    directory_structure[item] = files
                else:
                    directory_structure[item] = os.listdir(item_path)
            elif file_extension and item.endswith(file_extension):
                # 如果是根目录下的指定类型文件
                if '根目录' not in directory_structure:
                    directory_structure['根目录'] = []
                directory_structure['根目录'].append(item)
    
    return directory_structure


def safe_file_operation(file_path, operation='read'):
    """
    安全的文件操作函数
    
    Args:
        file_path: 文件路径
        operation: 操作类型 ('read', 'write', 'delete', 'exists')
        
    Returns:
        根据操作类型返回不同结果
    """
    try:
        if operation == 'exists':
            return os.path.exists(file_path)
        elif operation == 'delete':
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        elif operation == 'read':
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            return None
    except Exception as e:
        logging.error(f"文件操作失败 {operation} {file_path}: {str(e)}")
        return None


def generate_unique_id(prefix="id", length=8):
    """
    生成唯一ID的通用函数
    
    Args:
        prefix: ID前缀
        length: 随机部分长度
        
    Returns:
        str: 生成的唯一ID
    """
    import uuid
    return f"{prefix}_{str(uuid.uuid4())[:length]}"


def handle_file_upload(files, target_directory, related_info=None):
    """
    处理文件上传的通用函数
    
    Args:
        files: 上传的文件列表
        target_directory: 目标目录
        related_info: 相关信息（如知识库ID等）
        
    Returns:
        dict: 包含成功和失败文件信息的字典
    """
    success_count = 0
    failed_files = []
    
    # 确保目录存在
    Path(target_directory).mkdir(parents=True, exist_ok=True)
    
    for file in files:
        if file and file.filename:
            # 验证文件类型（可以根据需要添加更多类型）
            filename = file.filename

            # 构建安全的文件路径
            file_path = Path(target_directory) / filename
            
            # 检查是否已存在同名文件，如果存在则重命名
            counter = 1
            name, ext = file_path.stem, file_path.suffix
            while file_path.exists():
                new_filename = f"{name}_{counter}{ext}"
                file_path = Path(target_directory) / new_filename
                counter += 1

            # 保存文件到本地文件夹
            file.save(str(file_path))
            
            success_count += 1
    
    return {
        "success_count": success_count,
        "failed_count": len(failed_files),
        "failed_files": failed_files,
        "message": f"成功上传 {success_count} 个文件" + (f"，失败文件: {', '.join(failed_files)}" if failed_files else "")
    }


def render_template_with_version(template_name, css_static_dir="css", js_static_dir="js", **kwargs):
    """
    带版本参数的模板渲染函数，用于避免静态资源缓存问题
    
    Args:
        template_name: 模板名称
        css_static_dir: CSS静态文件目录
        js_static_dir: JS静态文件目录
        **kwargs: 传递给模板的其他参数
        
    Returns:
        渲染后的模板
    """
    import os
    from flask import render_template
    
    # 生成带版本参数的静态资源路径
    css_path = f"/static/{css_static_dir}/local_knowledge.css?version={os.urandom(4).hex()}"
    js_url = f"/static/{js_static_dir}/local_knowledge.js?version={os.urandom(4).hex()}"
    
    # 如果有额外的CSS和JS参数
    detail_css_path = f"/static/{css_static_dir}/local_knowledge_detail.css?version={os.urandom(4).hex()}"
    detail_js_url = f"/static/{js_static_dir}/local_knowledge_detail.js?version={os.urandom(4).hex()}"
    
    # 将路径添加到参数中
    kwargs.update({
        'css_path': css_path,
        'js_url': js_url,
        'detail_css_path': detail_css_path,
        'detail_js_url': detail_js_url
    })
    
    return render_template(template_name, **kwargs)


def get_knowledge_base_binding_info(kno_id, local_crud_class, env_crud_class):
    """
    获取知识库绑定信息的通用函数
    
    Args:
        kno_id: 知识库ID
        local_crud_class: 本地知识库CRUD类
        env_crud_class: 环境CRUD类
        
    Returns:
        dict or None: 绑定信息或None
    """
    with local_crud_class() as crud, env_crud_class() as env_crud:
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


def safe_execute_with_rollback(operation_func, rollback_func=None, logger=None):
    """
    安全执行操作并提供回滚功能的通用函数
    
    Args:
        operation_func: 要执行的操作函数
        rollback_func: 回滚函数
        logger: 日志记录器
        
    Returns:
        操作结果
    """
    try:
        result = operation_func()
        return result
    except Exception as e:
        if rollback_func:
            try:
                rollback_func()
            except Exception as rollback_error:
                if logger:
                    logger.error(f"回滚操作也失败: {str(rollback_error)}")
        
        if logger:
            logger.error(f"操作失败: {str(e)}")
        
        raise e