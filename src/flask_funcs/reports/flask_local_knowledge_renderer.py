"""
报告文件列表渲染器模块 - Flask版本
使用Flask模板引擎生成报告文件列表页面
"""
from .flask_renderer_base import FlaskHTMLRenderer
from env_config_init import settings

class LocalKnowledgeRendererFlask(FlaskHTMLRenderer):
    """报告文件列表渲染器 - Flask版本"""

    def __init__(self, css_path: str = None):
        """
        初始化报告列表渲染器

        Args:
            css_path: CSS文件路径
        """
        # 调用父类初始化
        super().__init__(css_path or "css/local_knowledge.css")  # todo 在css/ 下创建local_knowledge.css
    def render_local_knowledge_page(self):
        # todo 渲染模板
        # 准备本地知识列表数据，查看本地目录下第一级文件夹

        html_content = self.render_template(
            'local_knowledge.html'
        )
    def _prepare_local_knowledge_list_and_sql_list(self):
        """
        读取指定文件夹下的第一级目录,返回包含目录名称的list
        :return:
        """
        # todo 获取指定目录下的第一级目录 [folder_name...]
        # 获取sql中ai_local_knowledge的数据  [{'kno_id':"xx",'kno_name':"xxx"}]
        # 按folder_name和kno_name处理，如果都有则按sql中数据显示，如果仅本地有则只显示folder_name
        pass
