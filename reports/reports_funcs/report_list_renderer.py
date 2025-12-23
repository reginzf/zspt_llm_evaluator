"""
报告文件列表渲染器模块
使用Jinja2模板引擎生成报告文件列表页面
"""
from typing import List
from .html_renderer_base import BaseHTMLRenderer


class ReportListRenderer(BaseHTMLRenderer):
    """报告文件列表渲染器"""

    def __init__(self, template_dir: str = None, css_dir: str = None):
        """
        初始化报告列表渲染器
        
        Args:
            template_dir: 模板目录路径
            css_dir: CSS目录路径
        """
        # 调用父类初始化
        super().__init__(template_dir, css_dir, "/css/report_list.css")

    def render_report_list(self, json_files: List[str]) -> str:
        """
        渲染报告文件列表页面
        
        Args:
            json_files: JSON文件列表
            
        Returns:
            渲染后的HTML内容
        """
        try:
            template = self.env.get_template('report_list.html')
            template_context = {
                'json_files': json_files,
                'css_path': self.css_path,
                'total_files': len(json_files)
            }
            html_content = template.render(**template_context)
            return html_content
        except Exception as e:
            print(f"Jinja2渲染错误: {e}")
            raise e
