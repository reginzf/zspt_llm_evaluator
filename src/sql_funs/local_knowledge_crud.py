from typing import Optional, List, Tuple
from src.sql_funs.sql_base import PostgreSQLManager
import logging
from datetime import datetime

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
                               ls_status: int = 1):
        """
        插入本地知识库信息
        """
        return self.insert("ai_local_knowledge", data={
            "kno_id": kno_id,
            "kno_name": kno_name,
            "kno_describe": kno_describe,
            "kno_path": kno_path,
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

        try:
            result = self.update("ai_local_knowledge", data, kno_id=kno_id)
            return result
        except Exception as e:
            logger.error(f"更新本地知识库信息失败: {e}")
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
            elif current_status in [0, 4]:  # 未绑定、已解绑状态，更新为已绑定
                return self._local_knowledge_bind_update(kno_id, knowledge_id, target_status=2)

        else:
            # 如果记录不存在，插入新记录，初始状态为已绑定
            return self._local_knowledge_bind_insert(kno_id, knowledge_id, bind_status=2)

    def _local_knowledge_unbind(self, kno_id: str, knowledge_id: str):
        # 按kno_id和knowledge_id获取绑定关系
        bind_info = self.get_local_knowledge_bind(kno_id=kno_id, knowledge_id=knowledge_id)
        if bind_info:
            # 如果记录存在，检查当前状态
            current_status = bind_info[0][3]  # bind_status是第4列
            if current_status in [0, 4]:  # 未绑定、绑定中、已解绑状态
                return True
            elif current_status in [1, 2]:  # 绑定中、已绑定状态，更新为解绑中(3)
                return self._local_knowledge_bind_update(kno_id, knowledge_id, target_status=3)
            else:  # 已绑定状态，可以解绑
                # 更新状态为已解绑(4)
                return self._local_knowledge_bind_update(kno_id, knowledge_id, target_status=4)
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

        try:
            result = self.update("ai_local_knowledge_list", data, knol_id=knol_id)
            return result
        except Exception as e:
            logger.error(f"更新本地知识库列表信息失败: {e}")
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

    def get_local_knowledge_file_list(self, order_by: str = None, limit: int = None, **kwargs) -> Optional[List[Tuple]]:
        """
        获取本地知识库列表信息
        支持按 knol_id 精确查询，或按 knol_name 模糊查询
        支持排序和限制结果数量
        """

        exact_match_fields = ('knol_id', 'knol_path', 'ls_status', 'kno_id')
        partial_match_fields = ('knol_name', 'knol_describe')
        allowed_fileds = exact_match_fields + partial_match_fields
        query, params = self.gen_select_query('ai_local_knowledge_list', order_by=order_by, limit=limit,
                                              exact_match_fields=exact_match_fields,
                                              partial_match_fields=partial_match_fields,
                                              allowed_fileds=allowed_fileds, **kwargs)
        return self.execute_query(query, params)


    def get_local_knowledge_with_bindings(self, kno_id):
        """
        获取本地知识库及其绑定信息
        :param kno_id: 本地知识库ID
        :return: 包含绑定信息的综合信息
        """
        query_params = {'kno_id': kno_id}
        exact_match_fields = ['kno_id']
        partial_match_fields = []
        allowed_fileds = exact_match_fields + partial_match_fields
        
        query, params = self.gen_select_query('ai_local_knowledge_comprehensive_view', 
                                            exact_match_fields=exact_match_fields,
                                            partial_match_fields=partial_match_fields,
                                            allowed_fileds=allowed_fileds, 
                                            **query_params)
        
        try:
            return self.execute_query(query, params)
        except Exception as e:
            logger.error(f"查询本地知识库及其绑定信息时发生错误: {e}")
            raise e


    # 为 ai_local_knowledge_file_upload 表添加 CRUD 方法
    def local_knowledge_file_upload_insert(self, knol_id: str, knowledge_base_id: str, upload_status: int = 1, upload_time=None):
        """
        插入本地知识库文件上传记录
        :param knol_id: 本地知识库文件ID
        :param knowledge_base_id: 知识库ID
        :param upload_status: 上传状态 (0-已上传, 1-未上传, 2-上传中)
        :param upload_time: 上传时间
        :return: 成功返回True，失败返回False
        """
        from datetime import datetime
        
        data = {
            "knol_id": knol_id,
            "knowledge_base_id": knowledge_base_id,
            "upload_status": upload_status
        }
        
        if upload_time is None:
            upload_time = datetime.now()
        data["upload_time"] = upload_time
        
        return self.insert("ai_local_knowledge_file_upload", data=data)

    def local_knowledge_file_upload_update(self, knol_id: str, knowledge_base_id: str, upload_status: int = None, upload_time=None):
        """
        更新本地知识库文件上传记录
        :param knol_id: 本地知识库文件ID
        :param knowledge_base_id: 知识库ID
        :param upload_status: 上传状态 (0-已上传, 1-未上传, 2-上传中)
        :param upload_time: 上传时间
        :return: 成功返回True，失败返回False
        """
        data = {}
        if upload_status is not None:
            data["upload_status"] = upload_status
        if upload_time is None and upload_status is not None:  # 如果upload_time为None但upload_status不是None（即状态发生变化），则更新时间为当前时间
            data["upload_time"] = datetime.now()
        elif upload_time is not None:
            data["upload_time"] = upload_time
        
        if not data:
            return False
        
        try:
            result = self.update("ai_local_knowledge_file_upload", data, knol_id=knol_id, knowledge_base_id=knowledge_base_id)
            return result
        except Exception as e:
            logger.error(f"更新本地知识库文件上传记录失败: {e}")
            return False

    def local_knowledge_file_upload_delete(self, knol_id: str, knowledge_base_id: str):
        """
        删除本地知识库文件上传记录
        :param knol_id: 本地知识库文件ID
        :param knowledge_base_id: 知识库ID
        :return: 成功返回True，失败返回False
        """
        try:
            result = self.delete("ai_local_knowledge_file_upload", knol_id=knol_id, knowledge_base_id=knowledge_base_id)
            return result
        except Exception as e:
            logger.error(f"删除本地知识库文件上传记录失败: {e}")
            return False

    def get_local_knowledge_file_upload(self, order_by: str = None, limit: int = None, **kwargs) -> Optional[List[Tuple]]:
        """
        获取本地知识库文件上传记录
        支持按 knol_id、knowledge_base_id、upload_status 等字段查询
        支持排序和限制结果数量
        """
        exact_match_fields = ['knol_id', 'knowledge_base_id', 'upload_status']
        partial_match_fields = []
        allowed_fileds = ['knol_id', 'knowledge_base_id', 'upload_status', 'upload_time', 'created_at', 'updated_at']
        query, params = self.gen_select_query('ai_local_knowledge_file_upload', 
                                              order_by=order_by, 
                                              limit=limit,
                                              exact_match_fields=exact_match_fields,
                                              partial_match_fields=partial_match_fields,
                                              allowed_fileds=allowed_fileds, 
                                              **kwargs)
        
        logger.info(f"执行查询: {query}")
        return self.execute_query(query, params)

    def _local_knowledge_file_upload_to_json(self, upload_record: Tuple):
        """
        将本地知识库文件上传记录转换为JSON格式
        :param upload_record: 数据库记录元组
        :return: JSON格式的字典
        """
        if upload_record is not None:
            return {
                "id": upload_record[0],
                "knol_id": upload_record[1],
                "knowledge_base_id": upload_record[2],
                "upload_status": upload_record[3],
                "upload_time": upload_record[4].isoformat() if upload_record[4] and hasattr(upload_record[4], 'isoformat') else None,
                "created_at": upload_record[5].isoformat() if upload_record[5] and hasattr(upload_record[5], 'isoformat') else None,
                "updated_at": upload_record[6].isoformat() if upload_record[6] and hasattr(upload_record[6], 'isoformat') else None
            }
        return None


if __name__ == '__main__':
    l_k_c = LocalKnowledgeCrud()
    l_k_c.connect()

    l_k_c.disconnect()