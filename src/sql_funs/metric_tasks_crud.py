# -*- coding: utf-8 -*-
"""
指标任务管理CRUD操作模块

此模块提供了指标任务和报告管理的完整CRUD操作接口，
包括指标任务的创建、更新、删除、查询以及报告记录的管理。
"""
from typing import Optional, List, Tuple
from src.sql_funs.sql_base import PostgreSQLManager
import logging

logger = logging.getLogger(__name__)


class MetricTasksCRUD(PostgreSQLManager):
    """
    指标任务管理CRUD操作类
    
    继承自PostgreSQLManager，提供针对指标任务和报告的数据库操作方法，
    包括指标任务的增删改查以及报告记录的管理。
    """

    def metric_task_create(self, metric_task_id: str, task_id: str, status: str = '初始化',
                           search_type: str = None, knowledge_base_id: str = None, match_type: str = None):
        """
        创建指标任务
        
        在ai_metric_tasks表中插入新的指标任务记录。
        
        Args:
            metric_task_id: 计算任务ID
            match_type: 匹配方式
            task_id (str): 任务ID
            status (str, optional): 任务状态，默认为'初始化'
            search_type (str, optional): 搜索类型
            knowledge_base_id (str, optional): 知识库ID

        Returns:
            bool: 创建成功返回True，失败返回False
        """
        data = {
            "metric_task_id": metric_task_id,
            "task_id": task_id,
            "status": status,
            "search_type": search_type,
            "knowledge_base_id": knowledge_base_id,
            "match_type": match_type
        }
        # 只插入非空值
        data = {k: v for k, v in data.items() if v is not None}
        return self.insert("ai_metric_tasks", data=data)

    def metric_task_update(self,metric_task_id:str, task_id: str=None, status: str = None, search_type: str = None,
                          knowledge_base_id: str = None, match_type: str = None):
        """
        更新指标任务
        
        根据任务ID更新ai_metric_tasks表中的指标任务记录。
        
        Args:
            task_id (str): 要更新的任务ID
            status (str, optional): 新的任务状态
            search_type (str, optional): 新的搜索类型
            knowledge_base_id (str, optional): 新的知识库ID
            match_type (str, optional): 新的匹配方式

        Returns:
            bool: 更新成功返回True，失败返回False
        """
        data = {
            "task_id":task_id,
            "status": status,
            "search_type": search_type,
            "knowledge_base_id": knowledge_base_id,
            "match_type": match_type
        }
        # 只更新非空值
        data = {k: v for k, v in data.items() if v is not None}
        if not data:
            return False
        try:
            result = self.update("ai_metric_tasks", data, metric_task_id=metric_task_id)
            return result
        except Exception as e:
            logger.error(f"更新指标任务失败: {e}")
            return False

    def metric_task_delete(self, metric_task_id: str):
        """
        删除指标任务
        
        根据任务ID从ai_metric_tasks表中删除指标任务记录。
        
        Args:
            metric_task_id (str): 要删除的任务ID
        
        Returns:
            bool: 删除成功返回True，失败返回False
        """
        return self.delete("ai_metric_tasks", metric_task_id=metric_task_id)

    def metric_task_list(self, task_id: str = None, status: str = None, metric_task_id: str = None,
                         match_type: str = None,
                         search_type: str = None, order_by: str = None, limit: int = None, **kwargs) -> Optional[
        List[Tuple]]:
        """
        获取指标任务列表
        
        从ai_metric_tasks表中查询指标任务列表，支持多种查询条件、
        排序和结果数量限制。
        
        Args:
            metric_task_id (str, optional): 按计算任务ID精确查询
            match_type (str, optional): 按匹配类型精确查询
            task_id (str, optional): 按任务ID精确查询
            status (str, optional): 按任务状态精确查询
            search_type (str, optional): 按搜索类型精确查询
            order_by (str, optional): 排序字段
            limit (int, optional): 限制返回结果数量
            **kwargs: 其他查询条件参数
        
        Returns:
            Optional[List[Tuple]]: 查询结果列表，每个元素为元组形式的记录
        """
        exact_match_fields = ['task_id', 'status', 'search_type', 'metric_task_id']
        partial_match_fields = []  # 没有需要模糊匹配的字段
        allowed_fileds = exact_match_fields + partial_match_fields + ['order_by', 'limit']

        # 添加传入的额外参数
        query_params = {k: v for k, v in locals().items()
                        if k in allowed_fileds and v is not None}
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
        """
        将指标任务数据库记录转换为JSON格式
        
        将数据库查询返回的元组格式任务信息转换为字典格式，
        便于前端展示和数据处理，并将日期时间格式转换为ISO格式字符串。
        
        Args:
            row (Tuple): 数据库查询返回的任务信息元组
        
        Returns:
            dict or None: 转换后的任务信息字典，如果输入为None则返回None
        """
        if not row:
            return None

        return {
            'task_id': row[0] if len(row) > 0 else None,
            'status': row[1] if len(row) > 1 else None,
            'search_type': row[2] if len(row) > 2 else None,
            'created_at': row[3].isoformat(),
            'updated_at': row[4].isoformat(),
            'knowledge_base_id':row[5],
            'match_type': row[6],
            'metric_task_id': row[7]
        }

    def view_get_annotation_metric_tasks(self, task_id: str = None, local_knowledge_id: str = None,
                                         task_status: str = None, metric_status: str = None, order_by: str = None,
                                         limit: int = None, metric_task_id: str = None, match_type: str = None,
                                         **kwargs) -> Optional[List[Tuple]]:
        """
        获取标注任务与指标任务关联信息
        
        从ai_annotation_metric_tasks_view视图中查询标注任务与指标任务的关联信息。
        
        Args:
            task_id (str, optional): 任务ID
            local_knowledge_id (str, optional): 本地知识库ID
            task_status (str, optional): 任务状态
            metric_status (str, optional): 指标状态
            order_by (str, optional): 排序字段
            limit (int, optional): 限制返回结果数量
            metric_task_id (str, optional): 按计算任务ID精确查询
            match_type (str, optional): 按匹配类型精确查询
            **kwargs: 其他查询条件参数
        
        Returns:
            Optional[List[Tuple]]: 查询结果列表，每个元素为元组形式的记录
        """
        exact_match_fields = ['task_id', 'local_knowledge_id', 'task_status', 'metric_status', 'metric_task_id',
                              'match_type']
        partial_match_fields = ['task_name']  # 任务名称可能需要模糊匹配
        allowed_fileds = exact_match_fields + partial_match_fields + ['order_by', 'limit']

        # 添加传入的额外参数
        query_params = {k: v for k, v in locals().items()
                        if k in allowed_fileds and v is not None}
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
            'task_created_at': row[10].isoformat() if len(row) > 10 and row[10] and hasattr(row[10],
                                                                                            'isoformat') else None,
            'task_updated_at': row[11].isoformat() if len(row) > 11 and row[11] and hasattr(row[11],
                                                                                            'isoformat') else None,
            'annotation_type': row[12] if len(row) > 12 else None,  # 从ai_annotation_tasks表获取
            'metric_status': row[13] if len(row) > 13 else None,
            'search_type': row[14] if len(row) > 14 else None,
            'match_type': row[15],
            'metric_task_id': row[16] if len(row) > 14 else None,
            'metric_created_at': row[17].isoformat(),
            'metric_updated_at': row[18].isoformat(),
        }

    # 报告表相关操作方法
    def report_create(self, report_id: str, search_type: str, filepath: str, task_id: str, status: str = '待处理',
                      error_msg: str = None, match_type: str = None, metric_task_id=None):
        """
        创建报告记录
        
        在ai_reports表中插入新的报告记录。
        
        Args:
            metric_task_id: 计算任务ID
            report_id (str): 报告ID
            search_type (str): 搜索类型
            filepath (str): 文件路径
            task_id (str): 任务ID
            status (str, optional): 报告状态，默认为'待处理'
            error_msg (str, optional): 错误信息
            match_type (str, optional): 匹配类型
        
        Returns:
            bool: 创建成功返回True，失败返回False
        """
        data = {
            "metric_task_id": metric_task_id,
            "report_id": report_id,
            "search_type": search_type,
            "filepath": filepath,
            "task_id": task_id,
            "status": status,
            "error_msg": error_msg,
            "match_type": match_type
        }
        data = {k: v for k, v in data.items() if v is not None}
        return self.insert("ai_reports", data=data)

    def report_update(self, report_id: str, search_type: str = None, filepath: str = None, task_id: str = None,
                      status: str = None, error_msg: str = None, match_type: str = None):
        """
        更新报告记录
        
        根据报告ID更新ai_reports表中的报告记录。
        
        Args:
            report_id (str): 要更新的报告ID
            search_type (str, optional): 新的搜索类型
            filepath (str, optional): 新的文件路径
            task_id (str, optional): 新的任务ID
            status (str, optional): 新的报告状态
            error_msg (str, optional): 新的错误信息
            match_type (str, optional): 新的匹配类型
        
        Returns:
            bool: 更新成功返回True，失败返回False
        """
        data = {
            "search_type": search_type,
            "filepath": filepath,
            "task_id": task_id,
            "status": status,
            "error_msg": error_msg,
            "match_type": match_type
        }
        data = {k: v for k, v in data.items() if v is not None}
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
        
        根据报告ID从ai_reports表中删除报告记录。
        
        Args:
            report_id (str): 要删除的报告ID
        
        Returns:
            bool: 删除成功返回True，失败返回False
        """
        return self.delete("ai_reports", report_id=report_id)

    def report_list(self, report_id: str = None, search_type: str = None, filepath: str = None, task_id: str = None,
                    status: str = None, error_msg: str = None, order_by: str = None, limit: int = None,
                    metric_task_id: str = None, **kwargs) -> \
            Optional[
                List[Tuple]]:
        """
        获取报告列表
        
        从ai_reports表中查询报告列表，支持多种查询条件、
        排序和结果数量限制。
        
        Args:
            report_id (str, optional): 按报告ID精确查询
            search_type (str, optional): 按搜索类型精确查询
            filepath (str, optional): 按文件路径精确查询
            task_id (str, optional): 按任务ID精确查询
            status (str, optional): 按报告状态精确查询
            error_msg (str, optional): 按错误信息部分匹配查询
            order_by (str, optional): 排序字段
            limit (int, optional): 限制返回结果数量
            metric_task_id (str, optional)： 按计算任务ID精确查询
            **kwargs: 其他查询条件参数
        
        Returns:
            Optional[List[Tuple]]: 查询结果列表，每个元素为元组形式的记录
        """
        exact_match_fields = ['report_id', 'search_type', 'filepath', 'task_id', 'status', 'metric_task_id']
        partial_match_fields = ['error_msg']  # 错误信息可能需要模糊匹配
        allowed_fileds = exact_match_fields + partial_match_fields

        # 添加传入的额外参数
        query_params = {k: v for k, v in locals().items()
                        if k in allowed_fileds and v is not None}
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
        """
        将报告数据库记录转换为JSON格式
        
        将数据库查询返回的元组格式报告信息转换为字典格式，
        便于前端展示和数据处理，并将日期时间格式转换为ISO格式字符串。
        
        Args:
            row (Tuple): 数据库查询返回的报告信息元组
        
        Returns:
            dict or None: 转换后的报告信息字典，如果输入为None则返回None
        """
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
            'match_type': row[8] if len(row) > 8 else None,
            'metric_task_id': row[9] if len(row) > 9 else None,
        }
