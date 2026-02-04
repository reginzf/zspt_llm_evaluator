# -*- coding: utf-8 -*-
"""
标注任务与指标任务关联管理CRUD操作模块

此模块提供了标注任务与指标任务关联信息的完整CRUD操作接口，
包括关联信息的查询和数据格式转换。
"""
from typing import Optional, List, Tuple
from src.sql_funs.sql_base import PostgreSQLManager
import logging

logger = logging.getLogger(__name__)


class AnnotationMetricTasksCRUD(PostgreSQLManager):
    """
    标注任务与指标任务关联管理CRUD操作类
    
    继承自PostgreSQLManager，提供针对标注任务与指标任务关联信息的数据库操作方法，
    包括关联信息的查询和数据格式转换。
    """
    
    def get_annotation_metric_tasks(self, task_id: str = None, local_knowledge_id: str = None, 
                                   annotation_type: str = None, task_status: str = None, 
                                   metric_status: str = None, order_by: str = None, 
                                   limit: int = None, **kwargs) -> Optional[List[Tuple]]:
        """
        获取标注任务与指标任务关联信息
        
        从ai_annotation_metric_tasks_view视图中查询标注任务与指标任务的关联信息，
        支持多种查询条件、排序和结果数量限制。
        
        Args:
            task_id (str, optional): 任务ID
            local_knowledge_id (str, optional): 本地知识库ID
            annotation_type (str, optional): 标注类型
            task_status (str, optional): 任务状态
            metric_status (str, optional): 指标状态
            order_by (str, optional): 排序字段
            limit (int, optional): 限制返回结果数量
            **kwargs: 其他查询条件参数
        
        Returns:
            Optional[List[Tuple]]: 查询结果列表，每个元素为元组形式的记录
        """
        exact_match_fields = ['task_id', 'local_knowledge_id', 'annotation_type', 'task_status', 'metric_status']
        partial_match_fields = ['task_name']  # 任务名称可能需要模糊匹配
        allowed_fileds = exact_match_fields + partial_match_fields + ['order_by', 'limit']
        
        # 添加传入的额外参数
        query_params = {k: v for k, v in locals().items() 
                       if k in ['task_id', 'local_knowledge_id', 'annotation_type', 'task_status', 'metric_status'] and v is not None}
        query_params.update({k: v for k, v in kwargs.items() if v is not None})
        
        query, params = self.gen_select_query('ai_annotation_metric_tasks_view', 
                                           order_by=order_by, 
                                           limit=limit,
                                           exact_match_fields=exact_match_fields,
                                           partial_match_fields=partial_match_fields,
                                           allowed_fileds=allowed_fileds, 
                                           **query_params)
        return self.execute_query(query, params)

    def get_annotation_metric_tasks_by_knowledge_id(self, local_knowledge_id: str) -> Optional[List[Tuple]]:
        """
        根据本地知识库ID获取标注任务与指标任务关联信息
        
        从ai_annotation_metric_tasks_view视图中查询指定本地知识库ID的
        标注任务与指标任务关联信息，并按创建时间倒序排列。
        
        Args:
            local_knowledge_id (str): 本地知识库ID
        
        Returns:
            Optional[List[Tuple]]: 查询结果列表，每个元素为元组形式的记录
        """
        query = "SELECT * FROM ai_annotation_metric_tasks_view WHERE local_knowledge_id = %s ORDER BY task_created_at DESC"
        return self.execute_query(query, (local_knowledge_id,))

    def _annotation_metric_task_to_json(self, row):
        """
        将标注任务与指标任务关联视图记录转换为JSON格式
        
        将数据库查询返回的元组格式关联信息转换为字典格式，
        便于前端展示和数据处理，并将日期时间格式转换为ISO格式字符串。
        
        Args:
            row (Tuple): 数据库查询返回的关联信息元组
        
        Returns:
            dict or None: 转换后的关联信息字典，如果输入为None则返回None
        """
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
            'task_created_at': row[10].isoformat() if len(row) > 10 and row[10] and hasattr(row[10], 'isoformat') else None,
            'task_updated_at': row[11].isoformat() if len(row) > 11 and row[11] and hasattr(row[11], 'isoformat') else None,
            'annotation_type': row[12] if len(row) > 12 else None,
            'metric_status': row[13] if len(row) > 13 else None,
            'search_type': row[14] if len(row) > 14 else None,
            'report_path': row[15] if len(row) > 15 else None,
            'metric_created_at': row[16].isoformat() if len(row) > 16 and row[16] and hasattr(row[16], 'isoformat') else None,
            'metric_updated_at': row[17].isoformat() if len(row) > 17 and row[17] and hasattr(row[17], 'isoformat') else None,
        }