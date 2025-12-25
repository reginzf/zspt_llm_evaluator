"""
Flask兼容的HTML渲染器基类模块
提供与Flask集成的HTML渲染器基础实现
"""
from flask import render_template, url_for
from typing import Optional


class FlaskHTMLRenderer:
    """Flask兼容的HTML渲染器基类，使用Flask的模板系统"""

    def __init__(self, css_path: Optional[str] = None):
        """
        初始化Flask HTML渲染器
        
        Args:
            css_path: CSS文件路径（相对于static目录）
        """
        self.css_path = css_path or "css/styles.css"

    def _get_static_url(self, filename: str) -> str:
        """
        获取静态文件的URL
        
        Args:
            filename: 静态文件名
            
        Returns:
            静态文件的完整URL
        """
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
        准备模板上下文
        
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
        使用Flask的render_template渲染模板
        
        Args:
            template_name: 模板文件名
            **kwargs: 模板上下文参数
            
        Returns:
            渲染后的HTML内容
        """
        context = self._prepare_context(**kwargs)
        return render_template(template_name, **context)