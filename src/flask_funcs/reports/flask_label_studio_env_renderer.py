import logging
from typing import Dict, Any, List, Optional
from .flask_renderer_base import FlaskHTMLRenderer


class LabelStudioEnvRendererFlask(FlaskHTMLRenderer):
    """环境页面渲染器 - Flask版本"""

    def __init__(self, css_path: Optional[str] = None):
        """
        初始化环境页面渲染器

        Args:
            css_path: CSS文件路径
        """
        # 调用父类初始化
        super().__init__(css_path or "css/label_studio_env.css")

    def render_label_studio_env_page(self, environment_data: List, current_environment_id: str = "") -> str:
        """
        使用Flask渲染Label Studio环境页面

        Args:
            environment_data: Label Studio环境数据列表
            current_environment_id: 当前环境ID

        Returns:
            渲染后的HTML内容
        """
        try:
            # 准备JS文件URL
            js_url = self._get_js_url("label_studio_env.js")

            # 渲染模板
            html_content = self.render_template(
                'label_studio_env.html',
                environment_list=environment_data,
                current_environment_id=current_environment_id,
                js_url=js_url
            )
            return html_content

        except Exception as e:
            logging.error(f"Flask渲染Label Studio环境页面错误: {e}")
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
                    <p>Label Studio环境页面渲染失败: {str(e)}</p>
                </div>
            </body>
            </html>
            """
