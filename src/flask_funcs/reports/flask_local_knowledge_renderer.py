"""
本地知识库渲染器模块 - Flask版本
使用Flask模板引擎生成本地知识库页面
"""
from pathlib import Path

from .flask_renderer_base import FlaskHTMLRenderer
from env_config_init import settings

KNOWLEDGE_DETAIL_STATUS_MAP = {
    0: "sync_wait",  # 等待同步
    1: "sync_ok",  # 同步成功
    2: "syncing"  # 进行中
}


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
        knowledge_data = self._prepare_local_knowledge_page(db_knowledge_list, local_directories)
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

    def gen_knowledge_detail(self, local_files, knowledge_detail):
        """
        渲染本地知识库详情页面
        """
        res = []
        name_dict = {}
        # 准备知识详情数据
        if knowledge_detail and len(knowledge_detail) > 0:
            for detail_row in knowledge_detail:
                temp = {
                    'kno_id': detail_row[1],
                    'kno_name': detail_row[2],
                    'kno_describe': detail_row[3],
                    'kno_path': detail_row[4],
                    'ls_status': KNOWLEDGE_DETAIL_STATUS_MAP[detail_row[5]],
                    'created_at': detail_row[6],
                    'updated_at': detail_row[7]
                }
                res.append(temp)
                name_dict[temp['kno_name']] = temp
        # 处理文件数据
        for filename in local_files:
            filename_without_ext = Path(filename).stem
            if filename_without_ext in name_dict:
                name_dict[filename_without_ext]['status'] = 'sync_ok'
            else:
                res.append({
                    'kno_id': '',
                    'kno_name': filename_without_ext,
                    'kno_describe': '本地文件',
                    'kno_path': filename,
                    'ls_status': 'sync_wait',
                    'created_at': None,
                    'updated_at': None
                })
        return res

    def _prepare_local_knowledge_page(self, db_knowledge_list, local_directories):
        """
        读取指定文件夹下的第一级目录,返回包含目录名称的list
        :return:
        """
        if db_knowledge_list is None:
            db_knowledge_list = []
        if local_directories is None:
            local_directories = []

            # 准备本地知识列表数据，查看本地目录下第一级目录
            # 按folder_name和kno_name处理，如果都有则按sql中数据显示，如果仅本地有则只显示folder_name
        knowledge_data = []
        kno_name_data_dict = {}
        # 将数据库中的数据转换为字典格式
        # ai_local_knowledge表的列顺序: id, kno_id, kno_name, kno_describe, kno_path, knol_id, ls_status, created_at, updated_at
        for row in db_knowledge_list:
            temp = {
                'kno_id': row[1] if len(row) > 1 else row[0],  # kno_id
                'kno_name': row[2] if len(row) > 2 else row[1],  # kno_name
                'kno_describe': row[3] if len(row) > 3 else row[2],  # kno_describe
                'created_at': row[7] if len(row) > 7 else row[5],  # created_at
                'type': 'database'  # 标记为数据库数据
            }
            knowledge_data.append(temp)
            kno_name_data_dict[temp['kno_name']] = temp

        # 处理本地目录，如果不在数据库中则添加
        exists_in_db = [k['kno_name'] for k in knowledge_data]
        for folder_name in local_directories:
            if folder_name not in exists_in_db:
                knowledge_data.append({
                    'kno_id': folder_name,
                    'kno_name': folder_name,
                    'kno_describe': '本地目录',
                    'created_at': None,
                    'type': 'local',  # 标记为本地目录
                    'status': 'sync_wait'
                })
            else:
                kno_name_data_dict[folder_name]['status'] = 'sync_ok'
        return knowledge_data
