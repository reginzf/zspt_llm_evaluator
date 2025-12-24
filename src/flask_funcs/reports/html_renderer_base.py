"""
HTML渲染器基类模块
提供HTML渲染器的通用功能和基础实现
"""
from pathlib import Path
from typing import Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape


class BaseHTMLRenderer:
    """HTML渲染器基类，提供通用的初始化和渲染功能"""

    def __init__(self, template_dir: Optional[str] = None, css_dir: Optional[str] = None, css_path: Optional[str] = None):
        """
        初始化基础HTML渲染器
        
        Args:
            template_dir: 模板目录路径
            css_dir: CSS目录路径
            css_path: CSS文件路径（相对于URL）
        """
        self.template_dir = template_dir or str(Path(__file__).parent / "templates")
        self.css_dir = css_dir or str(Path(__file__).parent / "statics" / "css")
        self.css_path = css_path or "/css/styles.css"  # 默认CSS路径，子类可以覆盖

        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )

        # 添加自定义过滤器
        self.env.filters['round'] = lambda x, n=2: round(x, n) if isinstance(x, (int, float)) else x