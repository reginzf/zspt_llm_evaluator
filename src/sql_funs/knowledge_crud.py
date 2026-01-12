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

    def knowledge_update(self, doc_id: str, doc_name: str = None, doc_type: str = None, doc_describe: str = None, doc_path: str = None,
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


if __name__ == '__main__':
    kno = KnowledgeCrud('10.210.2.223', 5432, 'label_studio', 'labelstudio', 'Labelstudio123')
    kno.connect()
    kno.insert()

    kno.disconnect()