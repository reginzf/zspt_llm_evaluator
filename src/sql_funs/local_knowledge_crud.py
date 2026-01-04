from typing import Optional, List, Tuple
from src.sql_funs.sql_base import PostgreSQLManager
import logging

logger = logging.getLogger(__name__)
BIND_STATUS_MAP = {
    0: "未绑定",
    1: "绑定中",
    2: "已绑定",
    3: "解绑中",
    4: "已解绑"
}


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
        data = {
            key: value for key, value in locals().items()
            if key not in ['self', 'kno_id', 'knol_id'] and value is not None
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

    def local_knowledge_bind_func(self, kno_id: str, knowledge_id: str, action=None, target_status=None):
        # 0-未绑定, 1-绑定中, 2-已绑定, 3-解绑中, 4-已解绑
        if action == "bind":
            return self._local_knowledge_bind(kno_id, knowledge_id)
        elif action == "unbind":
            return self._local_knowledge_unbind(kno_id, knowledge_id)
        elif action == "update":
            return self._local_knowledge_bind_update(kno_id, knowledge_id, target_status)
        else:
            return False

    def get_local_knowledge_bind(self, order_by: str = None, limit: int = None, **kwargs) -> Optional[List[Tuple]]:
        exact_match_fields = ['kno_id', 'knowledge_id', 'bind_status']
        partial_match_fields = []
        allowed_fileds = exact_match_fields + partial_match_fields
        query, params = self.gen_select_query('ai_knowledge_bind', order_by=order_by, limit=limit,
                                              exact_match_fields=exact_match_fields,
                                              partial_match_fields=partial_match_fields,
                                              allowed_fileds=allowed_fileds, **kwargs)
        logger.info(f"执行查询: {query}")
        return self.execute_query(query, params)

    def _local_knowledge_bind_to_json(self, kno_bind: Tuple):
        if kno_bind is not None:
            return {
                "id": kno_bind[0],
                "kno_id": kno_bind[1],
                "knowledge_id": kno_bind[2],
                "bind_status": kno_bind[3],
                "created_at": kno_bind[4].isoformat() if kno_bind[4] else None,
                "updated_at": kno_bind[5].isoformat() if kno_bind[5] else None
            }
        return None

    def _local_knowledge_bind_insert(self, kno_id: str, knowledge_id: str, bind_status: int = 0):
        """
        插入知识库绑定关系
        :param kno_id: 本地知识库ID
        :param knowledge_id: 知识库ID
        :param bind_status: 绑定状态 (0-未绑定, 1-绑定中, 2-已绑定, 3-解绑中, 4-已解绑)
        """
        if bind_status not in [0, 1, 2, 3, 4]:
            logger.error(f"无效的绑定状态: {bind_status}")
            return False

        # 检查是否已存在相同的kno_id和knowledge_id组合
        existing_bind = self.get_local_knowledge_bind(kno_id=kno_id, knowledge_id=knowledge_id)
        if existing_bind:
            logger.warning(f"绑定关系已存在: kno_id={kno_id}, knowledge_id={knowledge_id}")
            return False

        return self.insert("ai_knowledge_bind", data={
            "kno_id": kno_id,
            "knowledge_id": knowledge_id,
            "bind_status": bind_status
        })

    def _local_knowledge_bind(self, kno_id: str, knowledge_id: str):
        # 按kno_id和knowledge_id查找绑定关系，如果存在且绑定关系为1、2、3则返回错误
        bind_info = self.get_local_knowledge_bind(kno_id=kno_id, knowledge_id=knowledge_id)
        if bind_info:
            # 如果记录存在，检查当前状态
            current_status = bind_info[0][3]  # bind_status是第4列
            if current_status in [1, 2, 3]:  # 绑定中、已绑定、解绑中
                logger.error(f"当前状态为{BIND_STATUS_MAP[current_status]}，不能重复绑定")
                return False  # 不能重复绑定
            elif current_status in [0, 4]:  # 未绑定、已解绑状态，可以更新为绑定中
                return self._local_knowledge_bind_update(kno_id, knowledge_id, target_status=1)

        else:
            # 如果记录不存在，插入新记录，初始状态为绑定中(1)
            return self._local_knowledge_bind_insert(kno_id, knowledge_id, bind_status=1)

    def _local_knowledge_unbind(self, kno_id: str, knowledge_id: str):
        # 按kno_id和knowledge_id获取绑定关系
        bind_info = self.get_local_knowledge_bind(kno_id=kno_id, knowledge_id=knowledge_id)
        if bind_info:
            # 如果记录存在，检查当前状态
            current_status = bind_info[0][3]  # bind_status是第4列
            if current_status in [0, 1, 3, 4]:  # 未绑定、绑定中、解绑中、已解绑状态
                # 如果是已解绑(4)则不需要再解绑，直接返回True
                if current_status == 4:
                    return True
                # 如果是其他状态，更新为解绑中(3)，然后到已解绑(4)
                self._local_knowledge_bind_update(kno_id, knowledge_id, target_status=3)
            elif current_status == 2:  # 已绑定状态，可以解绑
                # 更新状态为已解绑(4)
                self._local_knowledge_bind_update(kno_id, knowledge_id, target_status=4)
        else:
            # 如果记录不存在，插入新记录并设置为已解绑状态
            logger.error(f"绑定信息不存在: kno_id={kno_id}, knowledge_id={knowledge_id}")
            return False

    def _local_knowledge_bind_update(self, kno_id: str, knowledge_id: str, target_status: int):
        if target_status not in [0, 1, 2, 3, 4]:
            logger.error(f"无效的目标状态: {target_status}")
            return False
        query = "UPDATE ai_knowledge_bind SET bind_status = %s, updated_at = CURRENT_TIMESTAMP WHERE kno_id = %s AND knowledge_id = %s"
        params = (target_status, kno_id, knowledge_id)
        logger.info(f"更新绑定状态: {query} {params}")
        res = self.execute_query(query, params)
        if res is False:
            logger.error(f"更新绑定状态失败")
            return
        return res

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
        data = {
            key: value for key, value in locals().items()
            if key not in ['self', 'knol_id'] and value is not None
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

    def get_local_knowledge_list(self, order_by: str = None, limit: int = None, **kwargs) -> Optional[List[Tuple]]:
        """
        获取本地知识库列表信息
        支持按 knol_id 精确查询，或按 knol_name 模糊查询
        支持排序和限制结果数量
        """

        exact_match_fields = ('knol_id', 'knol_path', 'ls_status')
        partial_match_fields = ('knol_name', 'knol_describe')
        allowed_fileds = exact_match_fields + partial_match_fields
        query, params = self.gen_select_query('ai_local_knowledge_list', order_by=order_by, limit=limit,
                                              exact_match_fields=exact_match_fields,
                                              partial_match_fields=partial_match_fields,
                                              allowed_fileds=allowed_fileds, **kwargs)
        return self.execute_query(query, params)


if __name__ == '__main__':
    l_k_c = LocalKnowledgeCrud()
    l_k_c.connect()

    l_k_c.disconnect()
