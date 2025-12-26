import psycopg2
from psycopg2 import sql
from typing import Optional, List, Tuple, Dict, Any
import json
import logging

from env_config_init import settings

logging.basicConfig(level=logging.INFO)


class PostgreSQLManager:
    """PostgreSQL 数据库管理类"""

    _instances = {}

    def __new__(cls, host: str = "localhost", port: int = 5432, database: str = "postgres", user: str = "postgres",
                password: str = ""):
        """
        实现以host作为key的单例模式
        """
        if host not in cls._instances:
            cls._instances[host] = super(PostgreSQLManager, cls).__new__(cls)
        return cls._instances[host]

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
        self.logger = logging.logger(__name__)

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
            self.logger.info(f"成功连接到数据库 {self.database}")
            return True
        except Exception as e:
            self.logger.error(f"数据库连接失败: {e}")
            return False

    def disconnect(self):
        """断开数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
            self.logger.info("数据库连接已关闭")

    def execute_query(self, query: str, params: Tuple = None) -> Optional[List[Tuple]]:
        """
        执行查询语句
        """
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)

            if query.strip().upper().startswith("SELECT"):
                return self.cursor.fetchall()
            else:
                self.connection.commit()
                self.logger.info(f"执行成功: {query[:50]}...")
                return None
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"查询执行失败: {e}")
            return None

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

            self.logger.info(f"表 {table_name} 创建成功")
            return True
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"创建表 {table_name} 失败: {e}")
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
            self.logger.warning(f"创建触发器失败: {e}")

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
            self.logger.info(f"成功插入数据到表 {table_name}")
            return True
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"插入数据失败: {e}")
            return False

    def select(self,
               table_name: str,
               columns: List[str] = None,
               where: str = None,
               params: Tuple = None,
               order_by: str = None,
               limit: int = None) -> Optional[List[Tuple]]:
        """
        查询数据
        """
        try:
            if columns:
                columns_sql = sql.SQL(", ").join(map(sql.Identifier, columns))
            else:
                columns_sql = sql.SQL("*")

            query = sql.SQL("SELECT {} FROM {}").format(
                columns_sql,
                sql.Identifier(table_name)
            )

            if where:
                query = sql.SQL("{} WHERE {}").format(query, sql.SQL(where))

            if order_by:
                query = sql.SQL("{} ORDER BY {}").format(query, sql.SQL(order_by))

            if limit:
                query = sql.SQL("{} LIMIT %s").format(query)
                if params:
                    params = params + (limit,)
                else:
                    params = (limit,)

            results = self.execute_query(query.as_string(self.connection), params)

            # 解析 JSON 字段
            if results and columns:
                parsed_results = []
                for row in results:
                    parsed_row = []
                    for i, col in enumerate(row):
                        if isinstance(col, str) and col.startswith(('{', '[')):
                            try:
                                parsed_row.append(json.loads(col))
                            except:
                                parsed_row.append(col)
                        else:
                            parsed_row.append(col)
                    parsed_results.append(tuple(parsed_row))
                return parsed_results

            return results
        except Exception as e:
            self.logger.error(f"查询数据失败: {e}")
            return None

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()
