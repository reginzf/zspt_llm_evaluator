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
        super().__init__(template_dir, css_dir, "/css/styles.css")

        self._js_content = None  # 缓存JS内容

    def render_environment_page(self, environment_data: List, current_environment_id: str) -> str:
        """
        使用Jinja2渲染环境页面

        Args:
            environment_data: 环境数据列表
            current_environment_id: 当前环境ID

        Returns:
            渲染后的HTML内容
        """
        try:
            template = self.env.get_template(ENVIRONMENT_TEMPLATE_NAME)
            template_context = self._prepare_environment_data(environment_data, current_environment_id)
            template_context['currment_environment'] = self._prepare_currment_environment(environment_data,
                                                                                          current_environment_id)
            # 添加CSS路径
            template_context['css_path'] = self.css_path
        except Exception as e:
            logging.error(f"Jinja2渲染错误: {e}")
            raise e
        # 渲染模板
        html_content = template.render(**template_context)
        return html_content

    def _prepare_environment_data(self, environment_data: List, current_environment_id: str) -> Dict[str, Any]:
        """
        准备环境列表数据

        Args:
            environment_data: 环境数据列表
            current_environment_id: 当前环境ID

        Returns:
            包含环境列表的字典
        """
        # 将元组列表转换为字典列表，以便在模板中使用
        environment_list = []
        for env_tuple in environment_data:
            env_dict = {
                'zlpt_base_id': env_tuple[0],
                'zlpt_name': env_tuple[1],
                'zlpt_base_url': env_tuple[2],
                'key1': env_tuple[3],
                'key2_add': env_tuple[4],
                'pk': env_tuple[5],
                'username': env_tuple[6],
                'password': env_tuple[7],
                'domain': env_tuple[8],
                'created_at': env_tuple[9],
                'updated_at': env_tuple[10]
            }
            environment_list.append(env_dict)
        return {'environment_list': environment_list}

    def _prepare_currment_environment(self, environment_data: List, current_environment_id: str) -> Dict[str, Any]:
        """
        获取当前环境数据

        Args:
            environment_data: 环境数据列表
            current_environment_id: 当前环境ID

        Returns:
            当前环境数据字典
        """
        # 根据ID查找当前环境数据
        for env_tuple in environment_data:
            # env_tuple[0] 是 zlpt_base_id
            if env_tuple[0] == current_environment_id:
                # 将元组转换为字典
                return {
                    'zlpt_base_id': env_tuple[0],
                    'zlpt_name': env_tuple[1],
                    'zlpt_base_url': env_tuple[2],
                    'key1': env_tuple[3],
                    'key2_add': env_tuple[4],
                    'pk': env_tuple[5],
                    'username': env_tuple[6],
                    'password': env_tuple[7],
                    'domain': env_tuple[8],
                    'created_at': env_tuple[9],
                    'updated_at': env_tuple[10]
                }
        # 如果未找到，返回环境信息列表的第一条环境信息
        if environment_data:
            first_env = environment_data[0]
            return {
                'zlpt_base_id': first_env[0],
                'zlpt_name': first_env[1],
                'zlpt_base_url': first_env[2],
                'key1': first_env[3],
                'key2_add': first_env[4],
                'pk': first_env[5],
                'username': first_env[6],
                'password': first_env[7],
                'domain': first_env[8],
                'created_at': first_env[9],
                'updated_at': first_env[10]
            }
        return {}