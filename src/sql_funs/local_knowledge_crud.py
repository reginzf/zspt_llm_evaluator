from typing import Optional, List, Tuple
from src.sql_funs.sql_base import PostgreSQLManager
import logging

logger = logging.getLogger(__name__)


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

    def get_local_knowledge(self, order_by: str = None, limit: int = None, **kwargs) -> Optional[List[Tuple]]:
        """
        获取本地知识库详细信息
        支持按 kno_id 精确查询，或按 kno_name、kno_describe、kno_path 模糊查询
        支持排序和限制结果数量
        """
        exact_match_fields = ['kno_id', 'ls_status']
        partial_match_fields = ['kno_name', 'kno_describe', 'kno_path']
        allowed_fileds = ['kno_id', 'ls_status', 'kno_name', 'kno_describe', 'kno_path']
        query, params = self.gen_select_query('ai_local_knowledge', order_by=order_by, limit=limit,
                                              exact_match_fields=exact_match_fields,
                                              partial_match_fields=partial_match_fields,
                                              allowed_fileds=allowed_fileds, **kwargs)
        logger.info(f"执行查询: {query}")
        return self.execute_query(query, params)

    # 为 ai_local_knowledge_list 表添加 CRUD 方法
    def local_knowledge_list_insert(self, knol_id: str, knol_name: str, knol_describe: str = None,
                                    knol_path: str = None, ls_status: int = 1, kno_id=None):
        """
        插入本地知识库列表信息
        """
        return self.insert("ai_local_knowledge_list", data={
            "knol_id": knol_id,
            "knol_name": knol_name,
            "knol_describe": knol_describe,
            "knol_path": knol_path,
            "ls_status": ls_status,
            "kno_id": kno_id
        })

    def local_knowledge_list_update(self, knol_id: str, knol_name: str = None, knol_describe: str = None,
                                    knol_path: str = None, ls_status: int = None):
        """
        更新本地知识库列表信息
        """
        data = {}
        if knol_name is not None:
            data["knol_name"] = knol_name
        if knol_describe is not None:
            data["knol_describe"] = knol_describe
        if knol_path is not None:
            data["knol_path"] = knol_path
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
        query = f"UPDATE ai_local_knowledge_list SET {set_clause} WHERE knol_id = %s"
        params = param_values + [knol_id]

        try:
            self.cursor.execute(query, params)
            self.connection.commit()
            # 检查是否有行被更新
            return self.cursor.rowcount > 0
        except Exception as e:
            self.connection.rollback()
            return False

    def local_knowledge_list_delete(self, knol_id: str):
        """
        删除本地知识库列表信息
        """
        query = "DELETE FROM ai_local_knowledge_list WHERE knol_id = %s"
        params = (knol_id,)

        try:
            self.cursor.execute(query, params)
            self.connection.commit()
            # 检查是否有行被删除
            return self.cursor.rowcount > 0
        except Exception as e:
            self.connection.rollback()
            return False

    def get_local_knowledge_list(self, knol_id: str = None, knol_name: str = None, order_by: str = None,
                                 limit: int = None) -> Optional[List[Tuple]]:
        """
        获取本地知识库列表信息
        支持按 knol_id 精确查询，或按 knol_name 模糊查询
        支持排序和限制结果数量
        """
        # 构建查询条件
        where_parts = []
        params = []

        if knol_id:
            where_parts.append("knol_id = %s")
            params.append(knol_id)

        if knol_name:
            where_parts.append("knol_name ILIKE %s")
            params.append(f"%{knol_name}%")

        # 组合查询语句
        query = "SELECT * FROM ai_local_knowledge_list"

        if where_parts:
            query += " WHERE " + " AND ".join(where_parts)

        if order_by:
            query += f" ORDER BY {order_by}"

        if limit:
            query += " LIMIT %s"
            params.append(limit)
        self.gen_select_query('ai_local_knowledge_list', order_by, limit, )
        return self.execute_query(query, tuple(params))

    # 为 ai_knowledge_base 表添加 CRUD 方法
    def knowledge_base_insert(self, knowledge_id: str, knowledge_name: str, kno_root_id: str = None,
                              chunk_size: int = 500, chunk_overlap: float = 0.2, sliceidentifier: list = None,
                              visiblerange: int = 0, deptidlist: list = None, managedeptidlist: list = None):
        """
        插入知识库基础信息
        """
        return self.insert("ai_knowledge_base", data={
            "knowledge_id": knowledge_id,
            "knowledge_name": knowledge_name,
            "kno_root_id": kno_root_id,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "sliceidentifier": sliceidentifier or [],
            "visiblerange": visiblerange,
            "deptidlist": deptidlist or [],
            "managedeptidlist": managedeptidlist or []
        })

    def knowledge_base_update(self, knowledge_id: str, knowledge_name: str = None, kno_root_id: str = None,
                              chunk_size: int = None, chunk_overlap: float = None, sliceidentifier: list = None,
                              visiblerange: int = None, deptidlist: list = None, managedeptidlist: list = None):
        """
        更新知识库基础信息
        """
        data = {}
        if knowledge_name is not None:
            data["knowledge_name"] = knowledge_name
        if kno_root_id is not None:
            data["kno_root_id"] = kno_root_id
        if chunk_size is not None:
            data["chunk_size"] = chunk_size
        if chunk_overlap is not None:
            data["chunk_overlap"] = chunk_overlap
        if sliceidentifier is not None:
            data["sliceidentifier"] = sliceidentifier
        if visiblerange is not None:
            data["visiblerange"] = visiblerange
        if deptidlist is not None:
            data["deptidlist"] = deptidlist
        if managedeptidlist is not None:
            data["managedeptidlist"] = managedeptidlist

        if not data:
            return False  # 如果没有要更新的数据，返回False

        # 构建更新语句
        set_clauses = []
        param_values = []
        for key, value in data.items():
            set_clauses.append(f"{key} = %s")
            param_values.append(value)

        set_clause = ", ".join(set_clauses)
        query = f"UPDATE ai_knowledge_base SET {set_clause} WHERE knowledge_id = %s"
        params = param_values + [knowledge_id]

        try:
            self.cursor.execute(query, params)
            self.connection.commit()
            # 检查是否有行被更新
            return self.cursor.rowcount > 0
        except Exception as e:
            self.connection.rollback()
            return False

    def knowledge_base_delete(self, knowledge_id: str):
        """
        删除知识库基础信息
        """
        query = "DELETE FROM ai_knowledge_base WHERE knowledge_id = %s"
        params = (knowledge_id,)

        try:
            self.cursor.execute(query, params)
            self.connection.commit()
            # 检查是否有行被删除
            return self.cursor.rowcount > 0
        except Exception as e:
            self.connection.rollback()
            return False

    def get_knowledge_base(self, knowledge_id: str = None, knowledge_name: str = None, order_by: str = None,
                           limit: int = None) -> Optional[List[Tuple]]:
        """
        获取知识库基础信息
        支持按 knowledge_id 精确查询，或按 knowledge_name 模糊查询
        支持排序和限制结果数量
        """
        # 构建查询条件
        where_parts = []
        params = []

        if knowledge_id:
            where_parts.append("knowledge_id = %s")
            params.append(knowledge_id)

        if knowledge_name:
            where_parts.append("knowledge_name ILIKE %s")
            params.append(f"%{knowledge_name}%")

        # 组合查询语句
        query = "SELECT * FROM ai_knowledge_base"

        if where_parts:
            query += " WHERE " + " AND ".join(where_parts)

        if order_by:
            query += f" ORDER BY {order_by}"

        if limit:
            query += " LIMIT %s"
            params.append(limit)

        return self.execute_query(query, tuple(params))


if __name__ == '__main__':
    l_k_c = LocalKnowledgeCrud()
    l_k_c.connect()
    print(l_k_c.get_local_knowledge_detail())
    l_k_c.disconnect()
