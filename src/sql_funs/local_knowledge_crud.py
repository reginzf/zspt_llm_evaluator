from typing import Optional, List, Tuple
from src.sql_funs.sql_base import PostgreSQLManager


class LocalKnowledgeCrud(PostgreSQLManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    def local_knowledge_insert(self, kno_id: str, kno_name: str, kno_describe: str, kno_path: str,
                         knol_id: str, ls_status: int = 1):
        """
        插入本地知识库信息
        """
        self.logger.info(f"开始插入本地知识库信息，kno_id: {kno_id}")
        try:
            result = self.insert("ai_local_knowledge", data={
                "kno_id": kno_id,
                "kno_name": kno_name,
                "kno_describe": kno_describe,
                "kno_path": kno_path,
                "knol_id": knol_id,
                "ls_status": ls_status
            })
            self.logger.info(f"插入本地知识库信息成功，kno_id: {kno_id}")
            return result
        except Exception as e:
            self.logger.error(f"插入本地知识库信息失败，kno_id: {kno_id}, 错误: {str(e)}")
            raise

    def local_knowledge_update(self, kno_id: str, kno_name: str = None, kno_describe: str = None, 
                             kno_path: str = None, knol_id: str = None, ls_status: int = None):
        """
        更新本地知识库信息
        """
        self.logger.info(f"开始更新本地知识库信息，kno_id: {kno_id}")
        data = {}
        if kno_name is not None:
            data["kno_name"] = kno_name
        if kno_describe is not None:
            data["kno_describe"] = kno_describe
        if kno_path is not None:
            data["kno_path"] = kno_path
        if knol_id is not None:
            data["knol_id"] = knol_id
        if ls_status is not None:
            data["ls_status"] = ls_status

        if not data:
            self.logger.warning(f"没有要更新的数据，kno_id: {kno_id}")
            return False  # 如果没有要更新的数据，返回False

        # 构建更新语句
        set_clauses = []
        param_values = []
        for key, value in data.items():
            set_clauses.append(f"{key} = %s")
            param_values.append(value)
        
        set_clause = ", ".join(set_clauses)
        query = f"UPDATE ai_local_knowledge SET {set_clause} WHERE kno_id = %s"
        params = param_values + [kno_id]
        
        try:
            self.cursor.execute(query, params)
            self.connection.commit()
            # 检查是否有行被更新
            updated = self.cursor.rowcount > 0
            if updated:
                self.logger.info(f"更新本地知识库信息成功，kno_id: {kno_id}")
            else:
                self.logger.warning(f"未找到要更新的本地知识库信息，kno_id: {kno_id}")
            return updated
        except Exception as e:
            self.logger.error(f"更新本地知识库信息失败，kno_id: {kno_id}, 错误: {str(e)}")
            self.connection.rollback()
            return False

    def local_knowledge_delete(self, kno_id: str):
        """
        删除本地知识库信息
        """
        self.logger.info(f"开始删除本地知识库信息，kno_id: {kno_id}")
        query = "DELETE FROM ai_local_knowledge WHERE kno_id = %s"
        params = (kno_id,)
        
        try:
            self.cursor.execute(query, params)
            self.connection.commit()
            # 检查是否有行被删除
            deleted = self.cursor.rowcount > 0
            if deleted:
                self.logger.info(f"删除本地知识库信息成功，kno_id: {kno_id}")
            else:
                self.logger.warning(f"未找到要删除的本地知识库信息，kno_id: {kno_id}")
            return deleted
        except Exception as e:
            self.logger.error(f"删除本地知识库信息失败，kno_id: {kno_id}, 错误: {str(e)}")
            self.connection.rollback()
            return False

    def get_local_knowledge_detail(self, kno_id: str = None) -> Optional[List[Tuple]]:
        """
        获取本地知识库详细信息
        """
        if kno_id:
            self.logger.info(f"开始获取本地知识库详细信息，kno_id: {kno_id}")
            query = "SELECT * FROM ai_local_knowledge WHERE kno_id = %s"
            result = self.execute_query(query, (kno_id,))
        else:
            self.logger.info("开始获取所有本地知识库详细信息")
            query = "SELECT * FROM ai_local_knowledge"
            result = self.execute_query(query, None)
        self.logger.info(f"获取本地知识库详细信息完成，结果数量: {len(result) if result else 0}")
        return result
        
    def get_local_knowledge_by_knol_id(self, knol_id: str) -> Optional[List[Tuple]]:
        """
        根据knol_id获取本地知识库信息
        """
        self.logger.info(f"开始根据knol_id获取本地知识库信息，knol_id: {knol_id}")
        query = "SELECT * FROM ai_local_knowledge WHERE knol_id = %s"
        result = self.execute_query(query, (knol_id,))
        self.logger.info(f"根据knol_id获取本地知识库信息完成，knol_id: {knol_id}, 结果数量: {len(result) if result else 0}")
        return result
