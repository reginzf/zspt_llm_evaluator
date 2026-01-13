from typing import Optional, List, Tuple
from src.sql_funs.sql_base import PostgreSQLManager
import logging

logger = logging.getLogger(__name__)


class KnowledgeCrud(PostgreSQLManager):
    def knowledge_insert(self, doc_id: str, doc_name: str, doc_type: str, doc_describe: str, doc_path: str,
                         kno_path_id: str, knowledge_id: str):
        """
        插入知识库信息
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
        更新知识库信息
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
        删除知识库信息
        """
        return self.delete("ai_knowledge", doc_id=doc_id)

    def knowledge_get_by_id(self, doc_id: str) -> Optional[Tuple]:
        """
        根据文档ID获取知识库信息
        """
        query = "SELECT * FROM ai_knowledge WHERE doc_id = %s"
        result = self.execute_query(query, (doc_id,))
        return result[0] if result else None

    def knowledge_list(self, doc_name: str = None, doc_type: str = None, kno_path_id: str = None,
                       knowledge_id: str = None, order_by: str = None, limit: int = None, **kwargs) -> Optional[
        List[Tuple]]:
        """
        获取知识库列表
        支持按条件查询，模糊匹配文档名称，精确匹配其他字段
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
        """
        result = self.knowledge_get_by_id(doc_id)
        return result is not None

    def _knowledge_to_json(self, row):
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
