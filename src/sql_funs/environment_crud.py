# -*- coding: utf-8 -*-
"""
环境管理CRUD操作模块

此模块提供了环境和知识库管理的完整CRUD操作接口，
包括环境信息的增删改查以及知识库基础信息的操作。
"""
from typing import Optional, List, Tuple
import logging
from env_config_init import settings
from src.sql_funs.sql_base import PostgreSQLManager

logger = logging.getLogger(__name__)

# 定义允许的字段集合，用于防止非法字段操作
ALLOWED_FIELDS = {'zlpt_base_id', 'zlpt_name', 'project_name', 'project_id', 'zlpt_base_url', 'domain'}


class Environment_Crud(PostgreSQLManager):
    """
    环境管理CRUD操作类
    
    继承自PostgreSQLManager，提供针对环境信息和知识库基础信息的
    数据库操作方法。支持环境的增删改查以及知识库的基础操作。
    """
    
    def environment_list(self, **kwargs) -> Optional[List[Tuple]]:
        """
        获取环境列表
        
        支持根据传入的参数进行条件查询，查询关系为AND连接。
        可以按环境名称部分匹配或按ID精确匹配等方式查询。
        
        ai_environment_info表结构:
        - zlpt_base_id: VARCHAR(100) PRIMARY KEY - ZLPT基础ID
        - zlpt_name: VARCHAR(200) NOT NULL - ZLPT名称
        - zlpt_base_url: VARCHAR(500) NOT NULL - ZLPT基础URL  
        - domain: VARCHAR(100) DEFAULT 'default' - 域名
        
        Args:
            **kwargs: 查询条件关键字参数
                - zlpt_base_id: 按ID精确查询
                - zlpt_name: 按名称部分匹配查询
                - zlpt_base_url: 按URL部分匹配查询
                - domain: 按域名部分匹配查询
        
        Returns:
            Optional[List[Tuple]]: 查询结果列表，每个元素为元组形式的记录
            
        Examples:
            - environment_list()  # 获取所有环境
            - environment_list(zlpt_name="test_env")  # 根据名称部分匹配查询
            - environment_list(domain="production", zlpt_name="prod_env")  # 多条件部分匹配查询
            - environment_list(zlpt_base_id="specific_id")  # 根据ID精确查询
        """
        logging.info(f"查询环境列表，输入参数：{kwargs}")
        if not kwargs:
            logging.info("查询所有环境信息")
            query = "SELECT * FROM ai_environment_info"
            result = self.execute_query(query)
            # 检查结果类型，防止返回 False 导致类型错误
            if result is False:
                logging.error("查询执行失败")
                return []
            logging.info(f"查询返回结果数量：{len(result) if result else 0}")
            return result
        
        exact_match_fields = {'zlpt_base_id'}  # 精确匹配字段
        partial_match_fields = {'zlpt_name', 'zlpt_base_url', 'domain'}  # 部分匹配字段
        
        query, values = self.gen_select_query('ai_environment_info', exact_match_fields=exact_match_fields,
                                              partial_match_fields=partial_match_fields, allowed_fileds=ALLOWED_FIELDS,
                                              **kwargs)
        result = self.execute_query(query, values)
        # 检查结果类型，防止返回 False 导致类型错误
        if result is False:
            logging.error("查询执行失败")
            return []
        logging.info(f"查询返回结果数量：{len(result) if result else 0}")
        return result

    def _environment_list_to_json(self, environment: Tuple):
        """
        将环境信息元组转换为JSON格式
        
        将数据库查询返回的元组格式环境信息转换为字典格式，
        便于前端展示和数据处理。
        
        Args:
            environment (Tuple): 数据库查询返回的环境信息元组
            
        Returns:
            dict or None: 转换后的环境信息字典，如果输入为None则返回None
        """
        if environment is not None:
            return {
                "zlpt_base_id": environment[0],
                "zlpt_name": environment[1],
                "zlpt_base_url": environment[2],
                "key1": environment[3],
                "key2_add": environment[4],
                "pk": environment[5],
                "username": environment[6],
                "password": environment[7],
                "domain": environment[8],
                "created_at": environment[9],
                "updated_at": environment[10],
                "project_name": environment[11] if len(environment) > 11 else "",
                "project_id": environment[12] if len(environment) > 12 else ""
            }
        return None

    def environment_create(self, **kwargs) -> bool:
        """
        创建新环境信息
        
        在ai_environment_info表中插入新的环境信息记录，
        包括冲突检查、默认值填充和数据验证。
        
        Args:
            **kwargs: 环境信息参数
                - zlpt_base_id: ZLPT基础ID（必填）
                - zlpt_name: ZLPT名称（必填）
                - project_name: 项目名称（可选）
                - project_id: 项目ID（可选）
                - zlpt_base_url: ZLPT基础URL（必填）
                - username: 用户名（必填）
                - password: 密码（必填）
                - key1: 密钥1（可选，默认从配置获取）
                - key2_add: 密钥2（可选，默认从配置获取）
                - pk: 公钥（可选，默认从配置获取）
                - domain: 域名（可选）
        
        Returns:
            bool: 创建成功返回True，失败返回False
        """
        logging.info(f"创建环境，输入参数: {kwargs}")
        # 检查是否提供了必要的参数
        required_fields = ['zlpt_base_id', 'zlpt_name', 'zlpt_base_url', 'username', 'password']
        for field in required_fields:
            if field not in kwargs:
                logging.error(f"错误: 缺少必要字段 {field}")
                return False

        # 检查zlpt_base_id是否已存在
        logging.info(f"检查zlpt_base_id {kwargs['zlpt_base_id']} 是否已存在")
        existing_env = self.environment_list(zlpt_base_id=kwargs['zlpt_base_id'])
        if existing_env:
            logging.error("错误: 环境信息冲突，zlpt_base_id已存在")
            return False

        # 自动填充key1、key2_add、pk字段的默认值
        if 'key1' not in kwargs:
            kwargs['key1'] = settings.KEY1
        if 'key2_add' not in kwargs:
            kwargs['key2_add'] = settings.KEY2_ADD
        if 'pk' not in kwargs:
            kwargs['pk'] = settings.PK

        # 如果没有提供项目名称，基于环境名称生成默认值
        if 'project_name' not in kwargs or not kwargs['project_name']:
            env_name = kwargs['zlpt_name']
            if '生产' in env_name or 'prod' in env_name.lower():
                kwargs['project_name'] = '生产项目'
            elif '测试' in env_name or 'test' in env_name.lower():
                kwargs['project_name'] = '测试项目'
            elif '开发' in env_name or 'dev' in env_name.lower():
                kwargs['project_name'] = '开发项目'
            else:
                kwargs['project_name'] = f'项目_{env_name}'

        # 如果没有提供项目ID，基于环境ID生成
        if 'project_id' not in kwargs or not kwargs['project_id']:
            kwargs['project_id'] = f"proj_{kwargs['zlpt_base_id'].replace('env_', '')}"

        # 执行插入操作
        try:
            logging.info(f"准备插入环境信息: {kwargs}")
            result = self.insert('ai_environment_info', kwargs)
            if result:
                logging.info("成功: 环境信息添加成功")
            else:
                logging.error("错误: 环境信息添加失败")
            return result
        except Exception as e:
            logging.error(f"错误: 插入数据时发生异常: {e}")
            return False

    def environment_delete(self, **kwargs) -> bool:
        """
        删除环境信息
        
        根据传入的条件从ai_environment_info表中删除环境信息记录。
        包括参数验证、存在性检查和删除操作。
        
        Args:
            **kwargs: 删除条件参数
                - zlpt_base_id: 按ID删除
                - zlpt_name: 按名称删除
                - domain: 按域名删除
        
        Returns:
            bool: 删除成功返回True，失败返回False
        """
        logging.info(f"删除环境，输入参数: {kwargs}")
        # 检查是否提供了删除条件
        if not kwargs:
            logging.error("错误: 请提供删除条件")
            return False

        # 验证字段名是否合法
        for key in kwargs.keys():
            if key not in ALLOWED_FIELDS:
                logging.error(f"错误: 无效的字段名 {key}")
                return False

        # 先查询是否存在匹配的记录
        logging.info(f"查询是否存在匹配的记录: {kwargs}")
        logging.info(f"查询条件: {kwargs}")
        existing_env = self.environment_list(**kwargs)
        if not existing_env:
            logging.error("错误: 未找到匹配的环境信息")
            return False

        try:
            # 构建删除条件
            conditions = []
            values = []
            for key, value in kwargs.items():
                conditions.append(f"{key} = %s")
                values.append(value)
            where_clause = " AND ".join(conditions)

            query = f"DELETE FROM ai_environment_info WHERE {where_clause}"
            logging.info(f"执行删除语句: {query}，参数: {values}")
            self.cursor.execute(query, values)
            self.connection.commit()
            logging.info(f"成功: 删除了 {self.cursor.rowcount} 条环境信息")
            return True
        except Exception as e:
            self.connection.rollback()
            logging.error(f"错误: 删除数据时发生异常: {e}")
            return False

    def environment_update(self, zlpt_base_id: str, **kwargs) -> bool:
        """
        更新环境信息
        
        根据zlpt_base_id更新ai_environment_info表中的环境信息记录。
        包括存在性检查、参数验证和更新操作。
        
        Args:
            zlpt_base_id (str): 要更新的环境ID
            **kwargs: 要更新的环境信息参数
                - zlpt_name: ZLPT名称
                - zlpt_base_url: ZLPT基础URL
                - domain: 域名
                - username: 用户名
                - password: 密码
                - key1: 密钥1
                - key2_add: 密钥2
                - pk: 公钥
        
        Returns:
            bool: 更新成功返回True，失败返回False
        """
        logging.info(f"更新环境，zlpt_base_id: {zlpt_base_id}，更新参数: {kwargs}")
        # 检查是否提供了更新条件
        if not zlpt_base_id:
            logging.error("错误: 请提供zlpt_base_id作为更新条件")
            return False

        # 检查要更新的记录是否存在
        logging.info(f"检查要更新的记录是否存在，zlpt_base_id: {zlpt_base_id}")
        existing_env = self.environment_list(zlpt_base_id=zlpt_base_id)
        if not existing_env:
            logging.error("错误: 环境信息不存在")
            return False

        # 确保不更新主键
        if 'zlpt_base_id' in kwargs:
            logging.error("错误: 不能更新zlpt_base_id字段")
            return False

        # 验证字段名是否合法
        validated_updates = {}
        for key, value in kwargs.items():
            if key not in ALLOWED_FIELDS and key not in ['username', 'password', 'key1', 'key2_add', 'pk']:
                logging.warning(f"Invalid field name: {key}")
                continue
            validated_updates[key] = value

        if not validated_updates:
            logging.error("错误: 没有提供要更新的合法字段")
            return False

        try:
            result = self.update("ai_environment_info", validated_updates, zlpt_base_id=zlpt_base_id)
            if result:
                logging.info("成功: 环境信息更新成功")
            else:
                logging.error("错误: 环境信息更新失败")
            return result
        except Exception as e:
            logging.error(f"错误: 更新数据时发生异常: {e}")
            return False

    # 为 ai_knowledge_base 表添加 CRUD 方法
    def knowledge_base_insert(self, knowledge_id: str, knowledge_name: str, kno_root_id: str = None,
                              chunk_size: int = 500, chunk_overlap: float = 0.2, sliceidentifier: list = None,
                              visiblerange: int = 0, deptidlist: list = None, managedeptidlist: list = None,
                              zlpt_base_id: str = None):
        """
        插入知识库基础信息
        
        在ai_knowledge_base表中插入新的知识库基础信息记录。
        
        Args:
            knowledge_id (str): 知识库ID
            knowledge_name (str): 知识库名称
            kno_root_id (str, optional): 知识库根节点ID
            chunk_size (int): 分块大小，默认为500
            chunk_overlap (float): 分块重叠比例，默认为0.2
            sliceidentifier (list, optional): 切片标识符列表
            visiblerange (int): 可见范围，默认为0
            deptidlist (list, optional): 部门ID列表
            managedeptidlist (list, optional): 管理部门ID列表
            zlpt_base_id (str, optional): ZLPT基础ID
        
        Returns:
            bool: 插入成功返回True，失败返回False
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
            "managedeptidlist": managedeptidlist or [],
            "zlpt_id": zlpt_base_id  # 修正字段名
        })

    def knowledge_base_update(self, knowledge_id: str, knowledge_name: str = None, kno_root_id: str = None,
                              chunk_size: int = None, chunk_overlap: float = None, sliceidentifier: list = None,
                              visiblerange: int = None, deptidlist: list = None, managedeptidlist: list = None,
                              zlpt_base_id: str = None):
        """
        更新知识库基础信息
        
        根据知识库ID更新ai_knowledge_base表中的知识库基础信息记录。
        
        Args:
            knowledge_id (str): 要更新的知识库ID
            knowledge_name (str, optional): 新的知识库名称
            kno_root_id (str, optional): 新的知识库根节点ID
            chunk_size (int, optional): 新的分块大小
            chunk_overlap (float, optional): 新的分块重叠比例
            sliceidentifier (list, optional): 新的切片标识符列表
            visiblerange (int, optional): 新的可见范围
            deptidlist (list, optional): 新的部门ID列表
            managedeptidlist (list, optional): 新的管理部门ID列表
            zlpt_base_id (str, optional): 新的ZLPT基础ID
        
        Returns:
            bool: 更新成功返回True，失败返回False
        """
        data = {
            key: value for key, value in locals().items()
            if key not in ['self', 'knowledge_id'] and value is not None
        }

        if not data:
            return False

        try:
            result = self.update("ai_knowledge_base", data, knowledge_id=knowledge_id)
            return result
        except Exception as e:
            # 记录错误以便调试
            print(f"更新知识库基础信息失败: {e}")
            return False

    def knowledge_base_delete(self, knowledge_id: str):
        """
        删除知识库基础信息
        
        根据知识库ID从ai_knowledge_base表中删除知识库基础信息记录。
        
        Args:
            knowledge_id (str): 要删除的知识库ID
        
        Returns:
            bool: 删除成功返回True，失败返回False
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
            raise e
            return False

    def get_knowledge_base(self, order_by: str = None, limit: int = None, **kwargs) -> Optional[List[Tuple]]:
        """
        获取知识库基础信息
        
        从ai_knowledge_base表中查询知识库基础信息，支持多种查询条件、
        排序和结果数量限制。
        
        Args:
            order_by (str, optional): 排序字段
            limit (int, optional): 限制返回结果数量
            **kwargs: 查询条件关键字参数
                - knowledge_id: 按ID精确查询
                - knowledge_name: 按名称部分匹配查询
                - chunk_size: 按分块大小精确查询
                - chunk_overlap: 按分块重叠比例精确查询
                - kno_root_id: 按根节点ID精确查询
                - zlpt_id: 按ZLPT ID精确查询
                - sliceidentifier: 按切片标识符部分匹配查询
        
        Returns:
            Optional[List[Tuple]]: 查询结果列表，每个元素为元组形式的记录
        """
        exact_match_fields = ('knowledge_id', 'chunk_size', 'chunk_overlap', 'kno_root_id', 'zlpt_id')
        partial_match_fields = ('knowledge_name', 'sliceidentifier')
        allowed_fileds = exact_match_fields + partial_match_fields
        query, params = self.gen_select_query('ai_knowledge_base', order_by=order_by, limit=limit,
                                              exact_match_fields=exact_match_fields,
                                              partial_match_fields=partial_match_fields,
                                              allowed_fileds=allowed_fileds, **kwargs)
        return self.execute_query(query, params)

    def _knowledge_base_to_json(self, kb):
        """
        将知识库基础信息元组转换为JSON格式
        
        将数据库查询返回的元组格式知识库信息转换为字典格式，
        便于前端展示和数据处理，并进行适当的数据类型转换。
        
        Args:
            kb (Tuple): 数据库查询返回的知识库信息元组
            
        Returns:
            dict or None: 转换后的知识库信息字典，如果输入为None则返回None
        """
        if kb is not None:
            return {
                "knowledge_id": kb[0],
                "knowledge_name": kb[1],
                "kno_root_id": kb[2],
                "chunk_size": int(kb[3]) if kb[3] is not None else None,  # 转换为int
                "chunk_overlap": float(kb[4]) if kb[4] is not None else None,  # 转换为float
                "sliceidentifier": kb[5],
                "visiblerange": int(kb[6]) if kb[6] is not None else None,  # 转换为int
                "deptidlist": kb[7],
                "managedeptidlist": kb[8],
                "created_at": str(kb[9]) if kb[9] is not None else None,  # 转换为字符串
                "updated_at": str(kb[10]) if kb[10] is not None else None,  # 转换为字符串
                "zlpt_base_id": kb[11],
            }
        return None


if __name__ == '__main__':
    env = Environment_Crud('10.210.2.223', 5432, 'label_studio', 'labelstudio', 'Labelstudio123')
    env.connect()
    print(env.environment_list())