from typing import Optional, List, Tuple
from src.sql_funs.sql_base import PostgreSQLManager
import logging

logger = logging.getLogger(__name__)


class MetricTasksCRUD(PostgreSQLManager):
    def metric_task_create(self, task_id: str, status: str = '初始化',
                           search_type: str = None):
        """
        创建指标任务
        """
        data = {
            "task_id": task_id,
            "status": status,
            "search_type": search_type
        }
        # 只插入非空值
        data = {k: v for k, v in data.items() if v is not None}
        return self.insert("ai_metric_tasks", data=data)

    def metric_task_update(self, task_id: str, status: str = None,
                           search_type: str = None,report_path=None):
        """
        更新指标任务
        """
        data = {
            key: value for key, value in locals().items()
            if key not in ['self', 'task_id'] and value is not None
        }
        if not data:
            return False
        try:
            result = self.update("ai_metric_tasks", data, task_id=task_id)
            return result
        except Exception as e:
            logger.error(f"更新指标任务失败: {e}")
            return False

    def metric_task_delete(self, task_id: str):
        """
        删除指标任务
        """
        return self.delete("ai_metric_tasks", task_id=task_id)

    def metric_task_get_by_id(self, task_id: str) -> Optional[Tuple]:
        """
        根据任务ID获取指标任务信息
        """
        query = "SELECT * FROM ai_metric_tasks WHERE task_id = %s"
        result = self.execute_query(query, (task_id,))
        return result[0] if result else None

    def metric_task_list(self, task_id: str = None, status: str = None,
                         search_type: str = None, order_by: str = None, limit: int = None, **kwargs) -> Optional[
        List[Tuple]]:
        """
        获取指标任务列表
        支持按条件查询
        """
        exact_match_fields = ['task_id', 'status', 'search_type']
        partial_match_fields = []  # 没有需要模糊匹配的字段
        allowed_fileds = exact_match_fields + partial_match_fields + ['order_by', 'limit']

        # 添加传入的额外参数
        query_params = {k: v for k, v in locals().items()
                        if k in ['task_id', 'status', 'search_type'] and v is not None}
        query_params.update({k: v for k, v in kwargs.items() if v is not None})

        query, params = self.gen_select_query('ai_metric_tasks',
                                              order_by=order_by,
                                              limit=limit,
                                              exact_match_fields=exact_match_fields,
                                              partial_match_fields=partial_match_fields,
                                              allowed_fileds=allowed_fileds,
                                              **query_params)
        return self.execute_query(query, params)


    def _metric_task_to_json(self, row):
        """将指标任务数据库记录转换为JSON格式"""
        if not row:
            return None

        return {
            'task_id': row[0] if len(row) > 0 else None,
            'status': row[1] if len(row) > 1 else None,
            'search_type': row[2] if len(row) > 2 else None,
            'created_at': row[3].isoformat(),
            'updated_at': row[4].isoformat(),
        }

    def view_get_annotation_metric_tasks(self, task_id: str = None, local_knowledge_id: str = None,
                                         task_status: str = None, metric_status: str = None, order_by: str = None,
                                         limit: int = None, **kwargs) -> Optional[List[Tuple]]:
        """
        获取标注任务与指标任务关联信息
        """
        exact_match_fields = ['task_id', 'local_knowledge_id', 'task_status', 'metric_status']
        partial_match_fields = ['task_name']  # 任务名称可能需要模糊匹配
        allowed_fileds = exact_match_fields + partial_match_fields + ['order_by', 'limit']

        # 添加传入的额外参数
        query_params = {k: v for k, v in locals().items()
                        if k in ['task_id', 'local_knowledge_id', 'task_status',
                                 'metric_status'] and v is not None}
        query_params.update({k: v for k, v in kwargs.items() if v is not None})

        query, params = self.gen_select_query('ai_annotation_metric_tasks_view',
                                              order_by=order_by,
                                              limit=limit,
                                              exact_match_fields=exact_match_fields,
                                              partial_match_fields=partial_match_fields,
                                              allowed_fileds=allowed_fileds,
                                              **query_params)
        return self.execute_query(query, params)



    def view_annotation_metric_task_to_json(self, row):
        """将标注任务与指标任务关联视图记录转换为JSON格式"""
        if not row:
            return None

        return {
            'task_id': row[0] if len(row) > 0 else None,
            'task_name': row[1] if len(row) > 1 else None,
            'local_knowledge_id': row[2] if len(row) > 2 else None,
            'question_set_id': row[3] if len(row) > 3 else None,
            'label_studio_env_id': row[4] if len(row) > 4 else None,
            'knowledge_base_id': row[5] if len(row) > 5 else None,
            'label_studio_project_id': row[6] if len(row) > 6 else None,
            'total_chunks': row[7] if len(row) > 7 else 0,
            'annotated_chunks': row[8] if len(row) > 8 else 0,
            'task_status': row[9] if len(row) > 9 else None,
            'task_created_at': row[10].isoformat() if len(row) > 10 and row[10] and hasattr(row[10],
                                                                                            'isoformat') else None,
            'task_updated_at': row[11].isoformat() if len(row) > 11 and row[11] and hasattr(row[11],
                                                                                            'isoformat') else None,
            'annotation_type': row[12] if len(row) > 12 else None,  # 从ai_annotation_tasks表获取
            'metric_status': row[13] if len(row) > 13 else None,
            'search_type': row[14] if len(row) > 14 else None,

            'metric_created_at': row[15].isoformat(),
            'metric_updated_at': row[16].isoformat(),
        }

    # 报告表相关操作方法
    def report_create(self, report_id: str, search_type: str, filepath: str, task_id: str, status: str = '待处理',
                      error_msg: str = None):
        """
        创建报告记录
        """
        data = {
            "report_id": report_id,
            "search_type": search_type,
            "filepath": filepath,
            "task_id": task_id,
            "status": status,
            "error_msg": error_msg
        }
        # 只插入非空值
        data = {k: v for k, v in data.items() if v is not None}
        return self.insert("ai_reports", data=data)

    def report_update(self, report_id: str, search_type: str = None, filepath: str = None, task_id: str = None,
                      status: str = None, error_msg: str = None):
        """
        更新报告记录
        """
        data = {
            key: value for key, value in locals().items()
            if key not in ['self', 'report_id'] and value is not None
        }
        if not data:
            return False
        try:
            result = self.update("ai_reports", data, report_id=report_id)
            return result
        except Exception as e:
            logger.error(f"更新报告记录失败: {e}")
            return False

    def report_delete(self, report_id: str):
        """
        删除报告记录
        """
        return self.delete("ai_reports", report_id=report_id)

    def report_list(self, report_id: str = None, search_type: str = None, filepath: str = None, task_id: str = None,
                    status: str = None, error_msg: str = None, order_by: str = None, limit: int = None, **kwargs) -> \
    Optional[
        List[Tuple]]:
        """
        获取报告列表
        支持按条件查询
        """
        exact_match_fields = ['report_id', 'search_type', 'filepath', 'task_id', 'status']
        partial_match_fields = ['error_msg']  # 错误信息可能需要模糊匹配
        allowed_fileds = exact_match_fields + partial_match_fields + ['order_by', 'limit']

        # 添加传入的额外参数
        query_params = {k: v for k, v in locals().items()
                        if k in ['report_id', 'search_type', 'filepath', 'task_id', 'status',
                                 'error_msg'] and v is not None}
        query_params.update({k: v for k, v in kwargs.items() if v is not None})

        query, params = self.gen_select_query('ai_reports',
                                              order_by=order_by,
                                              limit=limit,
                                              exact_match_fields=exact_match_fields,
                                              partial_match_fields=partial_match_fields,
                                              allowed_fileds=allowed_fileds,
                                              **query_params)
        return self.execute_query(query, params)

    def _report_to_json(self, row):
        """将报告数据库记录转换为JSON格式"""
        if not row:
            return None

        return {
            'report_id': row[0] if len(row) > 0 else None,
            'search_type': row[1] if len(row) > 1 else None,
            'filepath': row[2] if len(row) > 2 else None,
            'task_id': row[3] if len(row) > 3 else None,
            'status': row[4] if len(row) > 4 else None,
            'error_msg': row[5] if len(row) > 5 else None,
            'created_at': row[6].isoformat() if len(row) > 6 and row[6] and hasattr(row[6], 'isoformat') else None,
            'updated_at': row[7].isoformat() if len(row) > 7 and row[7] and hasattr(row[7], 'isoformat') else None,
        }
