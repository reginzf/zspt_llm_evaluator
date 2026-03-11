"""
通用Flask路由工具函数模块
提供多个Flask路由文件中重复使用的通用功能
"""
import os
import json
import tempfile
import logging
import uuid
import datetime
from pathlib import Path
from flask import jsonify

from src.utils.minio_client import MinIOClient

logger = logging.getLogger(__name__)

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
    return f"{prefix}_{str(uuid.uuid4())[:length]}"


def handle_file_upload(files, target_directory, related_info=None, use_minio=True):
    """
    处理文件上传的通用函数，支持文件夹上传和数据集文件解析
    仅支持MinIO存储模式
    
    Args:
        files: 上传的文件列表
        target_directory: 目标目录（MinIO前缀）
        related_info: 相关信息（如知识库ID等）
        use_minio: 是否使用MinIO存储，默认True
        
    Returns:
        dict: 包含成功和失败文件信息的字典
    """
    success_count = 0
    failed_files = []
    success_file_names = []
    processed_datasets = []
    
    # 仅使用MinIO存储
    return _handle_file_upload_minio(files, target_directory, related_info)


def _handle_file_upload_minio(files, target_directory, related_info=None):
    """处理MinIO文件上传"""
    logger = logging.getLogger(__name__)
    success_count = 0
    failed_files = []
    success_file_names = []
    processed_datasets = []
    
    # 获取MinIO客户端
    minio_client = MinIOClient()
    
    # 确保目标目录前缀格式正确
    if target_directory and not target_directory.endswith('/'):
        target_directory = target_directory + '/'

    for file in files:
        if file and file.filename:
            try:
                filename = file.filename
                
                # 检查是否是数据集文件
                if _is_dataset_file(filename):
                    # 处理数据集文件
                    dataset_info = _process_dataset_file_minio(file, target_directory, minio_client)
                    if dataset_info:
                        processed_datasets.append(dataset_info)
                        success_count += 1
                        success_file_names.append(filename)
                        logger.info(f"成功处理数据集文件到MinIO: {filename}")
                    else:
                        failed_files.append(f"{filename} (数据集处理失败)")
                    continue
                
                # 生成MinIO对象名称
                object_name = target_directory + filename
                
                # 检查是否已存在同名文件，如果存在则重命名
                counter = 1
                name, ext = Path(filename).stem, Path(filename).suffix
                new_filename = None
                while minio_client.file_exists(object_name):
                    new_filename = f"{name}_{counter}{ext}"
                    object_name = target_directory + new_filename
                    counter += 1

                # 创建临时文件进行上传
                with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                    file.save(tmp_file.name)
                    tmp_file.close()
                    
                    # 上传到MinIO
                    if minio_client.upload_file(tmp_file.name, object_name):
                        if new_filename:
                            success_file_names.append(new_filename)
                        else:
                            success_file_names.append(filename)
                        success_count += 1
                        logger.info(f"文件上传到MinIO成功: {object_name}")
                    else:
                        failed_files.append(f"{filename} (MinIO上传失败)")
                        logger.error(f"文件上传到MinIO失败: {filename}")
                    
                    # 清理临时文件
                    try:
                        os.unlink(tmp_file.name)
                    except Exception as e:
                        logger.warning(f"清理临时文件失败: {e}")
                
            except Exception as e:
                logger.error(f"处理文件 {filename} 时出错: {str(e)}")
                failed_files.append(f"{filename} ({str(e)})")

    # 如果有处理的数据集，生成数据集信息
    if processed_datasets:
        _generate_dataset_info_minio(processed_datasets, target_directory, minio_client)
    
    message = f"成功上传 {success_count} 个文件到MinIO"
    if processed_datasets:
        message += f"，处理了 {len(processed_datasets)} 个数据集文件"
    if failed_files:
        message += f"，失败文件: {', '.join(failed_files)}"
    
    return {
        "success_file_names": success_file_names,
        "success_count": success_count,
        "failed_count": len(failed_files),
        "failed_files": failed_files,
        "processed_datasets": processed_datasets,
        "message": message,
        "storage_type": "minio"
    }


def _is_dataset_file(filename):
    """检查文件是否是数据集文件"""
    dataset_extensions = ['.arrow', '.jsonl', '.json', '.parquet', '.csv']
    filename_lower = filename.lower()
    
    # 检查扩展名
    for ext in dataset_extensions:
        if filename_lower.endswith(ext):
            return True
    
    # 检查是否是HuggingFace数据集文件
    dataset_keywords = ['dataset', 'train', 'test', 'validation', 'split']
    for keyword in dataset_keywords:
        if keyword in filename_lower:
            return True
            
    return False


def _process_dataset_file(file, target_directory):
    """处理数据集文件"""
    try:
        filename = file.filename
        file_path = Path(target_directory) / filename
        
        # 保存文件
        file.save(str(file_path))
        
        # 根据文件类型处理
        if filename.lower().endswith('.jsonl') or filename.lower().endswith('.json'):
            return _process_json_dataset(file_path, filename)
        elif filename.lower().endswith('.arrow'):
            return _process_arrow_dataset(file_path, filename)
        elif filename.lower().endswith('.parquet'):
            return _process_parquet_dataset(file_path, filename)
        elif filename.lower().endswith('.csv'):
            return _process_csv_dataset(file_path, filename)
        else:
            # 通用处理
            return {
                'filename': filename,
                'type': 'unknown',
                'size': os.path.getsize(file_path),
                'message': '文件已保存，但未进行特殊处理'
            }
            
    except Exception as e:
        logger.error(f"处理数据集文件 {filename} 时出错: {str(e)}")
        return None


def _process_json_dataset(file_path, filename):
    """处理JSON/JSONL数据集文件"""
    try:
        samples = []
        with open(file_path, 'r', encoding='utf-8') as f:
            # 尝试作为JSONL处理
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line:
                    try:
                        sample = json.loads(line)
                        samples.append(sample)
                    except json.JSONDecodeError:
                        # 如果不是JSONL，尝试作为完整JSON处理
                        f.seek(0)
                        try:
                            data = json.load(f)
                            if isinstance(data, list):
                                samples = data
                            else:
                                samples = [data]
                        except json.JSONDecodeError:
                            pass
                        break
        
        return {
            'filename': filename,
            'type': 'json/jsonl',
            'samples': len(samples),
            'size': os.path.getsize(file_path),
            'features': list(samples[0].keys()) if samples else []
        }
        
    except Exception as e:
        logger.error(f"处理JSON数据集 {filename} 时出错: {str(e)}")
        return {
            'filename': filename,
            'type': 'json/jsonl',
            'error': str(e)
        }


def _process_arrow_dataset(file_path, filename):
    """处理Arrow数据集文件"""
    try:
        import pyarrow as pa
        
        with pa.memory_map(str(file_path), 'rb') as source:
            reader = pa.ipc.open_stream(source)
            table = reader.read_all()
            
            return {
                'filename': filename,
                'type': 'arrow',
                'rows': table.num_rows,
                'columns': table.num_columns,
                'size': os.path.getsize(file_path),
                'schema': [str(field) for field in table.schema]
            }
            
    except ImportError:
        return {
            'filename': filename,
            'type': 'arrow',
            'error': 'pyarrow库未安装，无法读取Arrow文件'
        }
    except Exception as e:
        logger.error(f"处理Arrow数据集 {filename} 时出错: {str(e)}")
        return {
            'filename': filename,
            'type': 'arrow',
            'error': str(e)
        }


def _process_parquet_dataset(file_path, filename):
    """处理Parquet数据集文件"""
    try:
        import pandas as pd
        
        df = pd.read_parquet(file_path)
        
        return {
            'filename': filename,
            'type': 'parquet',
            'rows': len(df),
            'columns': len(df.columns),
            'size': os.path.getsize(file_path),
            'columns_list': list(df.columns)
        }
        
    except ImportError:
        return {
            'filename': filename,
            'type': 'parquet',
            'error': 'pandas库未安装，无法读取Parquet文件'
        }
    except Exception as e:
        logger.error(f"处理Parquet数据集 {filename} 时出错: {str(e)}")
        return {
            'filename': filename,
            'type': 'parquet',
            'error': str(e)
        }


def _process_csv_dataset(file_path, filename):
    """处理CSV数据集文件"""
    try:
        import pandas as pd
        
        df = pd.read_csv(file_path)
        
        return {
            'filename': filename,
            'type': 'csv',
            'rows': len(df),
            'columns': len(df.columns),
            'size': os.path.getsize(file_path),
            'columns_list': list(df.columns)
        }
        
    except ImportError:
        return {
            'filename': filename,
            'type': 'csv',
            'error': 'pandas库未安装，无法读取CSV文件'
        }
    except Exception as e:
        logger.error(f"处理CSV数据集 {filename} 时出错: {str(e)}")
        return {
            'filename': filename,
            'type': 'csv',
            'error': str(e)
        }


def _generate_dataset_info(processed_datasets, target_directory):
    """生成数据集信息文件"""
    info_file = Path(target_directory) / "dataset_info.json"
    
    info = {
        'total_datasets': len(processed_datasets),
        'datasets': processed_datasets,
        'generated_at': datetime.datetime.now().isoformat()
    }
    
    with open(info_file, 'w', encoding='utf-8') as f:
        json.dump(info, f, ensure_ascii=False, indent=2)


def _process_dataset_file_minio(file, target_directory, minio_client):
    """
    处理数据集文件并上传到MinIO
    
    Args:
        file: 上传的文件对象
        target_directory: MinIO中的目标目录前缀
        minio_client: MinIO客户端实例
        
    Returns:
        dict: 数据集信息字典，失败返回None
    """
    try:
        filename = file.filename
        
        # 创建临时文件保存上传的文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as tmp_file:
            file.save(tmp_file.name)
            tmp_file_path = tmp_file.name
        
        try:
            # 根据文件类型处理并获取信息
            if filename.lower().endswith('.jsonl') or filename.lower().endswith('.json'):
                dataset_info = _process_json_dataset(Path(tmp_file_path), filename)
            elif filename.lower().endswith('.arrow'):
                dataset_info = _process_arrow_dataset(Path(tmp_file_path), filename)
            elif filename.lower().endswith('.parquet'):
                dataset_info = _process_parquet_dataset(Path(tmp_file_path), filename)
            elif filename.lower().endswith('.csv'):
                dataset_info = _process_csv_dataset(Path(tmp_file_path), filename)
            else:
                # 通用处理
                dataset_info = {
                    'filename': filename,
                    'type': 'unknown',
                    'size': os.path.getsize(tmp_file_path),
                    'message': '文件已上传，但未进行特殊处理'
                }
            
            # 确保目标目录前缀格式正确
            if target_directory and not target_directory.endswith('/'):
                target_directory = target_directory + '/'
            
            # 生成MinIO对象名称
            object_name = target_directory + filename
            
            # 检查是否已存在同名文件，如果存在则重命名
            counter = 1
            name, ext = Path(filename).stem, Path(filename).suffix
            new_filename = None
            while minio_client.file_exists(object_name):
                new_filename = f"{name}_{counter}{ext}"
                object_name = target_directory + new_filename
                counter += 1
            
            # 上传到MinIO
            if minio_client.upload_file(tmp_file_path, object_name):
                # 更新数据集信息
                dataset_info['object_name'] = object_name
                dataset_info['storage_type'] = 'minio'
                if new_filename:
                    dataset_info['original_filename'] = filename
                    dataset_info['filename'] = new_filename
                logger.info(f"数据集文件上传到MinIO成功: {object_name}")
                return dataset_info
            else:
                logger.error(f"数据集文件上传到MinIO失败: {filename}")
                return None
                
        finally:
            # 清理临时文件
            try:
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
            except Exception as e:
                logger.warning(f"清理临时文件失败: {e}")
            
    except Exception as e:
        logger.error(f"处理数据集文件 {filename} 时出错: {str(e)}")
        return None


def _generate_dataset_info_minio(processed_datasets, target_directory, minio_client):
    """
    在MinIO中生成数据集信息文件
    
    Args:
        processed_datasets: 处理过的数据集列表
        target_directory: MinIO中的目标目录前缀
        minio_client: MinIO客户端实例
    """
    try:
        # 确保目标目录前缀格式正确
        if target_directory and not target_directory.endswith('/'):
            target_directory = target_directory + '/'
        
        # 创建数据集信息
        info = {
            'total_datasets': len(processed_datasets),
            'datasets': processed_datasets,
            'generated_at': datetime.datetime.now().isoformat()
        }
        
        # 创建临时JSON文件
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp_file:
            json.dump(info, tmp_file, ensure_ascii=False, indent=2)
            tmp_file_path = tmp_file.name
        
        try:
            # 上传到MinIO
            object_name = target_directory + "dataset_info.json"
            if minio_client.upload_file(tmp_file_path, object_name):
                logger.info(f"数据集信息文件上传到MinIO成功: {object_name}")
            else:
                logger.error(f"数据集信息文件上传到MinIO失败")
        finally:
            # 清理临时文件
            try:
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
            except Exception as e:
                logger.warning(f"清理临时文件失败: {e}")
                
    except Exception as e:
        logger.error(f"生成数据集信息文件时出错: {str(e)}")


def handle_qa_data_file_upload(files, group_id=None, related_info=None):
    """
    处理QA数据文件上传的通用函数，使用MinIO存储到qa_data文件组
    
    Args:
        files: 上传的文件列表
        group_id: 分组ID（可选）
        related_info: 相关信息字典（可选）
        
    Returns:
        dict: 包含上传结果的字典
    """
    from src.utils.minio_client import get_qa_raw_files_client
    
    logger = logging.getLogger(__name__)
    success_count = 0
    failed_files = []
    saved_files = []
    folder_name = None
    
    # 获取MinIO客户端（使用qa-raw-files存储桶）
    minio_client = get_qa_raw_files_client()
    
    # 构建目标前缀：qa_data/timestamp/
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    if group_id:
        target_prefix = f"qa_data/group_{group_id}/{timestamp}/"
    else:
        target_prefix = f"qa_data/{timestamp}/"
    
    for file in files:
        if file and file.filename:
            try:
                filename = file.filename
                
                # 检查文件名是否包含路径（文件夹上传时会有相对路径）
                if '/' in filename:
                    # 文件夹上传，保持目录结构
                    relative_path = filename
                    object_name = target_prefix + relative_path
                    # 提取文件夹名称
                    if folder_name is None:
                        folder_name = filename.split('/')[0]
                else:
                    # 单文件上传
                    relative_path = filename
                    object_name = target_prefix + filename
                
                # 创建临时文件
                with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                    file.save(tmp_file.name)
                    tmp_file_path = tmp_file.name
                
                try:
                    # 确保目录结构存在（MinIO自动处理）
                    # 上传到MinIO
                    if minio_client.upload_file(tmp_file_path, object_name):
                        saved_files.append({
                            'original_name': filename,
                            'object_name': object_name,
                            'relative_path': relative_path
                        })
                        success_count += 1
                        logger.info(f"QA数据文件上传成功: {object_name}")
                    else:
                        failed_files.append(f"{filename} (MinIO上传失败)")
                        logger.error(f"QA数据文件上传失败: {filename}")
                        
                finally:
                    # 清理临时文件
                    try:
                        if os.path.exists(tmp_file_path):
                            os.unlink(tmp_file_path)
                    except Exception as e:
                        logger.warning(f"清理临时文件失败: {e}")
                
            except Exception as e:
                logger.error(f"处理文件 {file.filename} 时出错: {str(e)}")
                failed_files.append(f"{file.filename} ({str(e)})")
    
    # 构建虚拟的本地路径（用于兼容原有接口）
    virtual_base_path = f"/minio/qa-raw-files/{target_prefix}"
    
    result = {
        'success': success_count > 0,
        'success_count': success_count,
        'failed_count': len(failed_files),
        'failed_files': failed_files,
        'saved_files': saved_files,
        'virtual_path': virtual_base_path,
        'target_prefix': target_prefix,
        'folder_name': folder_name,
        'is_folder': folder_name is not None,
        'storage_type': 'minio',
        'message': f'成功上传 {success_count} 个文件到MinIO' + 
                   (f'（文件夹: {folder_name}）' if folder_name else '') +
                   (f'，失败: {len(failed_files)}' if failed_files else '')
    }
    
    return result


def download_minio_file_to_temp(object_name, bucket_name=None):
    """
    从MinIO下载文件到临时目录
    
    Args:
        object_name: MinIO中的对象名称
        bucket_name: 存储桶名称，如果为None则使用默认存储桶
        
    Returns:
        str: 临时文件路径，失败返回None
    """
    try:
        from src.utils.minio_client import MinIOClient
        
        # 获取MinIO客户端
        minio_client = MinIOClient(bucket_name=bucket_name)
        
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


def cleanup_minio_temp_files(object_names, bucket_name=None):
    """
    清理MinIO中的临时文件
    
    Args:
        object_names: 对象名称列表或单个对象名称
        bucket_name: 存储桶名称，如果为None则使用默认存储桶
        
    Returns:
        int: 成功删除的文件数量
    """
    try:
        from src.utils.minio_client import MinIOClient
        
        # 获取MinIO客户端
        minio_client = MinIOClient(bucket_name=bucket_name)
        
        # 确保是列表
        if isinstance(object_names, str):
            object_names = [object_names]
        
        deleted_count = 0
        for object_name in object_names:
            try:
                if minio_client.delete_file(object_name):
                    deleted_count += 1
                    logger.info(f"成功删除MinIO文件: {object_name}")
                else:
                    logger.warning(f"删除MinIO文件失败: {object_name}")
            except Exception as e:
                logger.warning(f"删除MinIO文件时出错 {object_name}: {e}")
        
        return deleted_count
        
    except Exception as e:
        logger.error(f"清理MinIO临时文件失败: {e}")
        return 0


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

        binding_list = [crud._local_knowledge_bind_to_json(binding) for binding in bindings]
        res = []
        for binding_dict in binding_list:
            knowledge_id = binding_dict['knowledge_id']
            # 获取知识库名称
            knowledge_base = env_crud.get_knowledge_base(knowledge_id=knowledge_id)
            if not knowledge_base:
                return None
            binding_dict['knowledge_name'] = knowledge_base[0][1]
            res.append(binding_dict)
        return res


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
