# -*- coding: utf-8 -*-
"""
问答对组管理API模块

此模块提供问答对组的完整CRUD API接口，
包括分组的创建、查询、更新、删除、激活/停用等功能。
"""
from flask import Blueprint, request, jsonify
import logging
from typing import Dict, Any, Optional
from src.sql_funs.ai_qa_data_group_crud import AIQADataGroupManager
from src.flask_funcs.common_utils import validate_required_fields
from src.flask_funcs.reports.flask_qa_renderer import render_qa_groups_page, render_qa_group_detail_page, render_error_page

# 创建logger
logger = logging.getLogger(__name__)

# 创建蓝图
qa_data_group_bp = Blueprint('qa_data_group', __name__)

# 常量定义
VALID_TEST_TYPES = ['accuracy', 'performance', 'robustness', 'comprehensive', 'custom']
VALID_LANGUAGES = ['zh', 'en', 'multi']


def validate_group_data(data, is_update=False):
    """
    验证分组数据的有效性
    
    Args:
        data: 分组数据
        is_update: 是否为更新操作
        
    Returns:
        tuple: (是否有效, 错误消息)
    """
    # 验证测试类型
    if 'test_type' in data:
        if data['test_type'] not in VALID_TEST_TYPES:
            return False, f'无效的测试类型: {data["test_type"]}，有效值: {", ".join(VALID_TEST_TYPES)}'
    
    # 验证语言
    if 'language' in data:
        if data['language'] not in VALID_LANGUAGES:
            return False, f'无效的语言: {data["language"]}，有效值: {", ".join(VALID_LANGUAGES)}'
    
    # 验证难度范围格式（简单验证）
    if 'difficulty_range' in data and data['difficulty_range']:
        difficulty_range = data['difficulty_range']
        if '-' not in difficulty_range:
            return False, '难度范围格式应为 "最小值-最大值"，例如: "1-5"'
    
    return True, ""


def get_pagination_params():
    """
    获取分页参数
    
    Returns:
        tuple: (page, limit)
    """
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        return max(1, page), max(1, min(limit, 100))  # 限制最大每页100条
    except ValueError:
        return 1, 20


def get_boolean_param(param_name, default=None):
    """
    获取布尔型参数
    
    Args:
        param_name: 参数名
        default: 默认值
        
    Returns:
        bool or None: 解析后的布尔值
    """
    param_value = request.args.get(param_name)
    if param_value is None:
        return default
    
    return param_value.lower() in ('true', '1', 'yes', 'on')


@qa_data_group_bp.route('/api/qa/groups', methods=['GET'])
def get_qa_groups():
    """
    分页查询问答对组列表
    Query Parameters:
        page: 页码，默认1
        limit: 每页数量，默认20
        keyword: 关键词搜索（名称/用途）
        test_type: 测试类型筛选
        language: 语言筛选
        is_active: 激活状态筛选
        order_by: 排序字段，默认created_at DESC
        
    Returns:
        JSON: {total: int, page: int, limit: int, pages: int, rows: list}
    """
    try:
        # 获取查询参数
        page, limit = get_pagination_params()
        keyword = request.args.get('keyword')
        test_type = request.args.get('test_type')
        language = request.args.get('language')
        is_active = get_boolean_param('is_active')
        order_by = request.args.get('order_by', 'created_at DESC')
        
        # 计算偏移量
        offset = (page - 1) * limit
        
        with AIQADataGroupManager() as manager:
            # 获取分组列表
            groups = manager.list_groups(
                name=keyword,
                test_type=test_type,
                is_active=is_active,
                language=language,
                order_by=order_by,
                limit=limit,
                offset=offset
            )
            
            # 获取总数
            total = manager.count_groups(
                name=keyword,
                test_type=test_type,
                is_active=is_active,
                language=language
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
                    'rows': groups
                }
            })
            
    except Exception as e:
        logger.error(f"获取问答对组列表失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取问答对组列表失败: {str(e)}'
        }), 500


@qa_data_group_bp.route('/api/qa/groups', methods=['POST'])
def create_qa_group():
    """
    创建问答对组
    
    Request Body:
        name: 分组名称（必填）
        purpose: 用途描述
        test_type: 测试类型（accuracy/performance/robustness/comprehensive/custom）
        language: 语言，默认'zh'
        difficulty_range: 难度范围，如 "1-5"
        tags: 标签列表
        metadata: 额外配置信息
        
    Returns:
        JSON: {success: bool, group_id: int, message: str}
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求体不能为空'
            }), 400
        
        # 验证必要字段
        required_fields = ['name']
        missing_field = validate_required_fields(data, required_fields)
        if missing_field:
            return jsonify({
                'success': False,
                'message': f'缺少必要字段: {missing_field}'
            }), 400
        
        # 验证数据有效性
        is_valid, error_msg = validate_group_data(data)
        if not is_valid:
            return jsonify({
                'success': False,
                'message': error_msg
            }), 400
        
        # 提取参数
        name = data.get('name')
        purpose = data.get('purpose')
        test_type = data.get('test_type', 'custom')
        language = data.get('language', 'zh')
        difficulty_range = data.get('difficulty_range')
        tags = data.get('tags', [])
        metadata = data.get('metadata', {})
        
        with AIQADataGroupManager() as manager:
            # 检查名称是否已存在
            existing_groups = manager.list_groups(name=name)
            if existing_groups:
                return jsonify({
                    'success': False,
                    'message': f'分组名称 "{name}" 已存在'
                }), 400
            
            # 创建分组
            group_id = manager.create_group(
                name=name,
                purpose=purpose,
                test_type=test_type,
                language=language,
                difficulty_range=difficulty_range,
                tags=tags,
                metadata=metadata
            )
            
            if group_id:
                return jsonify({
                    'success': True,
                    'group_id': group_id,
                    'message': '分组创建成功'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '分组创建失败'
                }), 400
            
    except Exception as e:
        logger.error(f"创建问答对组失败: {e}")
        return jsonify({
            'success': False,
            'message': f'创建问答对组失败: {str(e)}'
        }), 500


@qa_data_group_bp.route('/api/qa/groups/<int:group_id>', methods=['GET'])
def get_qa_group_detail(group_id: int):
    """
    获取问答对组详情
    
    Args:
        group_id: 分组ID
        
    Returns:
        JSON: {success: bool, data: dict, message: str}
    """
    try:
        with AIQADataGroupManager() as manager:
            group = manager.get_group_by_id(group_id)
            
            if not group:
                return jsonify({
                    'success': False,
                    'message': f'分组不存在: ID={group_id}'
                }), 404
            
            return jsonify({
                'success': True,
                'data': group,
                'message': '获取分组详情成功'
            })
            
    except Exception as e:
        logger.error(f"获取分组详情失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取分组详情失败: {str(e)}'
        }), 500


@qa_data_group_bp.route('/api/qa/groups/<int:group_id>', methods=['PUT'])
def update_qa_group(group_id: int):
    """
    更新问答对组信息
    
    Args:
        group_id: 分组ID
        
    Request Body:
        name: 分组名称
        purpose: 用途描述
        test_type: 测试类型
        language: 语言
        difficulty_range: 难度范围
        tags: 标签列表
        metadata: 额外配置信息
        
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
        
        with AIQADataGroupManager() as manager:
            # 检查分组是否存在
            if not manager.group_exists(group_id):
                return jsonify({
                    'success': False,
                    'message': f'分组不存在: ID={group_id}'
                }), 404
            
            # 如果更新名称，检查名称是否已存在（排除当前分组）
            if 'name' in data:
                existing_groups = manager.list_groups(name=data['name'])
                if existing_groups and any(g['id'] != group_id for g in existing_groups):
                    return jsonify({
                        'success': False,
                        'message': f'分组名称 "{data["name"]}" 已存在'
                    }), 400
            
            # 验证测试类型
            if 'test_type' in data:
                valid_test_types = ['accuracy', 'performance', 'robustness', 'comprehensive', 'custom']
                if data['test_type'] not in valid_test_types:
                    return jsonify({
                        'success': False,
                        'message': f'无效的测试类型: {data["test_type"]}，有效值: {", ".join(valid_test_types)}'
                    }), 400
            
            # 更新分组
            success = manager.update_group(group_id, **data)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': '分组更新成功'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '分组更新失败'
                }), 400
            
    except Exception as e:
        logger.error(f"更新分组失败: {e}")
        return jsonify({
            'success': False,
            'message': f'更新分组失败: {str(e)}'
        }), 500


@qa_data_group_bp.route('/api/qa/groups/<int:group_id>', methods=['DELETE'])
def delete_qa_group(group_id: int):
    """
    删除问答对组
    
    Args:
        group_id: 分组ID
        
    Query Parameters:
        force: 是否强制删除（有关联数据时也删除），默认false
        
    Returns:
        JSON: {success: bool, message: str}
    """
    try:
        force = request.args.get('force', 'false').lower() == 'true'
        
        with AIQADataGroupManager() as manager:
            # 检查分组是否存在
            if not manager.group_exists(group_id):
                return jsonify({
                    'success': False,
                    'message': f'分组不存在: ID={group_id}'
                }), 404
            
            # 删除分组
            success = manager.delete_group(group_id, force=force)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': '分组删除成功'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '分组删除失败，可能有关联的问答对数据'
                }), 400
            
    except Exception as e:
        logger.error(f"删除分组失败: {e}")
        return jsonify({
            'success': False,
            'message': f'删除分组失败: {str(e)}'
        }), 500


@qa_data_group_bp.route('/api/qa/groups/<int:group_id>/toggle', methods=['POST'])
def toggle_qa_group_status(group_id: int):
    """
    激活/停用问答对组
    
    Args:
        group_id: 分组ID
        
    Request Body (可选):
        status: 目标状态（true=激活, false=停用），不传则切换状态
        
    Returns:
        JSON: {success: bool, status: bool, message: str}
    """
    try:
        data = request.get_json() or {}
        target_status = data.get('status')
        
        with AIQADataGroupManager() as manager:
            # 检查分组是否存在
            group = manager.get_group_by_id(group_id)
            if not group:
                return jsonify({
                    'success': False,
                    'message': f'分组不存在: ID={group_id}'
                }), 404
            
            current_status = group.get('is_active', True)
            
            # 确定目标状态
            if target_status is not None:
                new_status = bool(target_status)
            else:
                new_status = not current_status
            
            # 更新状态
            success = manager.update_group(group_id, is_active=new_status)
            
            if success:
                return jsonify({
                    'success': True,
                    'status': new_status,
                    'message': f'分组已{"激活" if new_status else "停用"}'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '状态更新失败'
                }), 400
            
    except Exception as e:
        logger.error(f"切换分组状态失败: {e}")
        return jsonify({
            'success': False,
            'message': f'切换分组状态失败: {str(e)}'
        }), 500


@qa_data_group_bp.route('/api/qa/groups/<int:group_id>/statistics', methods=['GET'])
def get_qa_group_statistics(group_id: int):
    """
    获取问答对组统计信息
    
    Args:
        group_id: 分组ID
        
    Returns:
        JSON: {success: bool, data: dict, message: str}
    """
    try:
        with AIQADataGroupManager() as manager:
            # 检查分组是否存在
            if not manager.group_exists(group_id):
                return jsonify({
                    'success': False,
                    'message': f'分组不存在: ID={group_id}'
                }), 404
            
            # 获取统计信息
            statistics = manager.get_group_statistics(group_id)
            
            return jsonify({
                'success': True,
                'data': statistics,
                'message': '获取统计信息成功'
            })
            
    except Exception as e:
        logger.error(f"获取分组统计信息失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取分组统计信息失败: {str(e)}'
        }), 500


@qa_data_group_bp.route('/api/qa/groups/<int:group_id>/tags', methods=['POST'])
def add_qa_group_tags(group_id: int):
    """
    为问答对组添加标签
    
    Args:
        group_id: 分组ID
        
    Request Body:
        tags: 标签列表（必填）
        
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
        
        tags = data.get('tags')
        if not tags or not isinstance(tags, list):
            return jsonify({
                'success': False,
                'message': 'tags字段必须是非空列表'
            }), 400
        
        with AIQADataGroupManager() as manager:
            # 检查分组是否存在
            if not manager.group_exists(group_id):
                return jsonify({
                    'success': False,
                    'message': f'分组不存在: ID={group_id}'
                }), 404
            
            # 添加标签
            success = manager.add_tags(group_id, tags)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': '标签添加成功'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '标签添加失败'
                }), 400
            
    except Exception as e:
        logger.error(f"添加分组标签失败: {e}")
        return jsonify({
            'success': False,
            'message': f'添加分组标签失败: {str(e)}'
        }), 500


@qa_data_group_bp.route('/api/qa/groups/<int:group_id>/tags', methods=['DELETE'])
def remove_qa_group_tags(group_id: int):
    """
    从问答对组移除标签
    
    Args:
        group_id: 分组ID
        
    Request Body:
        tags: 要移除的标签列表（必填）
        
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
        
        tags = data.get('tags')
        if not tags or not isinstance(tags, list):
            return jsonify({
                'success': False,
                'message': 'tags字段必须是非空列表'
            }), 400
        
        with AIQADataGroupManager() as manager:
            # 检查分组是否存在
            if not manager.group_exists(group_id):
                return jsonify({
                    'success': False,
                    'message': f'分组不存在: ID={group_id}'
                }), 404
            
            # 移除标签
            success = manager.remove_tags(group_id, tags)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': '标签移除成功'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '标签移除失败'
                }), 400
            
    except Exception as e:
        logger.error(f"移除分组标签失败: {e}")
        return jsonify({
            'success': False,
            'message': f'移除分组标签失败: {str(e)}'
        }), 500


@qa_data_group_bp.route('/qa/groups', methods=['GET'])
def qa_groups_page():
    """
    问答对组管理页面
    
    Returns:
        HTML: 问答对组管理页面
    """
    try:
        return render_qa_groups_page()
    except Exception as e:
        logger.error(f"加载问答对组管理页面失败: {e}")
        return render_error_page(500, "页面加载失败")


@qa_data_group_bp.route('/qa/groups/<int:group_id>', methods=['GET'])
def qa_group_detail_page(group_id: int):
    """
    问答对组详情页面
    
    Args:
        group_id: 分组ID
        
    Returns:
        HTML: 问答对组详情页面
    """
    try:
        return render_qa_group_detail_page(group_id)
    except Exception as e:
        logger.error(f"加载问答对组详情页面失败: {e}")
        return render_error_page(500, "页面加载失败")


@qa_data_group_bp.route('/qa/groups/<int:group_id>/import', methods=['GET'])
def import_qa_data_page(group_id: int):
    """
    问答对导入页面
    
    Args:
        group_id: 分组ID
        
    Returns:
        HTML: 问答对导入页面
    """
    try:
        from src.flask_funcs.reports.flask_qa_renderer import render_qa_group_import_page
        return render_qa_group_import_page(group_id)
    except Exception as e:
        logger.error(f"加载问答对导入页面失败: {e}")
        return render_error_page(500, "页面加载失败")