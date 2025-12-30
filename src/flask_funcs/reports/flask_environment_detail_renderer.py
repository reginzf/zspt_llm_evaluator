"""
环境页面渲染模块 - Flask版本
使用Flask模板引擎生成美观的HTML报告
"""
import logging
from typing import Dict, Any, List, Optional
from .flask_renderer_base import FlaskHTMLRenderer


class EnvironmentDetailRendererFlask(FlaskHTMLRenderer):
    """环境页面渲染器 - Flask版本"""

    def __init__(self, css_path: Optional[str] = None):
        """
        初始化环境页面渲染器

        Args:
            css_path: CSS文件路径
        """
        # 调用父类初始化
        super().__init__(css_path or "css/environment_detail.css")

    def render_environment_detail_page(self, environment_detail, knowledge_base_list):
        """
        渲染环境详情页面
        
        Args:
            environment_detail: 环境详情数据
            knowledge_base_list: 知识库列表数据
        """
        page_data = self._prepare_environment_detail_page(environment_detail, knowledge_base_list)
        # 渲染模板
        html_content = self.render_template(
            'environment_detail.html',
            title='知识平台详细信息',
            heading='知识平台详细信息',
            environment=page_data['environment'],
            knowledge_bases=page_data['knowledge_bases'],
            js_url=self._get_js_url('environment_detail.js'),
            css_path=self._get_css_url()
        )
        return html_content

    def _prepare_environment_detail_page(self, environment_detail, knowledge_base_list):
        """
        准备环境详情页面数据
        
        Args:
            environment_detail: 环境详情数据
            knowledge_base_list: 知识库列表数据
        """
        from src.sql_funs.environment_crud import Environment_Crud
        env_crud = Environment_Crud()
        
        # 将环境详情元组转换为字典格式
        env_data = env_crud._environment_list_to_json(environment_detail)
        
        return {
            "environment": env_data,
            "knowledge_bases": knowledge_base_list
        }
