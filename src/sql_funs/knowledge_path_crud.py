from typing import Optional, List, Tuple
from src.sql_funs.sql_base import PostgreSQLManager


class KnowledgePathCrud(PostgreSQLManager):
    def knowledge_path_insert(self, kno_path_id: str, kno_path_name: str, knowledge_id: str, 
                             parent: str = None, doc_map: dict = None):
        """
        插入知识库目录信息
        """
        doc_map = doc_map or {}
        return self.insert("ai_knowledge_path", data={
            "kno_path_id": kno_path_id,
            "kno_path_name": kno_path_name,
            "knowledge_id": knowledge_id,
            "parent": parent,
            "doc_map": doc_map
        })

    def knowledge_path_update(self, kno_path_id: str, kno_path_name: str = None, parent: str = None, 
                             doc_map: dict = None):
        """
        更新知识库目录信息
        """
        data = {
            key: value for key, value in locals().items()
            if key not in ['self', 'kno_path_id'] and value is not None
        }
        if not data:
            return False

        # 构建更新语句
        set_clauses = []
        param_values = []
        for key, value in data.items():
            set_clauses.append(f"{key} = %s")
            param_values.append(value)

        set_clause = ", ".join(set_clauses)
        query = f"UPDATE ai_knowledge_path SET {set_clause} WHERE kno_path_id = %s"
        params = param_values + [kno_path_id]

        try:
            self.cursor.execute(query, params)
            self.connection.commit()
            # 检查是否有行被更新
            return self.cursor.rowcount > 0
        except Exception as e:
            self.connection.rollback()
            return False

    def knowledge_path_delete(self, kno_path_id: str):
        """
        删除知识库目录信息
        """
        query = "DELETE FROM ai_knowledge_path WHERE kno_path_id = %s"
        params = (kno_path_id,)

        try:
            self.cursor.execute(query, params)
            self.connection.commit()
            # 检查是否有行被删除
            return self.cursor.rowcount > 0
        except Exception as e:
            self.connection.rollback()
            return False

    def get_knowledge_path_list(self, order_by: str = None, limit: int = None, **kwargs) -> Optional[List[Tuple]]:
        """
        获取知识库目录列表
        支持按 kno_path_id 精确查询，或按 kno_path_name 模糊查询
        支持排序和限制结果数量
        """
        exact_match_fields = ['kno_path_id', 'knowledge_id', 'parent']
        partial_match_fields = ['kno_path_name']
        allowed_fileds = exact_match_fields + partial_match_fields
        query, params = self.gen_select_query('ai_knowledge_path', order_by=order_by, limit=limit,
                                              exact_match_fields=exact_match_fields,
                                              partial_match_fields=partial_match_fields,
                                              allowed_fileds=allowed_fileds, **kwargs)
        return self.execute_query(query, params)

    def generate_knowledge_path_tree(self, knowledge_id: str) -> List[dict]:
        """
        根据knowledge_id生成知识库目录树
        """
        # 首先获取所有相关目录项
        all_paths = self.get_knowledge_path_list(knowledge_id=knowledge_id)
        
        if not all_paths:
            return []
        
        # 将结果转换为字典格式
        path_dict_list = []
        for path_row in all_paths:
            path_dict = {
                'kno_path_id': path_row[0],
                'kno_path_name': path_row[1],
                'knowledge_id': path_row[2],
                'parent': path_row[3],
                'doc_map': path_row[4],
                'created_at': path_row[5],
                'updated_at': path_row[6]
            }
            path_dict_list.append(path_dict)
        
        # 构建树形结构
        path_map = {path['kno_path_id']: path for path in path_dict_list}
        tree = []
        
        for path in path_dict_list:
            parent_id = path['parent']
            if parent_id and parent_id in path_map:
                # 如果有父节点，添加到父节点的子节点列表中
                if 'children' not in path_map[parent_id]:
                    path_map[parent_id]['children'] = []
                path_map[parent_id]['children'].append(path)
            else:
                # 如果没有父节点，添加到根节点列表
                tree.append(path)
        
        return tree