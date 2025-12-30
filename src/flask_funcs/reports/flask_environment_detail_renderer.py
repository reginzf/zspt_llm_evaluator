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
        # 解析环境详情数据
        # environment_detail 格式: (zlpt_base_id, zlpt_name, zlpt_base_url, key1, key2_add, pk, username, password, domain, created_at, updated_at)
        env_data = {
            "zlpt_base_id": environment_detail[0],
            "zlpt_name": environment_detail[1],
            "zlpt_base_url": environment_detail[2],
            "key1": environment_detail[3],
            "key2_add": environment_detail[4],
            "pk": environment_detail[5],
            "username": environment_detail[6],
            "password": "***",  # 隐藏密码
            "domain": environment_detail[8],
            "created_at": environment_detail[9],
            "updated_at": environment_detail[10]
        }
        
        # 解析知识库列表数据
        knowledge_list = []
        for kb in knowledge_base_list:
            # kb格式: (knowledge_id, knowledge_name, kno_root_id, chunk_size, chunk_overlap, 
            #         sliceidentifier, visiblerange, deptidlist, managedeptidlist, zlpt_base_id, created_at, updated_at)
            kb_data = {
                "knowledge_id": kb[0],
                "knowledge_name": kb[1],
                "kno_root_id": kb[2],
                "chunk_size": kb[3],
                "chunk_overlap": kb[4],
                "sliceidentifier": kb[5],
                "visiblerange": kb[6],
                "deptidlist": kb[7],
                "managedeptidlist": kb[8],
                "zlpt_base_id": kb[9],
                "created_at": kb[10],
                "updated_at": kb[11]
            }
            knowledge_list.append(kb_data)
        
        return {
            "environment": env_data,
            "knowledge_bases": knowledge_list
        }
