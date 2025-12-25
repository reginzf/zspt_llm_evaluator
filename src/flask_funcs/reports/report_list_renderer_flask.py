"""
报告文件列表渲染器模块 - Flask版本
使用Flask模板引擎生成报告文件列表页面
"""
from typing import List
from .flask_renderer_base import FlaskHTMLRenderer


class ReportListRendererFlask(FlaskHTMLRenderer):
    """报告文件列表渲染器 - Flask版本"""

    def __init__(self, css_path: str = None):
        """
        初始化报告列表渲染器
        
        Args:
            css_path: CSS文件路径
        """
        # 调用父类初始化
        super().__init__(css_path or "css/report_list.css")

    def render_report_list(self, json_files: List[str]) -> str:
        """
        渲染报告文件列表页面
        
        Args:
            json_files: JSON文件列表
            
        Returns:
            渲染后的HTML内容
        """
        try:
            # 渲染模板
            html_content = self.render_template(
                'report_list.html',
                json_files=json_files,
                total_files=len(json_files),
                js_url=self._get_js_url('report_list.js')
            )
            return html_content
        except Exception as e:
            print(f"Flask渲染错误: {e}")
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
                    <p>报告列表渲染失败: {str(e)}</p>
                </div>
            </body>
            </html>
            """

    def render_report_list_with_directory(self, directory_structure: dict) -> str:
        """
        渲染带目录结构的报告文件列表页面
        
        Args:
            directory_structure: 目录结构字典
            
        Returns:
            渲染后的HTML内容
        """
        try:
            # 渲染模板
            html_content = self.render_template(
                'report_list.html',
                directory_structure=directory_structure,
                total_files=sum(len(files) for files in directory_structure.values()),
                js_url=self._get_js_url('report_list.js')
            )
            return html_content
        except Exception as e:
            print(f"Flask渲染错误: {e}")
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
                    <p>报告列表渲染失败: {str(e)}</p>
                </div>
            </body>
            </html>
            """
