# -*- coding: utf-8 -*-
"""
问答对管理API模块

此模块提供问答对数据的完整CRUD API接口，
包括问答对的创建、查询、更新、删除等功能。
"""
from flask import Blueprint, request, jsonify
import logging
import os
import tempfile
from src.sql_funs.ai_qa_data_crud import AIQADataManager
from src.sql_funs.ai_qa_data_crud_enhanced import EnhancedAIQADataManager, DatasetPreview, ImportConfig
from src.sql_funs.ai_qa_data_group_crud import AIQADataGroupManager
from src.flask_funcs.common_utils import validate_required_fields

# 创建logger
logger = logging.getLogger(__name__)

# 创建蓝图
qa_data_bp = Blueprint('qa_data', __name__)


@qa_data_bp.route('/api/qa/groups/<int:group_id>/items', methods=['GET'])
def get_qa_data_list(group_id: int):
    """
    分页查询指定组的问答对列表
    
    Args:
        group_id: 分组ID
        
    Query Parameters:
        page: 页码，默认1
        limit: 每页数量，默认20
        question_type: 问题类型筛选
        difficulty_level: 难度等级筛选
        category: 分类筛选
        language: 语言筛选
        question_keyword: 问题关键词搜索
        context_keyword: 上下文关键词搜索
        order_by: 排序字段，默认created_at DESC
        
    Returns:
        JSON: {total: int, page: int, limit: int, pages: int, rows: list}
    """
    try:
        # 获取查询参数
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        question_type = request.args.get('question_type')
        difficulty_level = request.args.get('difficulty_level')
        category = request.args.get('category')
        language = request.args.get('language')
        question_keyword = request.args.get('question_keyword')
        context_keyword = request.args.get('context_keyword')
        order_by = request.args.get('order_by', 'created_at DESC')
        
        # 处理难度等级参数
        difficulty = None
        if difficulty_level:
            try:
                difficulty = int(difficulty_level)
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': '难度等级必须是整数'
                }), 400
        
        # 计算偏移量
        offset = (page - 1) * limit
        
        with AIQADataManager() as manager:
            # 检查分组是否存在
            with AIQADataGroupManager() as group_manager:
                if not group_manager.group_exists(group_id):
                    return jsonify({
                        'success': False,
                        'message': f'分组不存在: ID={group_id}'
                    }), 404
            
            # 获取问答对列表
            qa_data_list = manager.list_qa_data(
                group_id=group_id,
                question_type=question_type,
                difficulty_level=difficulty,
                category=category,
                language=language,
                question_keyword=question_keyword,
                context_keyword=context_keyword,
                order_by=order_by,
                limit=limit,
                offset=offset
            )
            
            # 获取总数
            total = manager.count_qa_data(
                group_id=group_id,
                question_type=question_type,
                difficulty_level=difficulty,
                category=category,
                language=language,
                question=question_keyword,
                context=context_keyword
            )
            
            # 计算总页数
            pages = (total + limit - 1) // limit if limit > 0 else 0
            
            return jsonify({
                'success': True,
                'data': {
                    'total': total,
                    'page': page,
                    'limit': limit,
                    'pages': pages,
                    'rows': qa_data_list
                }
            })
            
    except Exception as e:
        logger.error(f"获取问答对列表失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取问答对列表失败: {str(e)}'
        }), 500


@qa_data_bp.route('/api/qa/groups/<int:group_id>/items', methods=['POST'])
def create_qa_data(group_id: int):
    """
    创建问答对
    
    Args:
        group_id: 分组ID
        
    Request Body:
        question: 问题文本（必填）
        answers: 答案，支持字符串、字符串列表或字典格式（必填）
        context: 上下文/背景信息
        question_type: 问题类型（factual/contextual/conceptual/reasoning/application/multi_choice）
        source_dataset: 源数据集名称
        hf_dataset_id: HuggingFace原始ID
        language: 语言，默认'zh'
        difficulty_level: 难度等级（1-10）
        category: 分类标签
        sub_category: 子分类
        tags: 标签列表
        fixed_metadata: 固定元数据
        dynamic_metadata: 动态元数据
        
    Returns:
        JSON: {success: bool, qa_id: int, message: str}
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求体不能为空'
            }), 400
        
        # 验证必要字段
        required_fields = ['question', 'answers']
        missing_field = validate_required_fields(data, required_fields)
        if missing_field:
            return jsonify({
                'success': False,
                'message': f'缺少必要字段: {missing_field}'
            }), 400
        
        # 提取参数
        question = data.get('question')
        answers = data.get('answers')
        context = data.get('context')
        question_type = data.get('question_type')
        source_dataset = data.get('source_dataset')
        hf_dataset_id = data.get('hf_dataset_id')
        language = data.get('language', 'zh')
        difficulty_level = data.get('difficulty_level')
        category = data.get('category')
        sub_category = data.get('sub_category')
        tags = data.get('tags', [])
        fixed_metadata = data.get('fixed_metadata', {})
        dynamic_metadata = data.get('dynamic_metadata', {})
        
        # 验证问题类型
        if question_type:
            valid_question_types = ['factual', 'contextual', 'conceptual', 'reasoning', 'application', 'multi_choice']
            if question_type not in valid_question_types:
                return jsonify({
                    'success': False,
                    'message': f'无效的问题类型: {question_type}，有效值: {", ".join(valid_question_types)}'
                }), 400
        
        # 验证难度等级
        if difficulty_level is not None:
            try:
                difficulty = int(difficulty_level)
                if not (1 <= difficulty <= 10):
                    return jsonify({
                        'success': False,
                        'message': '难度等级必须在1-10之间'
                    }), 400
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': '难度等级必须是整数'
                }), 400
        
        with AIQADataManager() as manager:
            # 检查分组是否存在
            with AIQADataGroupManager() as group_manager:
                if not group_manager.group_exists(group_id):
                    return jsonify({
                        'success': False,
                        'message': f'分组不存在: ID={group_id}'
                    }), 404
            
            # 创建问答对
            qa_id = manager.create_qa_data(
                group_id=group_id,
                question=question,
                answers=answers,
                context=context,
                question_type=question_type,
                source_dataset=source_dataset,
                hf_dataset_id=hf_dataset_id,
                language=language,
                difficulty_level=difficulty_level,
                category=category,
                sub_category=sub_category,
                tags=tags,
                fixed_metadata=fixed_metadata,
                dynamic_metadata=dynamic_metadata
            )
            
            if qa_id:
                return jsonify({
                    'success': True,
                    'qa_id': qa_id,
                    'message': '问答对创建成功'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '问答对创建失败'
                }), 400
            
    except Exception as e:
        logger.error(f"创建问答对失败: {e}")
        return jsonify({
            'success': False,
            'message': f'创建问答对失败: {str(e)}'
        }), 500


@qa_data_bp.route('/api/qa/items/<int:qa_id>', methods=['GET'])
def get_qa_data_detail(qa_id: int):
    """
    获取问答对详情
    
    Args:
        qa_id: 问答对ID
        
    Returns:
        JSON: {success: bool, data: dict, message: str}
    """
    try:
        with AIQADataManager() as manager:
            qa_data = manager.get_qa_data_by_id(qa_id)
            
            if not qa_data:
                return jsonify({
                    'success': False,
                    'message': f'问答对不存在: ID={qa_id}'
                }), 404
            
            return jsonify({
                'success': True,
                'data': qa_data,
                'message': '获取问答对详情成功'
            })
            
    except Exception as e:
        logger.error(f"获取问答对详情失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取问答对详情失败: {str(e)}'
        }), 500


@qa_data_bp.route('/api/qa/items/<int:qa_id>', methods=['PUT'])
def update_qa_data(qa_id: int):
    """
    更新问答对信息
    
    Args:
        qa_id: 问答对ID
        
    Request Body:
        question: 问题文本
        answers: 答案
        context: 上下文/背景信息
        question_type: 问题类型
        source_dataset: 源数据集名称
        hf_dataset_id: HuggingFace原始ID
        language: 语言
        difficulty_level: 难度等级
        category: 分类标签
        sub_category: 子分类
        tags: 标签列表
        fixed_metadata: 固定元数据
        dynamic_metadata: 动态元数据
        
    Returns:
        JSON: {success: bool, message: str}
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求体不能为空'
            }), 400
        
        with AIQADataManager() as manager:
            # 检查问答对是否存在
            if not manager.qa_data_exists(qa_id):
                return jsonify({
                    'success': False,
                    'message': f'问答对不存在: ID={qa_id}'
                }), 404
            
            # 验证问题类型
            if 'question_type' in data:
                valid_question_types = ['factual', 'contextual', 'conceptual', 'reasoning', 'application', 'multi_choice']
                if data['question_type'] not in valid_question_types:
                    return jsonify({
                        'success': False,
                        'message': f'无效的问题类型: {data["question_type"]}，有效值: {", ".join(valid_question_types)}'
                    }), 400
            
            # 验证难度等级
            if 'difficulty_level' in data and data['difficulty_level'] is not None:
                try:
                    difficulty = int(data['difficulty_level'])
                    if not (1 <= difficulty <= 10):
                        return jsonify({
                            'success': False,
                            'message': '难度等级必须在1-10之间'
                        }), 400
                except ValueError:
                    return jsonify({
                        'success': False,
                        'message': '难度等级必须是整数'
                    }), 400
            
            # 更新问答对
            success = manager.update_qa_data(qa_id, **data)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': '问答对更新成功'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '问答对更新失败'
                }), 400
            
    except Exception as e:
        logger.error(f"更新问答对失败: {e}")
        return jsonify({
            'success': False,
            'message': f'更新问答对失败: {str(e)}'
        }), 500


@qa_data_bp.route('/api/qa/items/<int:qa_id>', methods=['DELETE'])
def delete_qa_data(qa_id: int):
    """
    删除问答对
    
    Args:
        qa_id: 问答对ID
        
    Returns:
        JSON: {success: bool, message: str}
    """
    try:
        with AIQADataManager() as manager:
            # 检查问答对是否存在
            if not manager.qa_data_exists(qa_id):
                return jsonify({
                    'success': False,
                    'message': f'问答对不存在: ID={qa_id}'
                }), 404
            
            # 删除问答对
            success = manager.delete_qa_data(qa_id)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': '问答对删除成功'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '问答对删除失败'
                }), 400
            
    except Exception as e:
        logger.error(f"删除问答对失败: {e}")
        return jsonify({
            'success': False,
            'message': f'删除问答对失败: {str(e)}'
        }), 500


@qa_data_bp.route('/api/qa/groups/<int:group_id>/items/batch-delete', methods=['POST'])
def batch_delete_qa_data(group_id: int):
    """
    批量删除问答对
    
    Args:
        group_id: 分组ID
        
    Request Body:
        ids: 问答对ID列表（必填）
        
    Returns:
        JSON: {success: bool, data: {deleted_count: int}, message: str}
    """
    try:
        data = request.get_json()
        
        # 验证必填字段
        if not data or 'ids' not in data:
            return jsonify({
                'success': False,
                'message': '缺少必填字段: ids'
            }), 400
        
        ids = data['ids']
        if not isinstance(ids, list) or len(ids) == 0:
            return jsonify({
                'success': False,
                'message': 'ids必须是非空列表'
            }), 400
        
        # 检查分组是否存在
        with AIQADataGroupManager() as group_manager:
            if not group_manager.group_exists(group_id):
                return jsonify({
                    'success': False,
                    'message': f'分组不存在: ID={group_id}'
                }), 404
        
        # 批量删除问答对
        deleted_count = 0
        failed_ids = []
        
        with AIQADataManager() as manager:
            for qa_id in ids:
                try:
                    # 检查问答对是否属于该分组
                    qa_data = manager.get_qa_data_by_id(qa_id)
                    if qa_data and qa_data.get('group_id') == group_id:
                        if manager.delete_qa_data(qa_id):
                            deleted_count += 1
                        else:
                            failed_ids.append(qa_id)
                    else:
                        failed_ids.append(qa_id)
                except Exception as e:
                    logger.warning(f"删除问答对失败 ID={qa_id}: {e}")
                    failed_ids.append(qa_id)
        
        logger.info(f"批量删除完成: 成功={deleted_count}, 失败={len(failed_ids)}")
        
        return jsonify({
            'success': True,
            'message': f'成功删除 {deleted_count} 个问答对',
            'data': {
                'deleted_count': deleted_count,
                'failed_count': len(failed_ids),
                'failed_ids': failed_ids
            }
        })
        
    except Exception as e:
        logger.error(f"批量删除问答对失败: {e}")
        return jsonify({
            'success': False,
            'message': f'批量删除问答对失败: {str(e)}'
        }), 500


@qa_data_bp.route('/api/qa/groups/<int:group_id>/items/batch', methods=['POST'])
def batch_create_qa_data(group_id: int):
    """
    批量创建问答对
    
    Args:
        group_id: 分组ID
        
    Request Body:
        items: 问答对数据列表（必填）
        
    Returns:
        JSON: {success: bool, stats: dict, message: str}
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求体不能为空'
            }), 400
        
        items = data.get('items')
        if not items or not isinstance(items, list):
            return jsonify({
                'success': False,
                'message': 'items字段必须是非空列表'
            }), 400
        
        # 为每个项目添加group_id
        for item in items:
            item['group_id'] = group_id
        
        with AIQADataManager() as manager:
            # 检查分组是否存在
            with AIQADataGroupManager() as group_manager:
                if not group_manager.group_exists(group_id):
                    return jsonify({
                        'success': False,
                        'message': f'分组不存在: ID={group_id}'
                    }), 404
            
            # 批量创建
            stats = manager.batch_create_qa_data(items)
            
            return jsonify({
                'success': True,
                'stats': {
                    'total': stats.total,
                    'success': stats.success,
                    'failed': stats.failed,
                    'skipped': stats.skipped,
                    'duration': stats.duration
                },
                'message': f'批量创建完成，成功{stats.success}条，失败{stats.failed}条'
            })
            
    except Exception as e:
        logger.error(f"批量创建问答对失败: {e}")
        return jsonify({
            'success': False,
            'message': f'批量创建问答对失败: {str(e)}'
        }), 500


@qa_data_bp.route('/api/qa/items/search', methods=['GET'])
def search_similar_questions():
    """
    搜索相似问题
    
    Query Parameters:
        question: 搜索关键词（必填）
        group_id: 限制在特定分组内搜索
        limit: 返回结果数量，默认10
        
    Returns:
        JSON: {success: bool, data: list, message: str}
    """
    try:
        question = request.args.get('question')
        if not question:
            return jsonify({
                'success': False,
                'message': 'question参数不能为空'
            }), 400
        
        group_id = request.args.get('group_id')
        limit = int(request.args.get('limit', 10))
        
        # 处理group_id参数
        group_id_int = None
        if group_id:
            try:
                group_id_int = int(group_id)
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'group_id必须是整数'
                }), 400
        
        with AIQADataManager() as manager:
            # 搜索相似问题
            similar_questions = manager.search_similar_questions(
                question=question,
                group_id=group_id_int,
                limit=limit
            )
            
            return jsonify({
                'success': True,
                'data': similar_questions,
                'message': '搜索成功'
            })
            
    except Exception as e:
        logger.error(f"搜索相似问题失败: {e}")
        return jsonify({
            'success': False,
            'message': f'搜索相似问题失败: {str(e)}'
        }), 500


@qa_data_bp.route('/api/qa/groups/<int:group_id>/items/import/huggingface', methods=['POST'])
def import_from_huggingface(group_id: int):
    """
    从HuggingFace数据集导入问答对
    
    Args:
        group_id: 分组ID
        
    Request Body:
        dataset_path: HuggingFace数据集路径或本地路径（必填）
        batch_size: 批次大小，默认1000
        transform_func: 数据转换函数（可选，需要序列化）
        
    Returns:
        JSON: {success: bool, stats: dict, message: str}
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求体不能为空'
            }), 400
        
        dataset_path = data.get('dataset_path')
        if not dataset_path:
            return jsonify({
                'success': False,
                'message': 'dataset_path参数不能为空'
            }), 400
        
        batch_size = data.get('batch_size', 1000)
        
        with AIQADataManager() as manager:
            # 检查分组是否存在
            with AIQADataGroupManager() as group_manager:
                if not group_manager.group_exists(group_id):
                    return jsonify({
                        'success': False,
                        'message': f'分组不存在: ID={group_id}'
                    }), 404
            
            # 导入数据
            stats = manager.import_from_huggingface(
                dataset_path=dataset_path,
                group_id=group_id,
                batch_size=batch_size
            )
            
            return jsonify({
                'success': True,
                'stats': {
                    'total': stats.total,
                    'success': stats.success,
                    'failed': stats.failed,
                    'skipped': stats.skipped,
                    'duration': stats.duration,
                    'error_count': len(stats.errors)
                },
                'message': f'导入完成，成功{stats.success}条，失败{stats.failed}条'
            })
            
    except Exception as e:
        logger.error(f"从HuggingFace导入数据失败: {e}")
        return jsonify({
            'success': False,
            'message': f'从HuggingFace导入数据失败: {str(e)}'
        }), 500


@qa_data_bp.route('/api/qa/groups/<int:group_id>/items/import/upload', methods=['POST'])
def upload_huggingface_file(group_id: int):
    """
    上传HuggingFace数据集文件或文件夹到MinIO
    
    Args:
        group_id: 分组ID
        
    Request Form:
        file: 上传的文件（必填，支持多文件上传）
        
    Returns:
        JSON: {success: bool, file_path: str, message: str}
    """
    try:
        # 检查文件是否上传
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': '没有上传文件'
            }), 400
        
        # 获取所有上传的文件（支持多文件上传）
        uploaded_files = request.files.getlist('file')
        
        # 检查是否有文件
        if not uploaded_files or all(f.filename == '' for f in uploaded_files):
            return jsonify({
                'success': False,
                'message': '没有选择文件'
            }), 400
        
        # 检查分组是否存在
        with AIQADataGroupManager() as group_manager:
            if not group_manager.group_exists(group_id):
                return jsonify({
                    'success': False,
                    'message': f'分组不存在: ID={group_id}'
                }), 404
        
        # 使用MinIO上传文件
        from src.flask_funcs.common_utils import handle_qa_data_file_upload
        
        result = handle_qa_data_file_upload(
            files=uploaded_files,
            group_id=group_id,
            related_info={'upload_type': 'huggingface_dataset'}
        )
        
        if not result['success']:
            return jsonify({
                'success': False,
                'message': result['message']
            }), 400
        
        # 返回MinIO路径信息
        return jsonify({
            'success': True,
            'file_path': result['virtual_path'],  # 虚拟路径用于兼容
            'minio_prefix': result['target_prefix'],  # MinIO前缀
            'saved_files': result['saved_files'],  # 保存的文件列表
            'is_folder': result['is_folder'],
            'folder_name': result['folder_name'],
            'file_count': result['success_count'],
            'storage_type': 'minio',
            'message': result['message']
        })
            
    except Exception as e:
        logger.error(f"上传HuggingFace文件失败: {e}")
        return jsonify({
            'success': False,
            'message': f'上传文件失败: {str(e)}'
        }), 500


@qa_data_bp.route('/api/qa/groups/<int:group_id>/items/import/preview', methods=['POST'])
def preview_huggingface_dataset(group_id: int):
    """
    预览HuggingFace数据集（支持MinIO存储）
    
    Args:
        group_id: 分组ID
        
    Request Body:
        file_path: 文件路径（必填，支持MinIO虚拟路径或本地路径）
        minio_prefix: MinIO前缀（可选，用于从MinIO下载）
        saved_files: 保存的文件列表（可选，包含MinIO对象名）
        preview_rows: 预览行数，默认5
        
    Returns:
        JSON: {success: bool, preview: dict, message: str}
    """
    temp_downloaded_files = []
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求体不能为空'
            }), 400
        
        file_path = data.get('file_path')
        if not file_path:
            return jsonify({
                'success': False,
                'message': 'file_path参数不能为空'
            }), 400
        
        preview_rows = data.get('preview_rows', 5)
        minio_prefix = data.get('minio_prefix')
        saved_files = data.get('saved_files', [])
        
        # 检查分组是否存在
        with AIQADataGroupManager() as group_manager:
            if not group_manager.group_exists(group_id):
                return jsonify({
                    'success': False,
                    'message': f'分组不存在: ID={group_id}'
                }), 404
        
        # 判断是否为MinIO路径
        is_minio_path = '/minio/' in file_path or minio_prefix is not None
        
        if is_minio_path and saved_files:
            # 从MinIO下载文件到临时目录
            from src.flask_funcs.common_utils import download_minio_file_to_temp
            from src.utils.minio_client import get_qa_raw_files_client
            
            minio_client = get_qa_raw_files_client()
            
            # 创建临时目录
            temp_dir = tempfile.mkdtemp(prefix='qa_preview_')
            
            # 下载所有文件
            for file_info in saved_files:
                object_name = file_info.get('object_name')
                relative_path = file_info.get('relative_path', file_info.get('original_name'))
                
                if object_name:
                    # 下载文件
                    temp_path = download_minio_file_to_temp(object_name, bucket_name='qa-raw-files')
                    if temp_path:
                        # 构建目标路径保持目录结构
                        target_path = os.path.join(temp_dir, relative_path)
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        # 移动文件到正确位置
                        import shutil
                        shutil.move(temp_path, target_path)
                        temp_downloaded_files.append(target_path)
                        logger.info(f"文件下载并移动成功: {target_path}")
                    else:
                        logger.error(f"从MinIO下载文件失败: {object_name}")
            
            # 使用临时目录作为预览路径
            if temp_downloaded_files:
                preview_path = temp_dir
            else:
                return jsonify({
                    'success': False,
                    'message': '从MinIO下载文件失败'
                }), 500
        else:
            # 使用本地路径
            preview_path = file_path
        
        # 预览数据集
        with EnhancedAIQADataManager() as manager:
            preview = manager.preview_huggingface_dataset(preview_path, preview_rows)
            
            if preview.error:
                return jsonify({
                    'success': False,
                    'message': preview.error
                }), 400
            
            # 获取智能映射建议
            suggestions = manager.get_smart_mapping_suggestions(preview.columns)
            
            return jsonify({
                'success': True,
                'preview': {
                    'file_path': preview.file_path,
                    'total_records': preview.total_records,
                    'preview_rows': preview.preview_rows,
                    'columns': preview.columns,
                    'suggestions': suggestions
                },
                'temp_path': preview_path if is_minio_path else None,
                'message': '数据集预览成功'
            })
            
    except Exception as e:
        logger.error(f"预览HuggingFace数据集失败: {e}")
        return jsonify({
            'success': False,
            'message': f'预览数据集失败: {str(e)}'
        }), 500
    finally:
        # 清理临时下载的文件（保留临时目录供后续导入使用）
        # 临时目录将在 cleanup_import_files 中清理
        pass


@qa_data_bp.route('/api/qa/groups/<int:group_id>/items/import/execute', methods=['POST'])
def execute_import_with_mapping(group_id: int):
    """
    执行带字段映射的导入（支持MinIO存储）
    
    Args:
        group_id: 分组ID
        
    Request Body:
        file_path: 文件路径（必填，支持本地路径或MinIO虚拟路径）
        mapping: 字段映射配置（必填）
        minio_prefix: MinIO前缀（可选）
        saved_files: 保存的文件列表（可选，包含MinIO对象名）
        temp_path: 临时目录路径（可选，预览时已下载）
        options: 导入选项
            - batch_size: 批次大小，默认1000
            - skip_rows: 跳过的行数，默认0
            - unmapped_fields: 未映射字段处理方式，默认'ignore'
        
    Returns:
        JSON: {success: bool, stats: dict, message: str}
    """
    temp_downloaded_files = []
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求体不能为空'
            }), 400
        
        file_path = data.get('file_path')
        if not file_path:
            return jsonify({
                'success': False,
                'message': 'file_path参数不能为空'
            }), 400
        
        mapping = data.get('mapping')
        if not mapping:
            return jsonify({
                'success': False,
                'message': 'mapping参数不能为空'
            }), 400
        
        options = data.get('options', {})
        minio_prefix = data.get('minio_prefix')
        saved_files = data.get('saved_files', [])
        temp_path = data.get('temp_path')
        
        # 检查分组是否存在
        with AIQADataGroupManager() as group_manager:
            if not group_manager.group_exists(group_id):
                return jsonify({
                    'success': False,
                    'message': f'分组不存在: ID={group_id}'
                }), 404
        
        # 判断是否为MinIO路径
        is_minio_path = '/minio/' in file_path or minio_prefix is not None
        
        if is_minio_path:
            if temp_path and os.path.exists(temp_path):
                # 使用预览时已经下载的临时目录
                import_path = temp_path
                logger.info(f"使用预览时下载的临时目录: {import_path}")
            else:
                # 需要从MinIO下载文件
                from src.flask_funcs.common_utils import download_minio_file_to_temp
                
                # 创建临时目录
                temp_dir = tempfile.mkdtemp(prefix='qa_import_')
                
                # 下载所有文件
                for file_info in saved_files:
                    object_name = file_info.get('object_name')
                    relative_path = file_info.get('relative_path', file_info.get('original_name'))
                    
                    if object_name:
                        temp_file_path = download_minio_file_to_temp(object_name, bucket_name='qa-raw-files')
                        if temp_file_path:
                            # 构建目标路径保持目录结构
                            target_path = os.path.join(temp_dir, relative_path)
                            os.makedirs(os.path.dirname(target_path), exist_ok=True)
                            # 移动文件到正确位置
                            import shutil
                            shutil.move(temp_file_path, target_path)
                            temp_downloaded_files.append(target_path)
                            logger.info(f"文件下载并移动成功: {target_path}")
                        else:
                            logger.error(f"从MinIO下载文件失败: {object_name}")
                
                if not temp_downloaded_files:
                    return jsonify({
                        'success': False,
                        'message': '从MinIO下载文件失败'
                    }), 500
                
                import_path = temp_dir
        else:
            # 使用本地路径
            import_path = file_path
        
        # 创建导入配置
        config = ImportConfig(
            file_path=import_path,
            group_id=group_id,
            mapping=mapping,
            options=options
        )
        
        # 执行导入
        with EnhancedAIQADataManager() as manager:
            stats = manager.import_with_mapping(config)
            
            return jsonify({
                'success': True,
                'stats': {
                    'total': stats.total,
                    'success': stats.success,
                    'failed': stats.failed,
                    'skipped': stats.skipped,
                    'duration': stats.duration,
                    'error_count': len(stats.errors),
                    'errors': stats.errors[:10]  # 只返回前10个错误
                },
                'temp_path': import_path if is_minio_path else None,
                'message': f'导入完成，成功{stats.success}条，失败{stats.failed}条'
            })
            
    except Exception as e:
        logger.error(f"执行导入失败: {e}")
        return jsonify({
            'success': False,
            'message': f'执行导入失败: {str(e)}'
        }), 500


@qa_data_bp.route('/api/qa/groups/<int:group_id>/items/import/cleanup', methods=['POST'])
def cleanup_import_files(group_id: int):
    """
    清理导入的临时文件（支持本地和MinIO存储）
    
    Args:
        group_id: 分组ID
        
    Request Body:
        file_path: 文件路径（必填，支持本地路径或MinIO虚拟路径）
        minio_prefix: MinIO前缀（可选，用于清理MinIO文件）
        saved_files: 保存的文件列表（可选，包含MinIO对象名）
        temp_path: 临时目录路径（可选，用于清理本地临时文件）
        
    Returns:
        JSON: {success: bool, message: str}
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求体不能为空'
            }), 400
        
        file_path = data.get('file_path')
        if not file_path:
            return jsonify({
                'success': False,
                'message': 'file_path参数不能为空'
            }), 400
        
        minio_prefix = data.get('minio_prefix')
        saved_files = data.get('saved_files', [])
        temp_path = data.get('temp_path')
        
        # 判断是否为MinIO路径
        is_minio_path = '/minio/' in file_path or minio_prefix is not None
        
        cleanup_messages = []
        
        # 清理MinIO文件
        if is_minio_path and saved_files:
            from src.flask_funcs.common_utils import cleanup_minio_temp_files
            
            object_names = [f.get('object_name') for f in saved_files if f.get('object_name')]
            if object_names:
                deleted_count = cleanup_minio_temp_files(object_names, bucket_name='qa-raw-files')
                cleanup_messages.append(f'MinIO文件已清理: {deleted_count}个')
        
        # 清理本地临时文件
        if temp_path and os.path.exists(temp_path):
            try:
                import shutil
                shutil.rmtree(temp_path)
                cleanup_messages.append(f'本地临时目录已清理: {temp_path}')
            except Exception as e:
                logger.warning(f"清理本地临时目录失败: {e}")
                cleanup_messages.append(f'本地临时目录清理失败: {e}')
        
        # 如果传入的是本地路径，也尝试清理
        if not is_minio_path and os.path.exists(file_path):
            try:
                with EnhancedAIQADataManager() as manager:
                    manager.cleanup_temp_files(file_path)
                    cleanup_messages.append('本地文件已清理')
            except Exception as e:
                logger.warning(f"清理本地文件失败: {e}")
        
        return jsonify({
            'success': True,
            'message': '文件清理完成' + (': ' + '; '.join(cleanup_messages) if cleanup_messages else '')
        })
            
    except Exception as e:
        logger.error(f"清理文件失败: {e}")
        return jsonify({
            'success': False,
            'message': f'清理文件失败: {str(e)}'
        }), 500