"""
环境页面渲染模块
使用Jinja2模板引擎生成美观的HTML报告
"""
import logging

from typing import Dict, Any, List, Optional
from .html_renderer_base import BaseHTMLRenderer

ENVIRONMENT_TEMPLATE_NAME = 'environment.html'


class EnvironmentRenderer(BaseHTMLRenderer):
    """环境页面渲染器"""

    def __init__(self, template_dir: Optional[str] = None, css_dir: Optional[str] = None):
        """
        初始化HTML渲染器

        Args:
            template_dir: 模板目录路径，如果为None则使用默认目录
            css_dir: CSS目录路径，如果为None则使用默认目录
        """
        # 调用父类初始化
        super().__init__(template_dir, css_dir, )

        self._js_content = None  # 缓存JS内容

    def render_environment_page(self, environment_data: List[Dict[str, Any]], current_environment_id: str) -> str:

        try:
            template = self.env.get_template(ENVIRONMENT_TEMPLATE_NAME)
            # todo 准备环境列表数据  environment_data
            # todo 准备当前环境数据  current_environment_id  根据id获取环境数
            template_context = self._prepare_environment_data(environment_data, current_environment_id)
            template_context['currment_environment'] = self._prepare_currment_environment(environment_data,
                                                                                          current_environment_id)
        except Exception as e:
            logging.error(f"Jinja2渲染错误: {e}")
            raise e
            # 渲染模板
        html_content = template.render(**template_context)
        return html_content

    def _prepare_environment_data(self, environment_data, current_environment_id):
        # todo 准备环境列表数据
        return {'environment_list': []}

    def _prepare_currment_environment(self, environment_data, current_environment_id):
        # todo 获取当前环境数据
        return {}
