"""
修复版的Flask HTML渲染器基类
解决Jinja2模板渲染和静态文件引用问题
"""
from flask import render_template, url_for
from typing import Optional


class FlaskHTMLRenderer:
    """修复版的Flask HTML渲染器基类"""

    def __init__(self, css_path: Optional[str] = None):
        """
        初始化修复版Flask HTML渲染器

        Args:
            css_path: CSS文件路径（相对于static目录）
        """
        self.css_path = css_path or "css/styles.css"

    def _get_static_url(self, filename: str) -> str:
        """
        获取静态文件的URL - 修复版

        Args:
            filename: 静态文件名

        Returns:
            静态文件的完整URL
        """
        # 使用正确的静态文件路由
        if filename.startswith('css/'):
            return url_for('static_bp.custom_css', filename=filename.replace('css/', ''))
        elif filename.startswith('js/'):
            return url_for('static_bp.custom_js', filename=filename.replace('js/', ''))
        else:
            # 尝试使用默认静态路由
            return url_for('static', filename=filename)

    def _get_css_url(self) -> str:
        """
        获取CSS文件的URL

        Returns:
            CSS文件的完整URL
        """
        return self._get_static_url(self.css_path)

    def _get_js_url(self, js_filename: str) -> str:
        """
        获取JS文件的URL

        Args:
            js_filename: JS文件名

        Returns:
            JS文件的完整URL
        """
        return self._get_static_url(f"js/{js_filename}")

    def _prepare_context(self, **kwargs) -> dict:
        """
        准备模板上下文 - 修复版

        Args:
            **kwargs: 额外的上下文参数

        Returns:
            模板上下文字典
        """
        context = {
            'css_path': self._get_css_url(),
            **kwargs
        }
        return context

    def render_template(self, template_name: str, **kwargs) -> str:
        """
        使用Flask的render_template渲染模板 - 修复版

        Args:
            template_name: 模板文件名
            **kwargs: 模板上下文参数

        Returns:
            渲染后的HTML内容
        """
        try:
            context = self._prepare_context(**kwargs)
            return render_template(template_name, **context)
        except Exception as e:
            # 如果渲染失败，返回简单的错误页面
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>渲染错误</title>
                <style>
                    body {{ font-family: Arial, sans-serif; padding: 20px; }}
                    .error {{ color: red; }}
                </style>
            </head>
            <body>
                <h1>模板渲染错误</h1>
                <p class="error">错误信息: {str(e)}</p>
                <p>请检查模板文件和上下文数据</p>
            </body>
            </html>
            """