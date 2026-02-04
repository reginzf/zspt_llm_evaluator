# -*- coding: utf-8 -*-
"""
问题集管理CRUD操作模块

此模块提供了问题集和问题管理的完整CRUD操作接口，
包括问题集配置的增删改查以及不同类型问题的管理。
"""
from typing import Optional, List, Tuple
from src.sql_funs.sql_base import PostgreSQLManager
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class QuestionsCRUD(PostgreSQLManager):
    """
    问题集管理CRUD操作类
    
    继承自PostgreSQLManager，提供针对问题集和问题的数据库操作方法，
    包括问题集配置的管理以及不同类型问题（基础、详细、机制、主题）的增删改查。
    """
    
    def question_config_create(self, question_id: str, question_name: str, knowledge_id: str = None,
                               question_set_type: str = None):
        """
        创建问题集配置
        
        在ai_question_config表中插入新的问题集配置记录。
        
        Args:
            question_id (str): 问题集ID
            question_name (str): 问题集名称
            knowledge_id (str, optional): 知识库ID
            question_set_type (str, optional): 问题集类型
        
        Returns:
            bool: 创建成功返回True，失败返回False
        """
        return self.insert("ai_question_config", data={
            "question_id": question_id,
            "question_name": question_name,
            "knowledge_id": knowledge_id,
            "question_set_type": question_set_type
        })

    def question_config_update(self, question_id: str, question_name: str = None, question_count: int = None,
                               question_set_type: str = None):
        """
        更新问题集配置
        
        根据问题集ID更新ai_question_config表中的问题集配置记录。
        
        Args:
            question_id (str): 要更新的问题集ID
            question_name (str, optional): 新的问题集名称
            question_count (int, optional): 问题数量
            question_set_type (str, optional): 新的问题集类型
        
        Returns:
            bool: 更新成功返回True，失败返回False
        """
        data = {
            "question_name": question_name,
            "question_count": question_count,
            "question_set_type": question_set_type
        }
        data = {k: v for k, v in data.items() if v is not None}
        if not data:
            return False
        return self.update("ai_question_config", data, question_id=question_id)

    def question_config_delete(self, question_id: str):
        """
        删除问题集配置
        
        根据问题集ID从ai_question_config表中删除问题集配置记录。
        
        Args:
            question_id (str): 要删除的问题集ID
        
        Returns:
            bool: 删除成功返回True，失败返回False
        """
        return self.delete("ai_question_config", question_id=question_id)

    def question_config_list(self, order_by: str = None, limit: int = None, **kwargs) -> \
            Optional[List[Tuple]]:
        """
        获取问题集配置列表
        
        从ai_question_config表中查询问题集配置列表，支持多种查询条件、
        排序和结果数量限制。
        
        Args:
            order_by (str, optional): 排序字段
            limit (int, optional): 限制返回结果数量
            **kwargs: 查询条件关键字参数
                - knowledge_id: 按知识库ID精确查询
                - question_id: 按问题集ID精确查询
                - question_name: 按问题集名称部分匹配查询
        
        Returns:
            Optional[List[Tuple]]: 查询结果列表，每个元素为元组形式的记录
        """
        exact_match_fields = ['knowledge_id', 'question_id']
        partial_match_fields = ['question_name']
        allowed_fileds = exact_match_fields + partial_match_fields
        query, params = self.gen_select_query('ai_question_config', order_by=order_by, limit=limit,
                                              exact_match_fields=exact_match_fields,
                                              partial_match_fields=partial_match_fields,
                                              allowed_fileds=allowed_fileds, **kwargs)
        return self.execute_query(query, params)

    def questions_list(self, order_by=None, limit=None, **kwargs):
        """
        获取问题列表
        
        从ai_annotation_task_extended_view视图中查询问题列表，
        并根据问题集类型获取相应的问题记录。
        
        Args:
            order_by (str, optional): 排序字段
            limit (int, optional): 限制返回结果数量
            **kwargs: 查询条件关键字参数
        
        Returns:
            List[dict]: 问题列表，每个元素为字典格式的问题信息
        """
        exact_match_fields = ['task_id']
        partial_match_fields = []
        allowed_fileds = exact_match_fields + partial_match_fields
        query, params = self.gen_select_query('ai_annotation_task_extended_view', order_by=order_by, limit=limit,
                                              exact_match_fields=exact_match_fields,
                                              partial_match_fields=partial_match_fields,
                                              allowed_fileds=allowed_fileds, **kwargs)
        res = self.execute_query(query, params)
        if res:
            question_set_id = res[0][3]
            qs_set_config = self.question_config_list(question_id=question_set_id)
            if not qs_set_config:
                logger.warning(f"无法获取问题集 '{question_set_id}' 的配置")
                return None
            qs_set_config = qs_set_config[0]
            qs_set_type = qs_set_config[5]

            # 获取所有问题
            questions = self.get_questions_by_type(qs_set_type, question_set_id=question_set_id)
            questions = [self._question_to_json(q) for q in questions]
            return questions
        return []

    def _question_config_to_json(self, question_config_tuple):
        """
        将问题集配置元组转换为JSON格式
        
        将数据库查询返回的元组格式问题集配置信息转换为字典格式，
        便于前端展示和数据处理。
        
        Args:
            question_config_tuple (Tuple): 数据库查询返回的问题集配置元组
        
        Returns:
            dict: 转换后的问题集配置信息字典
        """
        return {
            "question_id": question_config_tuple[0],
            "question_name": question_config_tuple[1],
            "knowledge_id": question_config_tuple[2],
            "question_set_type": question_config_tuple[5],
            "question_count": question_config_tuple[6]
        }

    def _create_question(self, table_name: str, question_id: str, question_type: str, question_content: str,
                         question_set_id: str = None, chunk_ids: List[str] = None):
        """
        通用问题创建方法
        
        在指定的问题表中插入新的问题记录。
        
        Args:
            table_name (str): 目标表名
            question_id (str): 问题ID
            question_type (str): 问题类型
            question_content (str): 问题内容
            question_set_id (str, optional): 问题集ID
            chunk_ids (List[str], optional): 分块ID列表
        
        Returns:
            bool: 创建成功返回True，失败返回False
        """
        return self.insert(table_name, data={
            "question_id": question_id,
            "question_type": question_type,
            "question_content": question_content,
            "question_set_id": question_set_id,
            "chunk_ids": chunk_ids or []
        })

    def create_basic_question(self, question_id: str, question_type: str, question_content: str,
                              question_set_id: str = None, chunk_ids: List[str] = None):
        """
        创建基础问题
        
        在ai_basic_questions表中插入新的基础问题记录。
        
        Args:
            question_id (str): 问题ID
            question_type (str): 问题类型
            question_content (str): 问题内容
            question_set_id (str, optional): 问题集ID
            chunk_ids (List[str], optional): 分块ID列表
        
        Returns:
            bool: 创建成功返回True，失败返回False
        """
        return self._create_question("ai_basic_questions", question_id, question_type, question_content,
                                     question_set_id, chunk_ids)

    def create_detailed_question(self, question_id: str, question_type: str, question_content: str,
                                 question_set_id: str = None, chunk_ids: List[str] = None):
        """
        创建详细问题
        
        在ai_detailed_questions表中插入新的详细问题记录。
        
        Args:
            question_id (str): 问题ID
            question_type (str): 问题类型
            question_content (str): 问题内容
            question_set_id (str, optional): 问题集ID
            chunk_ids (List[str], optional): 分块ID列表
        
        Returns:
            bool: 创建成功返回True，失败返回False
        """
        return self._create_question("ai_detailed_questions", question_id, question_type, question_content,
                                     question_set_id, chunk_ids)

    def create_mechanism_question(self, question_id: str, question_type: str, question_content: str,
                                  question_set_id: str = None, chunk_ids: List[str] = None):
        """
        创建机制问题
        
        在ai_mechanism_questions表中插入新的机制问题记录。
        
        Args:
            question_id (str): 问题ID
            question_type (str): 问题类型
            question_content (str): 问题内容
            question_set_id (str, optional): 问题集ID
            chunk_ids (List[str], optional): 分块ID列表
        
        Returns:
            bool: 创建成功返回True，失败返回False
        """
        return self._create_question("ai_mechanism_questions", question_id, question_type, question_content,
                                     question_set_id, chunk_ids)

    def create_thematic_question(self, question_id: str, question_type: str, question_content: str,
                                 question_set_id: str = None, chunk_ids: List[str] = None):
        """
        创建主题问题
        
        在ai_thematic_questions表中插入新的主题问题记录。
        
        Args:
            question_id (str): 问题ID
            question_type (str): 问题类型
            question_content (str): 问题内容
            question_set_id (str, optional): 问题集ID
            chunk_ids (List[str], optional): 分块ID列表
        
        Returns:
            bool: 创建成功返回True，失败返回False
        """
        return self._create_question("ai_thematic_questions", question_id, question_type, question_content,
                                     question_set_id, chunk_ids)

    def get_questions_by_type(self, question_set_type: str, question_id: str = None, question_set_id: str = None,
                              question_type: str = None, question_content: str = None, chunk_ids: str = None) -> \
            Optional[List[Tuple]]:
        """
        根据类型获取问题
        
        从指定类型的问题表中查询问题记录。
        
        Args:
            question_set_type (str): 问题集类型
            question_id (str, optional): 按问题ID精确查询
            question_set_id (str, optional): 按问题集ID精确查询
            question_type (str, optional): 按问题类型精确查询
            question_content (str, optional): 按问题内容部分匹配查询
            chunk_ids (str, optional): 按分块ID查询
        
        Returns:
            Optional[List[Tuple]]: 查询结果列表，每个元素为元组形式的记录
        """
        table_name = self._get_question_table_by_type(question_set_type)
        if not table_name:
            logger.warning(f"无法获取问题类型 '{question_set_type}' 对应的表名")
            return None

        # 构建查询参数
        kwargs = {}
        if question_id is not None:
            kwargs['question_id'] = question_id
        if question_set_id is not None:
            kwargs['question_set_id'] = question_set_id
        if question_type is not None:
            kwargs['question_type'] = question_type

        # 精确匹配字段
        exact_match_fields = ['question_id', 'question_set_id', 'question_type']
        # 模糊匹配字段
        partial_match_fields = ['question_content', 'chunk_ids']

        # 添加模糊匹配字段
        if question_content is not None:
            kwargs['question_content'] = question_content
        if chunk_ids is not None:
            kwargs['chunk_ids'] = chunk_ids

        allowed_fileds = exact_match_fields + partial_match_fields

        query, params = self.gen_select_query(table_name,
                                              exact_match_fields=exact_match_fields,
                                              partial_match_fields=partial_match_fields,
                                              allowed_fileds=allowed_fileds, **kwargs)

        logger.info(f"执行查询: {query} 参数: {params}")
        result = self.execute_query(query, params)
        logger.info(f"查询返回 {len(result) if result else 0} 条记录")

        return result

    def update_question_by_type(self, question_id: str, question_type: str, question_content: str = None,
                                chunk_ids: List[str] = None):
        """
        根据类型更新问题
        
        根据问题ID和类型更新指定问题表中的问题记录。
        
        Args:
            question_id (str): 要更新的问题ID
            question_type (str): 问题类型
            question_content (str, optional): 新的问题内容
            chunk_ids (List[str], optional): 新的分块ID列表
        
        Returns:
            bool: 更新成功返回True，失败返回False
        """
        table_name = self._get_question_table_by_type(question_type)
        if not table_name:
            return False

        # 构建更新数据
        update_data = {}
        if question_content is not None:
            update_data["question_content"] = question_content
        if chunk_ids is not None:
            update_data["chunk_ids"] = chunk_ids

        if not update_data:
            return False

        return self.update(table_name, update_data, question_id=question_id)

    def delete_question_by_type(self, question_id: str, question_type: str):
        """
        根据类型删除问题
        
        根据问题ID和类型从指定问题表中删除问题记录。
        
        Args:
            question_id (str): 要删除的问题ID
            question_type (str): 问题类型
        
        Returns:
            bool: 删除成功返回True，失败返回False
        """
        table_name = self._get_question_table_by_type(question_type)
        if not table_name:
            return False

        return self.delete(table_name, question_id=question_id)

    def _get_question_table_by_type(self, question_type: str) -> str:
        """
        根据问题类型获取对应的表名
        
        根据问题类型返回对应的问题表名。
        
        Args:
            question_type (str): 问题类型
        
        Returns:
            str: 对应的问题表名，如果类型不匹配则返回None
        """
        question_type_mapping = {
            'basic': 'ai_basic_questions',
            'detailed': 'ai_detailed_questions',
            'mechanism': 'ai_mechanism_questions',
            'thematic': 'ai_thematic_questions'
        }
        return question_type_mapping.get(question_type)

    def _question_to_json(self, question_tuple):
        """
        将问题记录元组转换为JSON格式
        
        将数据库查询返回的元组格式问题信息转换为字典格式，
        便于前端展示和数据处理，并将日期时间格式转换为ISO格式字符串。
        
        问题表结构：(id, question_id, question_set_id, question_type, question_content, chunk_ids, created_at, updated_at)
        
        Args:
            question_tuple (Tuple): 数据库查询返回的问题记录元组
        
        Returns:
            dict or None: 转换后的问题信息字典，如果输入为None则返回None
        """
        if question_tuple:
            return {
                "id": question_tuple[0] if len(question_tuple) > 0 else None,
                "question_id": question_tuple[1] if len(question_tuple) > 1 else None,
                "question_set_id": question_tuple[2] if len(question_tuple) > 2 else None,
                "question_type": question_tuple[3] if len(question_tuple) > 3 else None,
                "question_content": question_tuple[4] if len(question_tuple) > 4 else None,
                "chunk_ids": question_tuple[5] if len(question_tuple) > 5 else [],
                "created_at": question_tuple[6].isoformat() if len(question_tuple) > 6 and question_tuple[
                    6] and hasattr(question_tuple[6], 'isoformat') else None,
                "updated_at": question_tuple[7].isoformat() if len(question_tuple) > 7 and question_tuple[
                    7] and hasattr(question_tuple[7], 'isoformat') else None
            }
        return None

    def generate_question_json_by_qs_set_id(self, question_set_id: str) -> dict:
        """
        根据问题集ID获取所有问题，并返回JSON格式
        
        根据问题集ID查询所有相关的问题，并按照类型整理成JSON格式返回。
        
        Args:
            question_set_id (str): 问题集ID
        
        Returns:
            dict: 包含问题集名称和按类型分类的问题列表的字典
        """
        # 获取qs_set相关配置
        qs_set_config = self.question_config_list(question_id=question_set_id)
        if not qs_set_config:
            logger.warning(f"无法获取问题集 '{question_set_id}' 的配置")
            return None
        qs_set_config = qs_set_config[0]
        qs_set_type = qs_set_config[5]
        qs_set_name = qs_set_config[1]
        # 获取所有问题
        questions = self.get_questions_by_type(qs_set_type, question_set_id=question_set_id)
        if not questions:
            logger.info(f"问题集 '{question_set_id}' 中没有问题")
            return {"doc_name": qs_set_name, "datas": []}

        questions = [self._question_to_json(question) for question in questions]
        questions_by_type = defaultdict(list)
        for question in questions:
            q_type = question.get('question_type', 'factual')  # 默认为factual类型
            questions_by_type[q_type].append(question['question_content'])
        result = {
            "doc_name": qs_set_name,
            "datas": [{"type": q_type, "label_type": "Choice", "label_config": {"choice": "multiple"},
                       "questions": question_contents} for q_type, question_contents in questions_by_type.items()]
        }
        return result