from typing import Optional, List, Tuple
from src.sql_funs.sql_base import PostgreSQLManager
import logging

logger = logging.getLogger(__name__)


class LabelStudioCrud(PostgreSQLManager):
    def label_studio_create(self, label_studio_id: str, label_studio_url: str, label_studio_api_key: str):
        """
        创建Label Studio环境
        """
        return self.insert("ai_label_studio_info", data={
            "label_studio_id": label_studio_id,
            "label_studio_url": label_studio_url,
            "label_studio_api_key": label_studio_api_key
        })

    def label_studio_update(self, label_studio_id: str, label_studio_url: str = None, label_studio_api_key: str = None):
        """
        更新Label Studio环境信息
        """
        data = {
            key: value for key, value in locals().items()
            if key not in ['self', 'label_studio_id'] and value is not None
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
        query = f"UPDATE ai_label_studio_info SET {set_clause} WHERE label_studio_id = %s"
        params = param_values + [label_studio_id]

        try:
            self.cursor.execute(query, params)
            self.connection.commit()
            # 检查是否有行被更新
            return self.cursor.rowcount > 0
        except Exception as e:
            self.connection.rollback()
            return False

    def label_studio_delete(self, label_studio_id: str):
        """
        删除Label Studio环境
        """
        query = "DELETE FROM ai_label_studio_info WHERE label_studio_id = %s"
        params = (label_studio_id,)

        try:
            self.cursor.execute(query, params)
            self.connection.commit()
            # 检查是否有行被删除
            return self.cursor.rowcount > 0
        except Exception as e:
            self.connection.rollback()
            return False

    def label_studio_list(self, order_by: str = None, limit: int = None, **kwargs) -> Optional[List[Tuple]]:
        """
        获取Label Studio环境列表
        支持按 label_studio_id 精确查询，或按 label_studio_url 模糊查询
        支持排序和限制结果数量
        """
        exact_match_fields = ['label_studio_id']
        partial_match_fields = ['label_studio_url']
        allowed_fileds = exact_match_fields + partial_match_fields
        query, params = self.gen_select_query('ai_label_studio_info', order_by=order_by, limit=limit,
                                              exact_match_fields=exact_match_fields,
                                              partial_match_fields=partial_match_fields,
                                              allowed_fileds=allowed_fileds, **kwargs)
        return self.execute_query(query, params)

    def _label_studio_to_json(self, label_studio_tuple):
        """
        将Label Studio元组转换为JSON格式
        """
        if label_studio_tuple:
            # 获取项目数量（模拟逻辑，实际中可能需要调用Label Studio API来获取真实的项目数量）
            project_count = self._get_project_count(label_studio_tuple[1], label_studio_tuple[2])  # 使用URL和API密钥
            return {
                "label_studio_id": label_studio_tuple[0],
                "label_studio_url": label_studio_tuple[1],
                "label_studio_api_key": label_studio_tuple[2],
                "project_count": project_count,
                "created_at": label_studio_tuple[3].isoformat() if len(label_studio_tuple) > 3 and label_studio_tuple[3] else None,
                "updated_at": label_studio_tuple[4].isoformat() if len(label_studio_tuple) > 4 and label_studio_tuple[4] else None
            }
        return None

    def _get_project_count(self, label_studio_url: str, api_key: str) -> int:
        """
        获取Label Studio中的项目数量（模拟实现，实际中需要调用Label Studio API）
        """
        # 这里应该调用Label Studio API来获取项目数量
        # 由于当前没有API连接，这里返回一个默认值
        # 实际实现中应连接到Label Studio并获取真实的项目数量
        try:
            # 这里将来会添加实际的API调用逻辑
            # 示例：
            # import requests
            # headers = {'Authorization': f'Token {api_key}'}
            # response = requests.get(f'{label_studio_url}/api/projects', headers=headers)
            # if response.status_code == 200:
            #     projects = response.json()
            #     return len(projects)
            return 0  # 模拟返回0个项目
        except Exception as e:
            logger.error(f"获取Label Studio项目数量时发生错误: {str(e)}")
            return 0

    # 新增ai_label_studio_bind表的CRUD操作方法
    def label_studio_bind_insert(self, kno_id: str, label_studio_id: str, bind_status: int = 0):
        """
        创建本地知识库与Label Studio的绑定关系
        """
        return self.insert("ai_label_studio_bind", data={
            "kno_id": kno_id,
            "label_studio_id": label_studio_id,
            "bind_status": bind_status
        })

    def label_studio_bind_update(self, kno_id: str, label_studio_id: str, bind_status: int = None):
        """
        更新本地知识库与Label Studio的绑定状态
        """
        if bind_status is None:
            return False

        data = {"bind_status": bind_status}
        return self.update("ai_label_studio_bind", data, kno_id=kno_id, label_studio_id=label_studio_id)

    def label_studio_bind_delete(self, kno_id: str, label_studio_id: str):
        """
        删除本地知识库与Label Studio的绑定关系
        """
        return self.delete("ai_label_studio_bind", kno_id=kno_id, label_studio_id=label_studio_id)

    def label_studio_bind_get(self, kno_id: str = None, label_studio_id: str = None, bind_status: int = None) -> Optional[List[Tuple]]:
        """
        获取本地知识库与Label Studio的绑定关系列表
        支持按kno_id、label_studio_id、bind_status查询
        """
        data = {}
        if kno_id is not None:
            data['kno_id'] = kno_id
        if label_studio_id is not None:
            data['label_studio_id'] = label_studio_id
        if bind_status is not None:
            data['bind_status'] = bind_status

        exact_match_fields = ['kno_id', 'label_studio_id', 'bind_status']
        allowed_fileds = exact_match_fields
        
        query, params = self.gen_select_query('ai_label_studio_bind', 
                                              exact_match_fields=exact_match_fields,
                                              allowed_fileds=allowed_fileds, **data)
        return self.execute_query(query, params)



    def _label_studio_bind_to_json(self, bind_tuple):
        """
        将绑定关系元组转换为JSON格式
        """
        if bind_tuple:
            return {
                "id": bind_tuple[0],
                "kno_id": bind_tuple[1],
                "label_studio_id": bind_tuple[2],
                "bind_status": bind_tuple[3],
                "created_at": bind_tuple[4].isoformat() if len(bind_tuple) > 4 and bind_tuple[4] else None,
                "updated_at": bind_tuple[5].isoformat() if len(bind_tuple) > 5 and bind_tuple[5] else None
            }
        return None
