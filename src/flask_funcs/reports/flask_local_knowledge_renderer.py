"""
本地知识库渲染器模块 - Flask版本
使用Flask模板引擎生成本地知识库页面
"""
from .flask_renderer_base import FlaskHTMLRenderer
from env_config_init import settings


class LocalKnowledgeRendererFlask(FlaskHTMLRenderer):
    """本地知识库渲染器 - Flask版本"""

    def __init__(self, css_path: str = None):
        """
        初始化本地知识库渲染器

        Args:
            css_path: CSS文件路径
        """
        # 调用父类初始化
        super().__init__(css_path or "css/local_knowledge.css")  # 在css/ 下创建local_knowledge.css

    def render_local_knowledge_page(self, db_knowledge_list=None, local_directories=None):
        """
        渲染本地知识库页面
        """
        if db_knowledge_list is None:
            db_knowledge_list = []
        if local_directories is None:
            local_directories = []
        
        # 准备本地知识列表数据，查看本地目录下第一级目录
        # 按folder_name和kno_name处理，如果都有则按sql中数据显示，如果仅本地有则只显示folder_name
        knowledge_data = []
        
        # 将数据库中的数据转换为字典格式
        # ai_local_knowledge表的列顺序: id, kno_id, kno_name, kno_describe, kno_path, knol_id, ls_status, created_at, updated_at
        for row in db_knowledge_list:
            knowledge_data.append({
                'kno_id': row[1] if len(row) > 1 else row[0],  # kno_id
                'kno_name': row[2] if len(row) > 2 else row[1],  # kno_name
                'kno_describe': row[3] if len(row) > 3 else row[2],  # kno_describe
                'created_at': row[7] if len(row) > 7 else row[5],  # created_at
                'type': 'database'  # 标记为数据库数据
            })
        
        # 处理本地目录，如果不在数据库中则添加
        for folder_name in local_directories:
            exists_in_db = any(k['kno_name'] == folder_name for k in knowledge_data)
            if not exists_in_db:
                knowledge_data.append({
                    'kno_id': folder_name,
                    'kno_name': folder_name,
                    'kno_describe': '本地目录',
                    'created_at': None,
                    'type': 'local'  # 标记为本地目录
                })
        
        # 渲染模板
        html_content = self.render_template(
            'local_knowledge.html',
            title='本地知识库',
            heading='本地知识库列表',
            knowledge_data=knowledge_data,
            js_url=self._get_js_url('local_knowledge.js'),
            css_path=self._get_css_url()
        )
        return html_content

    def render_local_knowledge_detail(self, kno_id, knowledge_detail):
        """
        渲染本地知识库详情页面
        """
        # 准备知识详情数据
        knowledge_info = None
        if knowledge_detail and len(knowledge_detail) > 0:
            detail_row = knowledge_detail[0]
            # ai_local_knowledge表的列顺序: id, kno_id, kno_name, kno_describe, kno_path, knol_id, ls_status, created_at, updated_at
            knowledge_info = {
                'kno_id': detail_row[1] if len(detail_row) > 1 else detail_row[0],
                'kno_name': detail_row[2] if len(detail_row) > 2 else detail_row[1],
                'kno_describe': detail_row[3] if len(detail_row) > 3 else detail_row[2],
                'kno_path': detail_row[4] if len(detail_row) > 4 else detail_row[3],
                'knol_id': detail_row[5] if len(detail_row) > 5 else detail_row[4],
                'ls_status': detail_row[6] if len(detail_row) > 6 else detail_row[5],
                'created_at': detail_row[7] if len(detail_row) > 7 else detail_row[6],
                'updated_at': detail_row[8] if len(detail_row) > 8 else detail_row[7]
            }
        else:
            knowledge_info = None
        
        # todo: 获取关联的ai_knowledge表中的文件信息
        related_files = []  # 临时空列表，后续实现
        
        # 渲染模板
        html_content = self.render_template(
            'local_knowledge_detail.html',
            title=f'{knowledge_info["kno_name"] if knowledge_info else "知识详情"}',
            knowledge_info=knowledge_info,
            related_files=related_files,
            js_url=self._get_js_url('local_knowledge.js'),
            css_path=self._get_css_url()
        )
        return html_content

    def _prepare_local_knowledge_list_and_sql_list(self):
        """
        读取指定文件夹下的第一级目录,返回包含目录名称的list
        :return:
        """
        # todo 获取指定目录下的第一级目录 [folder_name...]
        # 获取sql中ai_local_knowledge的数据  [{'kno_id':"xx",'kno_name':"xxx"}]
        # 按folder_name和kno_name处理，如果都有则按sql中数据显示，如果仅本地有则只显示folder_name
        pass