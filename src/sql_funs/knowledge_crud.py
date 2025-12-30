# ai_knowledge* 开头表的增删改查走这个模块
from typing import Optional, List, Tuple
from src.sql_funs.sql_base import PostgreSQLManager


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

    def knowledge_update(self, doc_id: str, doc_name: str, doc_type: str, doc_describe: str, doc_path: str,
                         kno_path_id: str, knowledge_id: str):
        """
        更新知识库信息
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


if __name__ == '__main__':
    kno = KnowledgeCrud('10.210.2.223', 5432, 'label_studio', 'labelstudio', 'Labelstudio123')
    kno.connect()
    kno.insert()
    print(kno.get_knowledge_structure())
    kno.disconnect()
