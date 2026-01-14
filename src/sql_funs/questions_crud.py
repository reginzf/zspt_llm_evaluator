from typing import Optional, List, Tuple
from src.sql_funs.sql_base import PostgreSQLManager
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class QuestionsCRUD(PostgreSQLManager):
    def question_config_create(self, question_id: str, question_name: str, knowledge_id: str = None,
                               question_set_type: str = None):
        """
        创建问题集配置
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
        """
        data = {
            key: value for key, value in locals().items()
            if key not in ['self', 'question_id'] and value is not None
        }
        if not data:
            return False

        return self.update("ai_question_config", data, question_id=question_id)

    def question_config_delete(self, question_id: str):
        """
        删除问题集配置
        """
        return self.delete("ai_question_config", question_id=question_id)

    def question_config_list(self, knowledge_id: str = None, order_by: str = None, limit: int = None, **kwargs) -> \
            Optional[List[Tuple]]:
        """
        获取问题集配置列表
        支持按 knowledge_id 精确查询，或按 question_name 模糊查询
        支持排序和限制结果数量
        """
        exact_match_fields = ['knowledge_id', 'question_id']
        partial_match_fields = ['question_name']
        allowed_fileds = exact_match_fields + partial_match_fields
        query, params = self.gen_select_query('ai_question_config', order_by=order_by, limit=limit,
                                              exact_match_fields=exact_match_fields,
                                              partial_match_fields=partial_match_fields,
                                              allowed_fileds=allowed_fileds, **kwargs)
        return self.execute_query(query, params)

    def _question_config_to_json(self, question_config_tuple):
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
        """
        return self._create_question("ai_basic_questions", question_id, question_type, question_content,
                                     question_set_id, chunk_ids)

    def create_detailed_question(self, question_id: str, question_type: str, question_content: str,
                                 question_set_id: str = None, chunk_ids: List[str] = None):
        """
        创建详细问题
        """
        return self._create_question("ai_detailed_questions", question_id, question_type, question_content,
                                     question_set_id, chunk_ids)

    def create_mechanism_question(self, question_id: str, question_type: str, question_content: str,
                                  question_set_id: str = None, chunk_ids: List[str] = None):
        """
        创建机制问题
        """
        return self._create_question("ai_mechanism_questions", question_id, question_type, question_content,
                                     question_set_id, chunk_ids)

    def create_thematic_question(self, question_id: str, question_type: str, question_content: str,
                                 question_set_id: str = None, chunk_ids: List[str] = None):
        """
        创建主题问题
        """
        return self._create_question("ai_thematic_questions", question_id, question_type, question_content,
                                     question_set_id, chunk_ids)

    def get_questions_by_type(self, question_set_type: str, question_id: str = None, question_set_id: str = None,
                              question_type: str = None, question_content: str = None, chunk_ids: str = None) -> \
            Optional[List[Tuple]]:
        """
        根据类型获取问题
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
        """
        table_name = self._get_question_table_by_type(question_type)
        if not table_name:
            return False

        return self.delete(table_name, question_id=question_id)

    def _get_question_table_by_type(self, question_type: str) -> str:
        """
        根据问题类型获取对应的表名
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
        问题表结构：(id, question_id, question_set_id, question_type, question_content, chunk_ids, created_at, updated_at)
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
        根据question_set_id获取所有问题，并返回json
        :param question_set_id:
        :return:
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
