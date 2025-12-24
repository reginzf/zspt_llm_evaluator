from typing import Optional, List, Tuple
from src.sql_funs.sql_base import PostgreSQLManager


class KnowledgeCrud(PostgreSQLManager):
    def get_knowledge_detail(self, knowledge_id: str = None) -> Optional[List[Tuple]]:
        """
        获取知识库详细信息
        """
        query = "SELECT * FROM ai_knowledge_detail_view"
        params = None

        if knowledge_id:
            query += " WHERE knowledge_id = %s"
            params = (knowledge_id,)

        return self.execute_query(query, params)

    def get_knowledge_structure(self, knowledge_id: str = None) -> Optional[List[Tuple]]:
        """
        获取知识结构信息
        """
        query = "SELECT * FROM ai_knowledge_structure_view"
        params = None

        if knowledge_id:
            query += " WHERE knowledge_id = %s"
            params = (knowledge_id,)

        query += " ORDER BY display_order"

        return self.execute_query(query, params)
