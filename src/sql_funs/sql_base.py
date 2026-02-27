# -*- coding: utf-8 -*-
"""
PostgreSQL 数据库管理模块

此模块提供了完整的 PostgreSQL 数据库操作封装，包括连接管理、
CRUD 操作、查询构建等功能。采用单例模式确保每个主机上的每个子类
只有一个实例，避免重复连接数据库。
"""
import psycopg2
from psycopg2 import sql
from typing import Optional, List, Tuple, Dict, Any, Union
import json
import logging

from env_config_init import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PostgreSQLManager:
    """
    PostgreSQL 数据库管理类
    
    提供完整的数据库操作接口，包括连接管理、数据查询、插入、更新、删除等操作。
    通过单例模式确保每个主机上每种类别的数据库连接只有一个实例。
    
    Attributes:
        host (str): 数据库主机地址
        port (int): 数据库端口号
        database (str): 数据库名称
        user (str): 数据库用户名
        password (str): 数据库密码
        connection: 数据库连接对象
        cursor: 数据库游标对象
    """

    # 存储不同类和主机的实例
    _instances = {}

    def __new__(cls, host: str = "localhost", port: int = 5432, database: str = "postgres", user: str = "postgres",
                password: str = ""):
        """
        创建类实例的工厂方法，实现单例模式
        
        通过类名和主机地址作为唯一标识符，确保每个子类在每个主机上只有
        一个实例存在，避免重复创建数据库连接。
        
        Args:
            host (str): 数据库主机地址，默认为 localhost
            port (int): 数据库端口，默认为 5432
            database (str): 数据库名，默认为 postgres
            user (str): 用户名，默认为 postgres
            password (str): 密码，默认为空字符串
            
        Returns:
            PostgreSQLManager: 返回类的单例实例
        """
        # 使用类名和主机作为唯一标识符，确保每个子类有独立实例
        key = (cls.__name__, host)
        if key not in cls._instances:
            cls._instances[key] = super(PostgreSQLManager, cls).__new__(cls)
        return cls._instances[key]

    def __init__(self,
                 host: str = None,
                 port: int = None,
                 database: str = None,
                 user: str = None,
                 password: str = None):
        """
        初始化数据库连接参数
        
        从配置文件或传入参数中获取数据库连接信息，并初始化连接和游标对象。
        如果对象已经被初始化过，则跳过初始化过程，防止重复初始化。
        
        Args:
            host (str): 数据库主机地址
            port (int): 数据库端口
            database (str): 数据库名称
            user (str): 数据库用户名
            password (str): 数据库密码
        """
        # 避免重复初始化，如果已经有主机属性则直接返回
        if hasattr(self, 'host'):
            return

        # 优先使用传入参数，否则使用配置文件中的默认值
        self.host = host or settings.SQL_HOST
        self.port = port or settings.SQL_PORT
        self.database = database or settings.SQL_DB
        self.user = user or settings.SQL_USER
        self.password = password or settings.SQL_PASSWORD
        self.connection = None  # 数据库连接对象
        self.cursor = None  # 数据库游标对象

    def connect(self) -> bool:
        """
        连接到 PostgreSQL 数据库
        
        建立到 PostgreSQL 数据库的实际连接，并创建游标对象用于后续操作。
        如果连接失败，会记录错误日志并返回 False。
        
        Returns:
            bool: 连接成功返回 True，失败返回 False
        """
        try:
            # 使用配置信息建立数据库连接
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            # 创建游标对象用于执行 SQL 语句
            self.cursor = self.connection.cursor()
            logger.info(f"成功连接到数据库 {self.database}")
            return True
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            return False

    def disconnect(self):
        """
        断开数据库连接
        
        关闭数据库游标和连接，释放相关资源。
        在程序结束前应调用此方法确保数据库连接正确关闭。
        """
        # 先关闭游标
        if self.cursor:
            self.cursor.close()
        # 再关闭连接
        if self.connection:
            self.connection.close()
            logger.info("数据库连接已关闭")

    def gen_select_query(self, table_name: str,
                         order_by: str = None, limit: int = None,
                         exact_match_fields: List[str] = None,
                         partial_match_fields: List[str] = None,
                         allowed_fileds: List[str] = None, **kwargs) -> Tuple[str, tuple]:
        """
        生成 SELECT 查询语句
        
        根据传入的参数动态构建 SQL 查询语句，支持精确匹配和部分匹配两种方式，
        并可指定排序和限制条件。
        
        Args:
            table_name (str): 要查询的表名
            order_by (str): 排序字段，可选
            limit (int): 限制返回结果数量，可选
            exact_match_fields (List[str]): 需要精确匹配的字段列表
            partial_match_fields (List[str]): 需要部分匹配的字段列表
            allowed_fileds (List[str]): 允许查询的字段列表
            **kwargs: 查询条件的关键字参数
            
        Returns:
            Tuple[str, tuple]: 包含 SQL 查询语句和参数元组的元组
        """
        # 初始化查询条件和参数列表
        conditions = []
        values = []
        logger.info(f"查询参数: {kwargs}")

        # 遍历所有查询条件
        for key, value in kwargs.items():
            # 验证字段名是否在允许的字段列表中，防止 SQL 注入
            if key not in allowed_fileds:
                logging.warning(f"Invalid field name: {key}")
                continue

            # 根据字段类型确定匹配方式
            if key in exact_match_fields:
                # 精确匹配，适用于 ID、状态等精确值
                conditions.append(f"{key} = %s")
                values.append(value)
            elif key in partial_match_fields:
                # 部分匹配，适用于名称、描述等模糊搜索
                conditions.append(f"{key} LIKE %s")
                values.append(f"%{value}%")
            else:
                # 其他字段默认使用精确匹配
                conditions.append(f"{key} = %s")
                values.append(value)

        # 构建基础查询语句
        query = f"SELECT * FROM {table_name}"

        # 添加 WHERE 条件
        if conditions:
            where_clause = " AND ".join(conditions)
            query = f"{query} WHERE {where_clause}"

        # 添加排序条件
        if order_by:
            query = f"{query} ORDER BY {order_by}"  # 修复：移除sql.SQL包装，因为它可能导致问题

        # 添加限制条件
        if limit:
            query = f"{query} LIMIT {limit}"

        logger.info(f"查询语句: {query} 条件参数:{values}")
        return query, tuple(values)

    def execute_query(self, query: str, params: Tuple = None) -> Optional[List[Tuple]]:
        """
        执行查询语句
        
        根据查询语句的类型执行相应的数据库操作，如果是 SELECT 语句则返回查询结果，
        其他语句（INSERT、UPDATE、DELETE）则提交事务并返回执行结果。
        
        Args:
            query (str): 要执行的 SQL 查询语句
            params (Tuple): 查询参数元组，可选
            
        Returns:
            Optional[List[Tuple]]: SELECT 语句返回查询结果列表，其他语句返回 True 或 False
        """
        try:
            # 检查连接是否已关闭，如果关闭则重新连接
            if self.connection is None or self.connection.closed:
                logger.debug("数据库连接已关闭，重新连接...")
                self.connect()
            
            # 根据是否有参数决定如何执行查询
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            # 将 SQL 对象转换为字符串进行检查
            if isinstance(query, sql.SQL):
                query = query.as_string(self.cursor)
            if query.strip().upper().startswith("SELECT"):
                # SELECT 语句返回查询结果
                res = self.cursor.fetchall()
                logger.info(f"查询成功: {res}")
                return res
            else:
                # 其他语句提交事务
                self.connection.commit()
                logger.info(f"执行成功: {query[:50]}...")
                return True
        except Exception as e:
            # 出错时回滚事务
            self.connection.rollback()
            logger.error(f"查询执行失败: {e}")
            return False

    def create_table(self, table_name: str, columns: Dict[str, str]) -> bool:
        """
        创建数据表
        
        根据传入的表名和列定义创建数据表，支持普通列定义和外键约束。
        同时会自动创建 updated_at 字段的更新触发器。
        
        Args:
            table_name (str): 要创建的表名
            columns (Dict[str, str]): 列定义字典，键为列名，值为列定义
            
        Returns:
            bool: 创建成功返回 True，失败返回 False
        """
        try:
            # 分离外键约束和其他列定义
            column_defs = []
            foreign_keys = []

            for col, defn in columns.items():
                if defn.startswith("FOREIGN KEY"):
                    foreign_keys.append(defn)
                else:
                    column_defs.append(f"{col} {defn}")

            # 构建完整的 CREATE TABLE 语句
            create_stmt = f"CREATE TABLE IF NOT EXISTS {table_name} (\n    "
            create_stmt += ",\n    ".join(column_defs)

            if foreign_keys:
                create_stmt += ",\n    " + ",\n    ".join(foreign_keys)

            create_stmt += "\n);"

            self.cursor.execute(create_stmt)
            self.connection.commit()

            # 创建 updated_at 触发器
            self._create_update_trigger(table_name)

            logger.info(f"表 {table_name} 创建成功")
            return True
        except Exception as e:
            # 出错时回滚事务
            self.connection.rollback()
            logger.error(f"创建表 {table_name} 失败: {e}")
            return False

    def _create_update_trigger(self, table_name: str):
        """
        创建更新时间戳触发器
        
        为指定表创建一个触发器，在每次更新记录时自动更新 updated_at 字段为当前时间。
        
        Args:
            table_name (str): 要创建触发器的表名
        """
        try:
            # 创建更新函数
            trigger_func = """
                           CREATE \
                           OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
                           BEGIN
                NEW.updated_at \
                           = CURRENT_TIMESTAMP;
                           RETURN NEW;
                           END;
            $$ \
                           language 'plpgsql'; \
                           """
            self.cursor.execute(trigger_func)

            # 创建触发器
            trigger_stmt = f"""
            DROP TRIGGER IF EXISTS update_{table_name}_updated_at ON {table_name};
            CREATE TRIGGER update_{table_name}_updated_at
            BEFORE UPDATE ON {table_name}
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
            """
            self.cursor.execute(trigger_stmt)
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            logger.warning(f"创建触发器失败: {e}")

    def insert(self, table_name: str, data: Dict[str, Any]) -> bool:
        """
        插入数据到指定表
        
        将传入的数据字典插入到指定表中，支持自动处理 JSON 类型和 numpy 类型数据。
        使用参数化查询防止 SQL 注入攻击。
        
        Args:
            table_name (str): 目标表名
            data (Dict[str, Any]): 要插入的数据字典
            
        Returns:
            bool: 插入成功返回 True，失败返回 False
        """
        
        def convert_value(value):
            """转换值为 PostgreSQL 适配的类型"""
            if value is None:
                return None
            # 处理 numpy 类型
            if hasattr(value, 'item'):  # numpy 标量类型（numpy.float32, numpy.int64 等）
                return value.item()
            if hasattr(value, 'tolist'):  # numpy 数组
                return json.dumps(value.tolist(), ensure_ascii=False)
            # 处理字典和列表
            if isinstance(value, (list, dict)):
                return json.dumps(value, ensure_ascii=False)
            return value
        
        try:
            # 处理数据，转换 numpy 类型和 JSON 数据
            processed_data = {}
            for key, value in data.items():
                processed_data[key] = convert_value(value)

            # 构建插入语句的列名和值
            columns = list(processed_data.keys())
            values = list(processed_data.values())
            placeholders = ", ".join(["%s"] * len(values))

            # 使用 SQL 模板构建安全的插入语句
            query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                sql.Identifier(table_name),
                sql.SQL(", ").join(map(sql.Identifier, columns)),
                sql.SQL(placeholders)
            )

            self.cursor.execute(query, values)
            self.connection.commit()
            logger.info(f"成功插入数据到表 {table_name}")
            return True
        except Exception as e:
            # 出错时回滚事务并抛出异常
            self.connection.rollback()
            logger.error(f"插入数据失败: {e}")
            raise e

    def update(self, table_name: str, data: Dict[str, Any], **where_conditions) -> bool:
        """
        更新表中的数据
        
        根据条件更新指定表中的数据，支持 JSON 数据处理和参数化查询。
        
        Args:
            table_name (str): 要更新的表名
            data (Dict[str, Any]): 要更新的数据字典
            **where_conditions: 用于确定更新哪些记录的条件
            
        Returns:
            bool: 更新成功返回 True，失败返回 False
        """
        try:
            # 处理 JSON 数据，将字典和列表转换为 JSON 字符串
            processed_data = {}
            for key, value in data.items():
                if isinstance(value, (list, dict)):
                    processed_data[key] = json.dumps(value, ensure_ascii=False)
                else:
                    processed_data[key] = value

            # 构建 SET 子句
            set_parts = []
            set_values = []
            for key, value in processed_data.items():
                set_parts.append(f"{key} = %s")
                set_values.append(value)

            # 构建 WHERE 子句
            where_parts = []
            where_values = []
            for key, value in where_conditions.items():
                where_parts.append(f"{key} = %s")
                where_values.append(value)

            set_clause = ", ".join(set_parts)
            where_clause = " AND ".join(where_parts)

            query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"

            # 合并参数
            all_values = set_values + where_values

            self.cursor.execute(query, all_values)
            self.connection.commit()

            # 检查是否有行被更新
            rows_affected = self.cursor.rowcount
            logger.info(f"成功更新表 {table_name} 中的 {rows_affected} 行数据")
            return rows_affected > 0
        except Exception as e:
            # 出错时回滚事务
            self.connection.rollback()
            logger.error(f"更新数据失败: {e}")
            return False

    def delete(self, table_name: str, **where_conditions) -> bool:
        """
        从表中删除数据
        
        根据传入的条件从指定表中删除记录。
        
        Args:
            table_name (str): 要删除数据的表名
            **where_conditions: 用于确定删除哪些记录的条件
            
        Returns:
            bool: 删除成功返回 True，失败返回 False
        """
        try:
            # 构建 WHERE 子句
            where_parts = []
            where_values = []
            for key, value in where_conditions.items():
                where_parts.append(f"{key} = %s")
                where_values.append(value)

            where_clause = " AND ".join(where_parts)
            query = f"DELETE FROM {table_name} WHERE {where_clause}"

            self.cursor.execute(query, where_values)
            self.connection.commit()

            # 检查是否有行被删除
            rows_affected = self.cursor.rowcount
            logger.info(f"成功从表 {table_name} 中删除 {rows_affected} 行数据")
            return rows_affected > 0
        except Exception as e:
            # 出错时回滚事务
            self.connection.rollback()
            logger.error(f"删除数据失败: {e}")
            return False

    def __enter__(self):
        """上下文管理器入口
        
        使类可以与 with 语句一起使用，自动处理数据库连接的开启。
        
        Returns:
            PostgreSQLManager: 返回当前实例
        """
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口
        
        使类可以与 with 语句一起使用，自动处理数据库连接的关闭。
        
        Args:
            exc_type: 异常类型
            exc_val: 异常值
            exc_tb: 异常追踪信息
        """
        self.disconnect()

    def migrate_add_fields(self, table_name: str, field_definitions: dict, constraint_definitions: dict = None):
        """通用迁移方法：为指定表添加字段和约束

        Args:
            table_name: 表名称
            field_definitions: 字段定义字典，格式为 {字段名: SQL定义语句}
            constraint_definitions: 约束定义字典，格式为 {字段名: 约束SQL语句}，可选

        Returns:
            bool: 迁移是否成功
        """
        if constraint_definitions is None:
            constraint_definitions = {}

        print(f"开始执行{table_name}表字段扩展迁移...")

        try:
            added_fields = []
            added_constraints = []

            # 按字段顺序处理
            for field_name, field_sql in field_definitions.items():
                print(f"处理字段: {field_name}")

                # 检查字段是否存在
                check_field_query = f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}' 
                AND column_name = '{field_name}';
                """
                result = self.execute_query(check_field_query)

                if not result:
                    # 添加字段
                    add_field_query = f"""
                    ALTER TABLE {table_name} 
                    ADD COLUMN {field_name} {field_sql};
                    """
                    self.execute_query(add_field_query)
                    print(f"  ✓ 已添加{field_name}字段")
                    added_fields.append(field_name)

                    # 如果有对应的约束定义，则添加约束
                    if field_name in constraint_definitions:
                        constraint_sql = constraint_definitions[field_name]
                        add_constraint_query = f"""
                        ALTER TABLE {table_name} 
                        ADD CONSTRAINT {field_name} {constraint_sql};
                        """
                        self.execute_query(add_constraint_query)
                        print(f"  ✓ 已添加{field_name}字段的约束")
                        added_constraints.append(field_name)
                else:
                    print(f"  ✓ {field_name}字段已存在，跳过添加")

            # 显示最终表结构
            print(f"显示{table_name}表最终结构:")
            structure_query = f"""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position;
            """
            result = self.execute_query(structure_query)
            if result:
                print(f"  当前{table_name}表结构:")
                for row in result:
                    print(f"    {row[0]}: {row[1]} (nullable: {row[2]}, default: {row[3]})")

            print(f"迁移完成！{table_name}表已成功添加新字段")
            if added_fields:
                print("新增字段:")
                for field in added_fields:
                    print(f"  - {field}: {field_definitions[field]}")
            if added_constraints:
                print("新增约束:")
                for constraint in added_constraints:
                    print(f"  - {constraint}: {constraint_definitions[constraint]}")

            return True

        except Exception as e:
            print(f"迁移失败: {e}")
            return False
