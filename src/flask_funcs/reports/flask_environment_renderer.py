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
        super().__init__(css_path or "css/environment.css")

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
            current_environment = self._prepare_current_environment(environment_data, current_environment_id)

            # 准备JS文件URL
            js_url = self._get_js_url("environment.js")

            # 渲染模板
            html_content = self.render_template(
                'environment.html',
                environment_list=environment_data,
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


    def _prepare_current_environment(self, environment_data: List, current_environment_id: str) -> Dict[str, Any]:
        """
        获取当前环境数据

        Args:
            environment_data: 环境数据列表
            current_environment_id: 当前环境ID

        Returns:
            当前环境数据字典
        """
        # 如果环境数据为空，返回空字典
        if not environment_data:
            return {}
            
        # 查找匹配的环境
        for environment in environment_data:
            if environment['zlpt_base_id'] == current_environment_id:
                return environment
        
        # 如果没有找到匹配的环境，返回第一个环境（如果存在）
        return environment_data[0] if environment_data else {}