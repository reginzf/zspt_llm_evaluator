from typing import Optional, List, Tuple
from src.sql_funs.sql_base import PostgreSQLManager


class QuestionsCRUD(PostgreSQLManager):

    def get_question_detail(self, question_id: str = None) -> Optional[List[Tuple]]:
        """
        获取问题详细信息
        """
        query = "SELECT * FROM ai_question_detail_view"
        params = None

        if question_id:
            query += " WHERE question_id = %s"
            params = (question_id,)

        return self.execute_query(query, params)
