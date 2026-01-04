import psycopg2
from psycopg2 import sql
from typing import Optional, List, Tuple, Dict, Any, Union
import json
import logging

from env_config_init import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PostgreSQLManager:
    """PostgreSQL 数据库管理类"""

    _instances = {}

    def __new__(cls, host: str = "localhost", port: int = 5432, database: str = "postgres", user: str = "postgres",
                password: str = ""):
        """
        实现以host和类名作为key的单例模式，确保每个子类有独立实例
        """
        # 使用类名和主机作为唯一标识符
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
        """
        # 避免重复初始化
        if hasattr(self, 'host'):
            return

        self.host = host or settings.SQL_HOST
        self.port = port or settings.SQL_PORT
        self.database = database or settings.SQL_DB
        self.user = user or settings.SQL_USER
        self.password = password or settings.SQL_PASSWORD
        self.connection = None
        self.cursor = None

    def connect(self) -> bool:
        """
        连接到 PostgreSQL 数据库
        """
        try:
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            self.cursor = self.connection.cursor()
            logger.info(f"成功连接到数据库 {self.database}")
            return True
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            return False

    def disconnect(self):
        """断开数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
            logger.info("数据库连接已关闭")

    def gen_select_query(self, table_name,
                         order_by=None, limit=None, exact_match_fields=None, partial_match_fields=None,
                         allowed_fileds=None, **kwargs):
        """
        生成查询的命令行
        :param table_name:
        :param order_by:
        :param limit:
        :param exact_match_fields:
        :param partial_match_fields:
        :param allowed_fileds:
        :param kwargs:
        :return:
        """
        conditions = []
        values = []
        logger.info(f"查询参数: {kwargs}")
        for key, value in kwargs.items():
            # 验证字段名是否合法
            if key not in allowed_fileds:
                logging.warning(f"Invalid field name: {key}")
                continue

            # 根据字段类型确定匹配方式
            if key in exact_match_fields:
                # 精确匹配
                conditions.append(f"{key} = %s")
                values.append(value)
            elif key in partial_match_fields:
                # 部分匹配
                conditions.append(f"{key} LIKE %s")
                values.append(f"%{value}%")
            else:
                # 其他字段默认使用精确匹配
                conditions.append(f"{key} = %s")
                values.append(value)
        query = f"SELECT * FROM {table_name}"
        if conditions:
            where_clause = " AND ".join(conditions)
            query = f"{query} WHERE {where_clause}"
        if order_by:
            query = f"{query} ORDER BY {sql.SQL(order_by)}"
        if limit:
            query = f"{query} LIMIT {limit}"
        logger.info(f"查询语句: {query} 条件参数:{values}")
        return query, tuple(values)

    def execute_query(self, query: str, params: Tuple = None) -> Optional[List[Tuple]]:
        """
        执行查询语句
        """
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            # 将 SQL 对象转换为字符串进行检查
            if isinstance(query, sql.SQL):
                query = query.as_string(self.cursor)
            if query.strip().upper().startswith("SELECT"):
                res = self.cursor.fetchall()
                logger.info(f"查询成功: {res}")
                return res
            else:
                self.connection.commit()
                logger.info(f"执行成功: {query[:50]}...")
                return None
        except Exception as e:
            self.connection.rollback()
            logger.error(f"查询执行失败: {e}")
            return False

    def create_table(self, table_name: str, columns: Dict[str, str]) -> bool:
        """
        创建表
        """
        try:
            # 分离外键约束
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
            self.connection.rollback()
            logger.error(f"创建表 {table_name} 失败: {e}")
            return False

    def _create_update_trigger(self, table_name: str):
        """创建更新触发器"""
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
        插入数据
        """
        try:
            # 处理 JSON 数据
            processed_data = {}
            for key, value in data.items():
                if isinstance(value, (list, dict)):
                    processed_data[key] = json.dumps(value, ensure_ascii=False)
                else:
                    processed_data[key] = value

            columns = list(processed_data.keys())
            values = list(processed_data.values())
            placeholders = ", ".join(["%s"] * len(values))

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
            self.connection.rollback()
            logger.error(f"插入数据失败: {e}")
            return False

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()
