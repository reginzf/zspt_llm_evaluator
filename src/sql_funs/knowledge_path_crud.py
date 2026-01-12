from typing import Optional, List, Tuple
import json
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

        try:
            result = self.update("ai_knowledge_path", data, kno_path_id=kno_path_id)
            return result
        except Exception as e:
            # 记录错误以便调试
            print(f"更新知识库路径失败: {e}")
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
            if parent_id:
                # 如果有父节点，添加到父节点的子节点列表中
                if 'children' not in path_map[parent_id]:
                    path_map[parent_id]['children'] = []
                path_map[parent_id]['children'].append(path)
            else:
                # 如果没有父节点，添加到根节点列表
                tree.append(path)
        return tree

    def knowledge_path_insert_by_tree(self, tree_data: List[dict], knowledge_id: str, parent_id: str = None) -> bool:
        """
        根据树形结构数据批量插入知识库目录
        :param tree_data: 树形结构数据，格式如generate_content_tree的返回值
        :param knowledge_id: 知识库ID
        :param parent_id: 父节点ID，根节点为None
        :return: 插入是否成功
        """
        all_success = True

        for item in tree_data:
            # 提取节点信息
            content_code = item.get('contentCode')  # 对应kno_path_id
            content_name = item.get('contentName')  # 对应kno_path_name
            pcontent_code = item.get('pcontentCode')  # 对应parent
            children = item.get('children', [])

            # 如果pcontent_code为null，使用传入的parent_id
            actual_parent = pcontent_code if pcontent_code is not None else parent_id

            # 准备doc_map数据
            doc_map = {
                'psort': item.get('psort'),
                'plevel': item.get('plevel'),
                'id': item.get('id'),
                'knowledgeId': item.get('knowledgeId')
            }

            # 插入当前节点
            try:
                insert_result = self.knowledge_path_insert(
                    kno_path_id=content_code,
                    kno_path_name=content_name,
                    knowledge_id=knowledge_id,
                    parent=actual_parent,
                    doc_map=doc_map
                )

                if insert_result:
                    # 递归插入子节点
                    if children:
                        child_success = self.knowledge_path_insert_by_tree(
                            children,
                            knowledge_id,
                            content_code  # 当前节点作为子节点的父节点
                        )
                        if not child_success:
                            all_success = False
                else:
                    all_success = False
            except Exception as e:
                # 如果插入失败，记录错误并标记失败
                print(f"插入知识库路径失败: {e}")
                all_success = False
                continue

        return all_success
