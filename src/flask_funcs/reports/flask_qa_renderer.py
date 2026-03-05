# -*- coding: utf-8 -*-
"""
问答对管理页面渲染器

此模块提供问答对管理相关页面的渲染功能，
包括问答对组管理页面和问答对组详情页面。
"""
import logging
from flask import render_template, abort
from typing import Dict, Any, Optional
from src.sql_funs.ai_qa_data_group_crud import AIQADataGroupManager
from src.sql_funs.ai_qa_data_crud import AIQADataManager

logger = logging.getLogger(__name__)


def render_qa_groups_page() -> str:
    """
    渲染问答对组管理页面
    
    Returns:
        str: 渲染后的HTML页面
    """
    try:
        # 获取页面配置
        page_config = {
            'title': '问答对组管理',
            'heading': '问答对组管理',
            'css_path': '/static/css/qa_management.css?v=6',
            'js_path': '/static/js/qa_groups.js?v=8'
        }
        
        # 获取初始数据（可选）
        initial_data = {}
        
        return render_template(
            'qa_groups.html',
            **page_config,
            initial_data=initial_data
        )
        
    except Exception as e:
        logger.error(f"渲染问答对组管理页面失败: {e}")
        abort(500, description="页面渲染失败")


def render_qa_group_detail_page(group_id: int) -> str:
    """
    渲染问答对组详情页面
    
    Args:
        group_id: 分组ID
        
    Returns:
        str: 渲染后的HTML页面
        
    Raises:
        404: 分组不存在
    """
    try:
        # 获取分组信息
        with AIQADataGroupManager() as manager:
            group = manager.get_group_by_id(group_id)
            
            if not group:
                logger.warning(f"分组不存在: ID={group_id}")
                abort(404, description="分组不存在")
            
            # 获取分组统计信息
            statistics = manager.get_group_statistics(group_id)
            
            # 获取页面配置
            page_config = {
                'title': f'问答对组详情 - {group.get("name", "未知")}',
                'heading': f'问答对组详情: {group.get("name", "未知")}',
                'css_path': '/static/css/qa_management.css',
                'js_path': '/static/js/qa_group_detail.js',
                'group_id': group_id,
                'group_name': group.get('name', ''),
                'group_purpose': group.get('purpose', ''),
                'group_test_type': group.get('test_type', ''),
                'group_language': group.get('language', 'zh'),
                'group_difficulty_range': group.get('difficulty_range', ''),
                'group_is_active': group.get('is_active', True),
                'group_statistics': statistics
            }
            
            return render_template(
                'qa_group_detail.html',
                **page_config
            )
            
    except Exception as e:
        logger.error(f"渲染问答对组详情页面失败: {e}")
        abort(500, description="页面渲染失败")


def render_qa_data_edit_page(qa_id: int) -> str:
    """
    渲染问答对编辑页面（可选功能）
    
    Args:
        qa_id: 问答对ID
        
    Returns:
        str: 渲染后的HTML页面
        
    Raises:
        404: 问答对不存在
    """
    try:
        # 获取问答对信息
        with AIQADataManager() as manager:
            qa_data = manager.get_qa_data_by_id(qa_id)
            
            if not qa_data:
                logger.warning(f"问答对不存在: ID={qa_id}")
                abort(404, description="问答对不存在")
            
            # 获取分组信息
            group_id = qa_data.get('group_id')
            group_info = {}
            if group_id:
                with AIQADataGroupManager() as group_manager:
                    group_info = group_manager.get_group_by_id(group_id) or {}
            
            # 获取页面配置
            page_config = {
                'title': f'编辑问答对 - {qa_data.get("question", "未知")[:50]}...',
                'heading': '编辑问答对',
                'css_path': '/static/css/qa_management.css',
                'js_path': '/static/js/qa_data_edit.js',
                'qa_data': qa_data,
                'group_info': group_info
            }
            
            return render_template(
                'qa_data_edit.html',
                **page_config
            )
            
    except Exception as e:
        logger.error(f"渲染问答对编辑页面失败: {e}")
        abort(500, description="页面渲染失败")


def render_qa_data_create_page(group_id: int) -> str:
    """
    渲染问答对创建页面（可选功能）
    
    Args:
        group_id: 分组ID
        
    Returns:
        str: 渲染后的HTML页面
        
    Raises:
        404: 分组不存在
    """
    try:
        # 获取分组信息
        with AIQADataGroupManager() as manager:
            group = manager.get_group_by_id(group_id)
            
            if not group:
                logger.warning(f"分组不存在: ID={group_id}")
                abort(404, description="分组不存在")
            
            # 获取页面配置
            page_config = {
                'title': f'创建问答对 - {group.get("name", "未知")}',
                'heading': f'创建问答对（分组: {group.get("name", "未知")}）',
                'css_path': '/static/css/qa_management.css',
                'js_path': '/static/js/qa_data_create.js',
                'group_id': group_id,
                'group_name': group.get('name', ''),
                'group_test_type': group.get('test_type', ''),
                'group_language': group.get('language', 'zh')
            }
            
            return render_template(
                'qa_data_create.html',
                **page_config
            )
            
    except Exception as e:
        logger.error(f"渲染问答对创建页面失败: {e}")
        abort(500, description="页面渲染失败")


def render_qa_import_page() -> str:
    """
    渲染问答对导入页面（可选功能）
    
    Returns:
        str: 渲染后的HTML页面
    """
    try:
        # 获取所有分组用于选择
        groups = []
        with AIQADataGroupManager() as manager:
            groups = manager.list_groups(is_active=True, order_by='name ASC')
        
        # 获取页面配置
        page_config = {
            'title': '问答对导入',
            'heading': '问答对导入',
            'css_path': '/static/css/qa_management.css',
            'js_path': '/static/js/qa_import.js',
            'groups': groups
        }
        
        # 注意：旧的导入页面模板需要重命名为qa_import_old.html
        # 这里我们使用新的导入页面
        return render_template(
            'qa_import.html',
            **page_config
        )
        
    except Exception as e:
        logger.error(f"渲染问答对导入页面失败: {e}")
        abort(500, description="页面渲染失败")


def render_qa_group_import_page(group_id: int) -> str:
    """
    渲染问答对导入页面（针对特定分组）
    
    Args:
        group_id: 分组ID
        
    Returns:
        str: 渲染后的HTML页面
    """
    try:
        # 获取分组信息
        with AIQADataGroupManager() as manager:
            group = manager.get_group_by_id(group_id)
            
            if not group:
                abort(404, description=f"分组不存在: ID={group_id}")
            
            # 获取页面配置
            page_config = {
                'title': f'导入问答对数据 - {group["name"]}',
                'heading': f'导入问答对数据 - {group["name"]}',
                'css_path': '/static/css/qa_management.css',
                'group_id': group_id,
                'group_name': group['name'],
                'group_purpose': group.get('purpose', ''),
                'group_test_type': group.get('test_type', ''),
                'group_language': group.get('language', 'zh'),
                'group_is_active': group.get('is_active', True)
            }
            
            return render_template(
                'qa_import.html',
                **page_config
            )
            
    except Exception as e:
        logger.error(f"渲染问答对导入页面失败: {e}")
        abort(500, description="页面渲染失败")


def render_error_page(error_code: int, error_message: str = None) -> str:
    """
    渲染错误页面
    
    Args:
        error_code: 错误代码
        error_message: 错误消息
        
    Returns:
        str: 渲染后的HTML页面
    """
    try:
        error_messages = {
            404: '页面不存在',
            500: '服务器内部错误',
            403: '访问被拒绝',
            400: '请求错误'
        }
        
        default_message = error_messages.get(error_code, '未知错误')
        message = error_message or default_message
        
        page_config = {
            'title': f'错误 {error_code}',
            'heading': f'错误 {error_code}: {message}',
            'css_path': '/static/css/qa_management.css',
            'error_code': error_code,
            'error_message': message
        }
        
        return render_template(
            'qa_error.html',
            **page_config
        )
        
    except Exception as e:
        # 如果模板渲染失败，返回简单的错误页面
        logger.error(f"渲染错误页面失败: {e}")
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>错误 {error_code}</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 40px; text-align: center; }}
                h1 {{ color: #dc3545; }}
                .error-code {{ font-size: 72px; font-weight: bold; color: #6c757d; }}
                .error-message {{ font-size: 24px; margin: 20px 0; }}
                .back-link {{ color: #007bff; text-decoration: none; }}
            </style>
        </head>
        <body>
            <div class="error-code">{error_code}</div>
            <h1>错误</h1>
            <div class="error-message">{message}</div>
            <a href="/qa/groups" class="back-link">返回问答对组管理</a>
        </body>
        </html>
        """