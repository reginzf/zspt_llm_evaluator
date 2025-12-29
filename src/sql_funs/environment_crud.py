import logging
from typing import Optional, List, Tuple

from env_config_init import settings
from src.sql_funs.sql_base import PostgreSQLManager

ALLOWED_FIELDS = {'zlpt_base_id', 'zlpt_name', 'zlpt_base_url', 'domain'}


class Environment_Crud(PostgreSQLManager):
    def environment_list(self, **kwargs) -> Optional[List[Tuple]]:
        """
        获取环境列表
        支持输入多个参数进行select，查询关系是and
        
        ai_environment_info表结构:
        - zlpt_base_id: VARCHAR(100) PRIMARY KEY - ZLPT基础ID
        - zlpt_name: VARCHAR(200) NOT NULL - ZLPT名称
        - zlpt_base_url: VARCHAR(500) NOT NULL - ZLPT基础URL  
        - domain: VARCHAR(100) DEFAULT 'default' - 域名
        使用示例:
        - environment_list()  # 获取所有环境
        - environment_list(zlpt_name="test_env")  # 根据名称部分匹配查询
        - environment_list(domain="production", zlpt_name="prod_env")  # 多条件部分匹配查询
        - environment_list(zlpt_base_id="specific_id")  # 根据ID精确查询
        """
        logging.info(f"查询环境列表，输入参数: {kwargs}")
        if not kwargs:
            logging.info("查询所有环境信息")
            query = "SELECT * FROM ai_environment_info"
            result = self.execute_query(query)
            logging.info(f"查询返回结果数量: {len(result) if result else 0}")
            return result

        exact_match_fields = {'zlpt_base_id'}  # 精确匹配字段
        partial_match_fields = {'zlpt_name', 'zlpt_base_url', 'domain'}  # 部分匹配字段

        query, values = self.gen_select_query('ai_environment_info', exact_match_fields=exact_match_fields,
                                              partial_match_fields=partial_match_fields, allowed_fileds=ALLOWED_FIELDS,
                                              **kwargs)
        result = self.execute_query(query, values)
        logging.info(f"查询返回结果数量: {len(result) if result else 0}")
        return result

    def environment_create(self, **kwargs) -> bool:
        """
        在ai_environment_info中插入环境信息
        获取环境信息，并进行冲突检查
        检查失败则返回错误信息，提示环境信息冲突
        检查成功则返回成功信息，提示环境信息添加成功
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
        在ai_environment_info中删除环境信息
        查询对应环境信息，并删除
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
        在ai_environment_info中更新环境信息
        获取环境信息，检查update的环境是否存在
        不存在直接返回错误信息，提示环境信息不存在
        存在则进行更新，返回执行是否成功
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

        try:
            # 构建更新语句
            set_clause_parts = []
            values = []
            for key, value in kwargs.items():
                # 验证字段名是否合法
                if key not in ALLOWED_FIELDS and key not in ['username', 'password', 'key1', 'key2_add', 'pk']:
                    logging.warning(f"Invalid field name: {key}")
                    continue
                set_clause_parts.append(f"{key} = %s")
                values.append(value)

            if not set_clause_parts:
                logging.error("错误: 没有提供要更新的合法字段")
                return False

            set_clause = ", ".join(set_clause_parts)
            query = f"UPDATE ai_environment_info SET {set_clause} WHERE zlpt_base_id = %s"
            values.append(zlpt_base_id)

            logging.info(f"执行更新语句: {query}，参数: {values}")
            self.cursor.execute(query, values)
            self.connection.commit()

            if self.cursor.rowcount > 0:
                logging.info("成功: 环境信息更新成功")
                return True
            else:
                logging.error("错误: 环境信息更新失败")
                return False
        except Exception as e:
            self.connection.rollback()
            logging.error(f"错误: 更新数据时发生异常: {e}")
            return False


if __name__ == '__main__':
    env = Environment_Crud('10.210.2.223', 5432, 'label_studio', 'labelstudio', 'Labelstudio123')
    env.connect()
    print(env.environment_list())
