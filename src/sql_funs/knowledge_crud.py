# -*- coding: utf-8 -*-
"""
知识库文档CRUD操作模块

此模块提供了知识库文档管理的完整CRUD操作接口，
包括文档的增删改查等基本操作。
"""
from typing import Optional, List, Tuple
from src.sql_funs.sql_base import PostgreSQLManager
import logging

logger = logging.getLogger(__name__)


class KnowledgeCrud(PostgreSQLManager):
    """
    知识库文档CRUD操作类
    
    继承自PostgreSQLManager，提供针对知识库文档的数据库操作方法，
    包括文档的插入、更新、删除、查询等操作。
    """
    
    def knowledge_insert(self, doc_id: str, doc_name: str, doc_type: str, doc_describe: str, doc_path: str,
                         kno_path_id: str, knowledge_id: str):
        """
        插入知识库文档信息
        
        在ai_knowledge表中插入新的知识库文档记录。
        
        Args:
            doc_id (str): 文档ID
            doc_name (str): 文档名称
            doc_type (str): 文档类型
            doc_describe (str): 文档描述
            doc_path (str): 文档路径
            kno_path_id (str): 知识路径ID
            knowledge_id (str): 知识库ID
        
        Returns:
            bool: 插入成功返回True，失败返回False
        """
        return self.insert("ai_knowledge", data={
            "doc_id": doc_id,
            "doc_name": doc_name,
            "doc_type": doc_type,
            "doc_describe": doc_describe,
            "doc_path": doc_path,
            "kno_path_id": kno_path_id,
            "knowledge_id": knowledge_id
        })

    def knowledge_update(self, doc_id: str, doc_name: str = None, doc_type: str = None, doc_describe: str = None,
                         doc_path: str = None,
                         kno_path_id: str = None, knowledge_id: str = None):
        """
        更新知识库文档信息
        
        根据文档ID更新ai_knowledge表中的知识库文档记录。
        
        Args:
            doc_id (str): 要更新的文档ID
            doc_name (str, optional): 新的文档名称
            doc_type (str, optional): 新的文档类型
            doc_describe (str, optional): 新的文档描述
            doc_path (str, optional): 新的文档路径
            kno_path_id (str, optional): 新的知识路径ID
            knowledge_id (str, optional): 新的知识库ID
        
        Returns:
            bool: 更新成功返回True，失败返回False
        """
        data = {
            key: value for key, value in locals().items()
            if key not in ['self', 'doc_id'] and value is not None
        }

        if not data:
            return False

        try:
            result = self.update("ai_knowledge", data, doc_id=doc_id)
            return result
        except Exception as e:
            # 记录错误以便调试
            print(f"更新知识库信息失败: {e}")
            return False

    def knowledge_delete(self, doc_id: str):
        """
        删除知识库文档信息
        
        根据文档ID从ai_knowledge表中删除知识库文档记录。
        
        Args:
            doc_id (str): 要删除的文档ID
        
        Returns:
            bool: 删除成功返回True，失败返回False
        """
        return self.delete("ai_knowledge", doc_id=doc_id)

    def knowledge_get_by_id(self, doc_id: str) -> Optional[Tuple]:
        """
        根据文档ID获取知识库文档信息
        
        从ai_knowledge表中查询指定ID的文档记录。
        
        Args:
            doc_id (str): 要查询的文档ID
        
        Returns:
            Optional[Tuple]: 查询结果元组，如果未找到返回None
        """
        query = "SELECT * FROM ai_knowledge WHERE doc_id = %s"
        result = self.execute_query(query, (doc_id,))
        return result[0] if result else None

    def knowledge_list(self, doc_name: str = None, doc_type: str = None, kno_path_id: str = None,
                       knowledge_id: str = None, order_by: str = None, limit: int = None, **kwargs) -> Optional[
        List[Tuple]]:
        """
        获取知识库文档列表
        
        从ai_knowledge表中查询知识库文档列表，支持多种查询条件、
        排序和结果数量限制。
        
        Args:
            doc_name (str, optional): 按文档名称部分匹配查询
            doc_type (str, optional): 按文档类型精确查询
            kno_path_id (str, optional): 按知识路径ID精确查询
            knowledge_id (str, optional): 按知识库ID精确查询
            order_by (str, optional): 排序字段
            limit (int, optional): 限制返回结果数量
            **kwargs: 其他查询条件参数
        
        Returns:
            Optional[List[Tuple]]: 查询结果列表，每个元素为元组形式的记录
        """
        exact_match_fields = ['doc_id', 'doc_type', 'kno_path_id', 'knowledge_id']
        partial_match_fields = ['doc_name']
        allowed_fileds = exact_match_fields + partial_match_fields + ['order_by', 'limit']

        # 添加传入的额外参数
        query_params = {k: v for k, v in locals().items()
                        if k in ['doc_name', 'doc_type', 'kno_path_id', 'knowledge_id'] and v is not None}
        query_params.update({k: v for k, v in kwargs.items() if v is not None})

        query, params = self.gen_select_query('ai_knowledge',
                                              order_by=order_by,
                                              limit=limit,
                                              exact_match_fields=exact_match_fields,
                                              partial_match_fields=partial_match_fields,
                                              allowed_fileds=allowed_fileds,
                                              **query_params)
        return self.execute_query(query, params)

    def knowledge_exists(self, doc_id: str) -> bool:
        """
        检查知识库文档是否存在
        
        根据文档ID检查文档是否存在于ai_knowledge表中。
        
        Args:
            doc_id (str): 要检查的文档ID
        
        Returns:
            bool: 存在返回True，不存在返回False
        """
        result = self.knowledge_get_by_id(doc_id)
        return result is not None

    def _knowledge_to_json(self, row):
        """
        将知识库文档信息元组转换为JSON格式
        
        将数据库查询返回的元组格式文档信息转换为字典格式，
        便于前端展示和数据处理，并将日期时间格式转换为ISO格式字符串。
        
        Args:
            row (Tuple): 数据库查询返回的文档信息元组
        
        Returns:
            dict: 转换后的文档信息字典
        """
        return {
            'doc_id': row[0],
            'doc_name': row[1],
            'doc_type': row[2],
            'doc_describe': row[3],
            'doc_path': row[4],
            'kno_path_id': row[5],
            'knowledge_id': row[6],
            'created_at': row[7].isoformat() if row[7] else None,
            'updated_at': row[8].isoformat() if row[8] else None,
        }