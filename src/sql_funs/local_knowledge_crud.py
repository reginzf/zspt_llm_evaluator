from typing import Optional, List, Tuple
from src.sql_funs.sql_base import PostgreSQLManager


class LocalKnowledgeCrud(PostgreSQLManager):
    def local_knowledge_insert(self, kno_id: str, kno_name: str, kno_describe: str, kno_path: str,
                         knol_id: str, ls_status: int = 1):
        """
        插入本地知识库信息
        """
        return self.insert("ai_local_knowledge", data={
            "kno_id": kno_id,
            "kno_name": kno_name,
            "kno_describe": kno_describe,
            "kno_path": kno_path,
            "knol_id": knol_id,
            "ls_status": ls_status
        })

    def local_knowledge_update(self, kno_id: str, kno_name: str = None, kno_describe: str = None, 
                             kno_path: str = None, knol_id: str = None, ls_status: int = None):
        """
        更新本地知识库信息
        """
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
            return self.cursor.rowcount > 0
        except Exception as e:
            self.connection.rollback()
            return False

    def local_knowledge_delete(self, kno_id: str):
        """
        删除本地知识库信息
        """
        query = "DELETE FROM ai_local_knowledge WHERE kno_id = %s"
        params = (kno_id,)
        
        try:
            self.cursor.execute(query, params)
            self.connection.commit()
            # 检查是否有行被删除
            return self.cursor.rowcount > 0
        except Exception as e:
            self.connection.rollback()
            return False

    def get_local_knowledge_detail(self, kno_id: str = None) -> Optional[List[Tuple]]:
        """
        获取本地知识库详细信息
        """
        if kno_id:
            query = "SELECT * FROM ai_local_knowledge WHERE kno_id = %s"
            return self.execute_query(query, (kno_id,))
        else:
            query = "SELECT * FROM ai_local_knowledge"
            return self.execute_query(query, None)
        
    def get_local_knowledge_by_knol_id(self, knol_id: str) -> Optional[List[Tuple]]:
        """
        根据knol_id获取本地知识库信息
        """
        query = "SELECT * FROM ai_local_knowledge WHERE knol_id = %s"
        return self.execute_query(query, (knol_id,))

    def get_local_knowledge(self, kno_id: str = None, kno_name: str = None, kno_describe: str = None, 
                           kno_path: str = None, order_by: str = None, limit: int = None) -> Optional[List[Tuple]]:
        """
        获取本地知识库详细信息
        支持按 kno_id 精确查询，或按 kno_name、kno_describe、kno_path 模糊查询
        支持排序和限制结果数量
        """
        # 构建查询条件
        where_parts = []
        params = []
        
        if kno_id:
            where_parts.append("kno_id = %s")
            params.append(kno_id)
        
        if kno_name:
            where_parts.append("kno_name ILIKE %s")
            params.append(f"%{kno_name}%")
        
        if kno_describe:
            where_parts.append("kno_describe ILIKE %s")
            params.append(f"%{kno_describe}%")
        
        if kno_path:
            where_parts.append("kno_path ILIKE %s")
            params.append(f"%{kno_path}%")
        
        # 组合查询语句
        query = "SELECT * FROM ai_local_knowledge"
        
        if where_parts:
            query += " WHERE " + " AND ".join(where_parts)
        
        if order_by:
            query += f" ORDER BY {order_by}"
        
        if limit:
            query += " LIMIT %s"
            params.append(limit)
        
        return self.execute_query(query, tuple(params))