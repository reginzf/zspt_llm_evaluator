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

        task_ids, new_count, existing_count = ls_create_tasks(know_client, project, ['doc1'])

        self.assertEqual(new_count, 1)
        self.assertEqual(existing_count, 1)
        # import_tasks 只应被调用一次，且只传了 c2 对应的数据
        # call_args[0][0] 是传给 import_tasks 的第一个位置参数（切片列表）
        call_args = project.import_tasks.call_args[0][0]
        self.assertEqual(len(call_args), 1)
        self.assertEqual(call_args[0]['chunk_id'], 'c2')

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


if __name__ == '__main__':
    unittest.main()
