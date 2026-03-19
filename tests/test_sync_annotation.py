import sys
import os
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.zlpt_temp import ls_create_tasks


def _make_project(existing_chunk_ids=None, import_return=None):
    """构造一个模拟的 Label Studio Project 对象"""
    project = MagicMock()
    existing_tasks = [
        {'data': {'chunk_id': cid}} for cid in (existing_chunk_ids or [])
    ]
    project.get_tasks.return_value = existing_tasks
    project.import_tasks.return_value = import_return or []
    return project


def _make_know_client(chunks_by_doc):
    """构造模拟的知识库客户端，chunks_by_doc = {doc_id: [chunk_dict, ...]}

    mock 返回 (doc_name, chunks) 结构，与 zlpt_get_chunk_all_by_doc_id 的 wrapper 契约一致：
    zlpt_get_chunk_all_by_doc_id(know_client, doc_id) -> (doc_name, chunk_list)
    其内部调用 know_client.doc_get_chunk_all(doc_id)
    """
    know_client = MagicMock()

    def mock_doc_get_chunk_all(doc_id):
        chunks = chunks_by_doc.get(doc_id, [])
        return f'doc_{doc_id}', chunks

    know_client.doc_get_chunk_all.side_effect = mock_doc_get_chunk_all
    return know_client


class TestLsCreateTasksIncremental(unittest.TestCase):

    def test_first_sync_imports_all_chunks(self):
        """首次同步时（项目中无已存在任务），全部切片应被导入"""
        chunks = [
            {'chunk_id': 'c1', 'chunk_text': 'text1', 'chunk_title': 't1',
             'chunk_size': 100, 'doc_title': 'doc1', 'start_at': None},
            {'chunk_id': 'c2', 'chunk_text': 'text2', 'chunk_title': 't2',
             'chunk_size': 100, 'doc_title': 'doc1', 'start_at': None},
        ]
        know_client = _make_know_client({'doc1': chunks})
        project = _make_project(existing_chunk_ids=[], import_return=['task1', 'task2'])

        task_ids, new_count, existing_count = ls_create_tasks(know_client, project, ['doc1'])

        self.assertEqual(new_count, 2)
        self.assertEqual(existing_count, 0)
        self.assertEqual(task_ids, ['task1', 'task2'])
        project.import_tasks.assert_called()

    def test_second_sync_skips_existing_chunks(self):
        """第二次同步时，已存在的 chunk_id 不再导入"""
        chunks = [
            {'chunk_id': 'c1', 'chunk_text': 'text1', 'chunk_title': 't1',
             'chunk_size': 100, 'doc_title': 'doc1', 'start_at': None},
            {'chunk_id': 'c2', 'chunk_text': 'text2', 'chunk_title': 't2',
             'chunk_size': 100, 'doc_title': 'doc1', 'start_at': None},
        ]
        know_client = _make_know_client({'doc1': chunks})
        # c1 已存在，只有 c2 是新增
        project = _make_project(existing_chunk_ids=['c1'], import_return=['task2'])

        with patch('src.zlpt_temp.create_tasks', return_value=['task2']) as mock_create:
            task_ids, new_count, existing_count = ls_create_tasks(know_client, project, ['doc1'])

        self.assertEqual(new_count, 1)
        self.assertEqual(existing_count, 1)
        # 断言传给 create_tasks 的切片数据只包含 c2
        mock_create.assert_called_once()
        tasks_arg = mock_create.call_args[0][1]  # create_tasks(project, tasks) 的第二个参数
        chunk_ids_passed = [t['chunk_id'] for t in tasks_arg]
        self.assertEqual(chunk_ids_passed, ['c2'])

    def test_no_new_chunks_skips_import(self):
        """所有切片已存在时，不调用 import_tasks，返回空列表"""
        chunks = [
            {'chunk_id': 'c1', 'chunk_text': 'text1', 'chunk_title': 't1',
             'chunk_size': 100, 'doc_title': 'doc1', 'start_at': None},
        ]
        know_client = _make_know_client({'doc1': chunks})
        project = _make_project(existing_chunk_ids=['c1'])

        task_ids, new_count, existing_count = ls_create_tasks(know_client, project, ['doc1'])

        self.assertEqual(task_ids, [])
        self.assertEqual(new_count, 0)
        self.assertEqual(existing_count, 1)
        project.import_tasks.assert_not_called()

    def test_get_tasks_failure_falls_back_to_full_import(self):
        """获取已存在任务失败时，降级为全量导入所有切片"""
        chunks = [
            {'chunk_id': 'c1', 'chunk_text': 'text1', 'chunk_title': 't1',
             'chunk_size': 100, 'doc_title': 'doc1', 'start_at': None},
            {'chunk_id': 'c2', 'chunk_text': 'text2', 'chunk_title': 't2',
             'chunk_size': 100, 'doc_title': 'doc1', 'start_at': None},
        ]
        know_client = _make_know_client({'doc1': chunks})

        # 模拟 get_tasks 抛出异常（如网络超时）
        project = MagicMock()
        project.get_tasks.side_effect = Exception("connection timeout")
        project.import_tasks.return_value = ['task1', 'task2']

        task_ids, new_count, existing_count = ls_create_tasks(know_client, project, ['doc1'])

        # 降级后应全量导入，existing_count=0
        self.assertEqual(new_count, 2)
        self.assertEqual(existing_count, 0)
        self.assertEqual(len(task_ids), 2)
        project.import_tasks.assert_called()


import json


class TestSyncAnnotationProjectLabelConfig(unittest.TestCase):
    """测试 sync_annotation_project 在项目已存在时更新 label_config"""

    def _make_app_and_client(self):
        """创建 Flask 测试客户端"""
        import app as flask_app
        flask_app.app.config['TESTING'] = True
        return flask_app.app.test_client()

    def test_existing_project_updates_label_config(self):
        """项目已存在时，应调用 project.set_params 更新 label_config"""
        with patch('src.flask_funcs.local_knowledge_detail_label_studio.LabelStudioCrud') as MockLsCrud, \
             patch('src.flask_funcs.local_knowledge_detail_label_studio.QuestionsCRUD') as MockQCrud, \
             patch('src.flask_funcs.local_knowledge_detail_label_studio.KnowledgeCrud') as MockKCrud, \
             patch('src.flask_funcs.local_knowledge_detail_label_studio.KnowledgePathCrud') as MockKpCrud, \
             patch('src.flask_funcs.local_knowledge_detail_label_studio.ls_login') as mock_ls_login, \
             patch('src.flask_funcs.local_knowledge_detail_label_studio.zlpt_login') as mock_zlpt_login, \
             patch('src.flask_funcs.local_knowledge_detail_label_studio.KnowledgeBase') as MockKnowledgeBase, \
             patch('src.flask_funcs.local_knowledge_detail_label_studio.ls_create_tasks') as mock_create_tasks, \
             patch('src.flask_funcs.local_knowledge_detail_label_studio.LabelStudioXMLGenerator') as MockXml:

            # 构造 task 数据（label_studio_project_id 已存在）
            mock_task = {
                'task_id': 'task-001',
                'task_name': 'test_task',
                'local_knowledge_id': 'lk-001',
                'question_set_id': 'qs-001',
                'label_studio_env_id': 'ls-env-001',
                'label_studio_project_id': 'ls-proj-001',
                'knowledge_base_id': 'kb-001',
            }
            ls_crud_instance = MockLsCrud.return_value.__enter__.return_value
            ls_crud_instance.annotation_task_list.return_value = [None]
            ls_crud_instance._annotation_task_to_json.return_value = mock_task
            ls_crud_instance.annotation_task_update.return_value = True

            # 构造问题集数据
            q_crud_instance = MockQCrud.return_value.__enter__.return_value
            question_json = {'doc_name': 'qs', 'datas': []}
            q_crud_instance.generate_question_json_by_qs_set_id.return_value = question_json

            # 构造知识路径
            kp_crud_instance = MockKpCrud.return_value.__enter__.return_value
            kp_crud_instance.get_knowledge_path_list.return_value = [('path-001',)]

            # 构造文档列表
            k_crud_instance = MockKCrud.return_value.__enter__.return_value
            k_crud_instance.knowledge_list.return_value = [('doc-001',)]

            # 构造 LS project
            mock_project = MagicMock()
            mock_ls_user = mock_ls_login.return_value
            mock_ls_user.get_project.return_value = mock_project

            # 构造 XML generator
            mock_xml_instance = MockXml.return_value
            mock_xml_instance.generate_from_json.return_value = '<View></View>'

            # mock 网络相关
            mock_zlpt_login.return_value = MagicMock()
            MockKnowledgeBase.return_value = MagicMock()

            # ls_create_tasks 返回（new_chunks=2, existing_chunks=0）
            mock_create_tasks.return_value = (['t1'], 2, 0)

            client = self._make_app_and_client()
            resp = client.post(
                '/local_knowledge_detail/label_studio/sync_project',
                json={'task_id': 'task-001'},
                content_type='application/json'
            )

            data = json.loads(resp.data)
            self.assertTrue(data['success'], msg=f"响应: {data}")

            # 核心断言：应该调用了 set_params 更新 label_config
            mock_project.set_params.assert_called_once_with(label_config='<View></View>')


if __name__ == '__main__':
    unittest.main()
