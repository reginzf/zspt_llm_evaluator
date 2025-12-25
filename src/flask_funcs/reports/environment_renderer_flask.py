"""
环境页面渲染模块 - Flask版本
使用Flask模板引擎生成美观的HTML报告
"""
import logging
from typing import Dict, Any, List, Optional
from .flask_renderer_base import FlaskHTMLRenderer


class EnvironmentRendererFlask(FlaskHTMLRenderer):
    """环境页面渲染器 - Flask版本"""

    def __init__(self, css_path: Optional[str] = None):
        """
        初始化环境页面渲染器

        Args:
            css_path: CSS文件路径
        """
        # 调用父类初始化
        super().__init__(css_path or "css/styles.css")

    def render_environment_page(self, environment_data: List, current_environment_id: str) -> str:
        """
        使用Flask渲染环境页面

        Args:
            environment_data: 环境数据列表
            current_environment_id: 当前环境ID

        Returns:
            渲染后的HTML内容
        """
        try:
            # 准备环境数据
            environment_list = self._prepare_environment_data(environment_data)
            current_environment = self._prepare_current_environment(environment_data, current_environment_id)
            
            # 准备JS文件URL
            js_url = self._get_js_url("environment.js")
            
            # 渲染模板
            html_content = self.render_template(
                'environment.html',
                environment_list=environment_list,
                current_environment=current_environment,
                js_url=js_url
            )
            return html_content

        except Exception as e:
            logging.error(f"Flask渲染错误: {e}")
            # 返回简单的错误页面
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>错误</title>
                <link rel="stylesheet" href="{self._get_css_url()}">
            </head>
            <body>
                <div class="container">
                    <h1>渲染错误</h1>
                    <p>环境页面渲染失败: {str(e)}</p>
                </div>
            </body>
            </html>
            """

    def _prepare_environment_data(self, environment_data: List) -> List[Dict[str, Any]]:
        """
        准备环境列表数据

        Args:
            environment_data: 环境数据列表

        Returns:
            环境字典列表
        """
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
        return environment_list

    def _prepare_current_environment(self, environment_data: List, current_environment_id: str) -> Dict[str, Any]:
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