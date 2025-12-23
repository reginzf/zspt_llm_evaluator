import psycopg2
from psycopg2 import sql
from typing import Optional, List, Tuple, Dict, Any
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PostgreSQLManager:
    """PostgreSQL 数据库管理类"""

    def __init__(self,
                 host: str = "localhost",
                 port: int = 5432,
                 database: str = "postgres",
                 user: str = "postgres",
                 password: str = ""):
        """
        初始化数据库连接参数
        """
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
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
                logger.info(f"执行成功: {query[:50]}...")
                return None
        except Exception as e:
            self.connection.rollback()
            logger.error(f"查询执行失败: {e}")
            return None

    def create_all_tables(self):
        """创建所有表"""
        self.create_environment_table()
        self.create_knowledge_base_table()
        self.create_knowledge_path_table()
        self.create_label_studio_table()
        self.create_knowledge_table()
        self.create_question_config_table()
        self.create_basic_questions_table()
        self.create_detailed_questions_table()
        self.create_mechanism_questions_table()
        self.create_thematic_questions_table()

        # 创建视图
        self.create_views()

    def create_environment_table(self) -> bool:
        """1. 创建环境信息表"""
        columns = {
            "zlpt_base_id": "VARCHAR(100) PRIMARY KEY",
            "zlpt_name": "VARCHAR(200) NOT NULL",
            "zlpt_base_url": "VARCHAR(500) NOT NULL",
            "key1": "TEXT",
            "key2_add": "TEXT",
            "pk": "TEXT",
            "username": "VARCHAR(100) NOT NULL",
            "password": "VARCHAR(100) NOT NULL",
            "domain": "VARCHAR(100) DEFAULT 'default'",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        }

        return self.create_table("ai_environment_info", columns)

    def create_knowledge_base_table(self) -> bool:
        """2. 创建知识库表"""
        columns = {
            "knowledge_id": "VARCHAR(100) PRIMARY KEY",
            "knowledge_name": "VARCHAR(200) NOT NULL",
            "kno_root_id": "VARCHAR(100)",
            "chunk_size": "INTEGER DEFAULT 500",
            "chunk_overlap": "DECIMAL(3,2) DEFAULT 0.2",
            "sliceidentifier": "JSONB DEFAULT '[]'::jsonb",
            "visiblerange": "INTEGER DEFAULT 0",
            "deptidlist": "JSONB DEFAULT '[]'::jsonb",
            "managedeptidlist": "JSONB DEFAULT '[]'::jsonb",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        }

        return self.create_table("ai_knowledge_base", columns)

    def create_knowledge_path_table(self) -> bool:
        """3. 创建知识库目录表"""
        columns = {
            "kno_path_id": "VARCHAR(100) PRIMARY KEY",
            "kno_path_name": "VARCHAR(200) NOT NULL",
            "knowledge_id": "VARCHAR(100) NOT NULL",
            "parent": "VARCHAR(100)",
            "doc_map": "JSONB DEFAULT '{}'::jsonb",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "FOREIGN KEY (knowledge_id)": "REFERENCES ai_knowledge_base(knowledge_id) ON DELETE CASCADE",
            "FOREIGN KEY (parent)": "REFERENCES ai_knowledge_path(kno_path_id) ON DELETE CASCADE"
        }

        return self.create_table("ai_knowledge_path", columns)

    def create_label_studio_table(self) -> bool:
        """4. 创建 label-studio 信息表"""
        columns = {
            "label_studio_id": "VARCHAR(100) PRIMARY KEY",
            "label_studio_url": "VARCHAR(500) NOT NULL",
            "label_studio_api_key": "VARCHAR(200) NOT NULL",
            "zlpt_base_id": "VARCHAR(100)",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "FOREIGN KEY (zlpt_base_id)": "REFERENCES ai_environment_info(zlpt_base_id) ON DELETE SET NULL"
        }

        return self.create_table("ai_label_studio_info", columns)

    def create_knowledge_table(self) -> bool:
        """5. 创建知识表"""
        columns = {
            "doc_id": "VARCHAR(100) PRIMARY KEY",
            "doc_name": "VARCHAR(200) NOT NULL",
            "doc_type": "VARCHAR(50) NOT NULL",
            "doc_describe": "TEXT",
            "doc_path": "VARCHAR(500) NOT NULL",
            "kno_path_id": "VARCHAR(100) NOT NULL",
            "knowledge_id": "VARCHAR(100) NOT NULL",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "FOREIGN KEY (kno_path_id)": "REFERENCES ai_knowledge_path(kno_path_id) ON DELETE CASCADE",
            "FOREIGN KEY (knowledge_id)": "REFERENCES ai_knowledge_base(knowledge_id) ON DELETE CASCADE"
        }

        return self.create_table("ai_knowledge", columns)

    def create_question_config_table(self) -> bool:
        """6. 创建问题配置文件表"""
        columns = {
            "question_id": "VARCHAR(100) PRIMARY KEY",
            "question_name": "VARCHAR(200) NOT NULL",
            "knowledge_id": "VARCHAR(100)",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "FOREIGN KEY (knowledge_id)": "REFERENCES ai_knowledge_base(knowledge_id) ON DELETE CASCADE"
        }

        return self.create_table("ai_question_config", columns)

    def create_basic_questions_table(self) -> bool:
        """7. 创建基础问题表"""
        columns = {
            "id": "SERIAL PRIMARY KEY",
            "question_id": "VARCHAR(100) NOT NULL",
            "question_type": "VARCHAR(50) NOT NULL CHECK (question_type IN ('factual', 'contextual', 'conceptual', 'reasoning', 'application'))",
            "question_list": "JSONB DEFAULT '[]'::jsonb",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "FOREIGN KEY (question_id)": "REFERENCES ai_question_config(question_id) ON DELETE CASCADE"
        }

        return self.create_table("ai_basic_questions", columns)

    def create_detailed_questions_table(self) -> bool:
        """8. 创建详细问题表"""
        columns = {
            "id": "SERIAL PRIMARY KEY",
            "question_id": "VARCHAR(100) NOT NULL",
            "question_type": "VARCHAR(50) NOT NULL CHECK (question_type IN ('factual', 'contextual', 'conceptual', 'reasoning', 'application'))",
            "question_list": "JSONB DEFAULT '[]'::jsonb",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "FOREIGN KEY (question_id)": "REFERENCES ai_question_config(question_id) ON DELETE CASCADE"
        }

        return self.create_table("ai_detailed_questions", columns)

    def create_mechanism_questions_table(self) -> bool:
        """9. 创建机制问题表"""
        columns = {
            "id": "SERIAL PRIMARY KEY",
            "question_id": "VARCHAR(100) NOT NULL",
            "question_type": "VARCHAR(50) NOT NULL CHECK (question_type IN ('factual', 'contextual', 'conceptual', 'reasoning', 'application'))",
            "question_list": "JSONB DEFAULT '[]'::jsonb",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "FOREIGN KEY (question_id)": "REFERENCES ai_question_config(question_id) ON DELETE CASCADE"
        }

        return self.create_table("ai_mechanism_questions", columns)

    def create_thematic_questions_table(self) -> bool:
        """10. 创建主题问题表"""
        columns = {
            "id": "SERIAL PRIMARY KEY",
            "question_id": "VARCHAR(100) NOT NULL",
            "question_type": "VARCHAR(50) NOT NULL CHECK (question_type IN ('factual', 'contextual', 'conceptual', 'reasoning', 'application'))",
            "question_list": "JSONB DEFAULT '[]'::jsonb",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "FOREIGN KEY (question_id)": "REFERENCES ai_question_config(question_id) ON DELETE CASCADE"
        }

        return self.create_table("ai_thematic_questions", columns)

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

    def create_views(self):
        """创建视图"""
        self.create_knowledge_detail_view()
        self.create_question_detail_view()
        self.create_knowledge_structure_view()

    def create_knowledge_detail_view(self):
        """创建知识库详细信息视图"""
        view_query = """
                     CREATE \
                     OR REPLACE VIEW ai_knowledge_detail_view AS
                     SELECT kb.knowledge_id, \
                            kb.knowledge_name, \
                            kb.kno_root_id, \
                            kb.chunk_size, \
                            kb.chunk_overlap, \
                            kb.sliceidentifier, \
                            kb.visiblerange, \
                            kb.created_at                  as kb_created_at, \
                            kb.updated_at                  as kb_updated_at, \
                            COUNT(DISTINCT kp.kno_path_id) as path_count, \
                            COUNT(DISTINCT k.doc_id)       as doc_count, \
                            json_agg(DISTINCT jsonb_build_object(
                'path_id', kp.kno_path_id,
                'path_name', kp.kno_path_name,
                'parent', kp.parent,
                'doc_count', doc_info.doc_key
            ))           FILTER (WHERE kp.kno_path_id IS NOT NULL) as path_structure
                     FROM ai_knowledge_base kb
                              LEFT JOIN ai_knowledge_path kp ON kb.knowledge_id = kp.knowledge_id
                              LEFT JOIN ai_knowledge k ON kb.knowledge_id = k.knowledge_id
                              LEFT JOIN LATERAL (
                         SELECT jsonb_object_keys(kp.doc_map) AS doc_key
                             ) AS doc_info ON TRUE
                     GROUP BY kb.knowledge_id, kb.knowledge_name, kb.kno_root_id,
                              kb.chunk_size, kb.chunk_overlap, kb.sliceidentifier,
                              kb.visiblerange, kb.created_at, kb.updated_at; \
                     """

        self.execute_query(view_query)
        logger.info("知识库详细信息视图创建成功")

    def create_question_detail_view(self):
        """创建问题详细信息视图"""
        view_query = """
                     CREATE \
                     OR REPLACE VIEW ai_question_detail_view AS
                     SELECT qc.question_id, \
                            qc.question_name, \
                            qc.knowledge_id, \
                            kb.knowledge_name, \
                            qc.created_at as config_created_at, \
                            qc.updated_at as config_updated_at, \
                            COALESCE( \
                                    jsonb_build_object( \
                                            'basic', (SELECT COUNT(*) \
                                                      FROM ai_basic_questions bq \
                                                      WHERE bq.question_id = qc.question_id), \
                                            'detailed', (SELECT COUNT(*) \
                                                         FROM ai_detailed_questions dq \
                                                         WHERE dq.question_id = qc.question_id), \
                                            'mechanism', (SELECT COUNT(*) \
                                                          FROM ai_mechanism_questions mq \
                                                          WHERE mq.question_id = qc.question_id), \
                                            'thematic', (SELECT COUNT(*) \
                                                         FROM ai_thematic_questions tq \
                                                         WHERE tq.question_id = qc.question_id) \
                                    ), \
                                    '{}' ::jsonb \
                            )             as question_counts, \
                            COALESCE( \
                                    jsonb_agg( \
                                        DISTINCT jsonb_build_object(
                        'table', 'basic',
                        'type', bq.question_type,
                        'count', jsonb_array_length(bq.question_list)
                    )
                ) FILTER(WHERE bq.id IS NOT NULL), \
                                    '[]' ::jsonb \
                            ) || \
                            COALESCE( \
                                    jsonb_agg( \
                                        DISTINCT jsonb_build_object(
                        'table', 'detailed',
                        'type', dq.question_type,
                        'count', jsonb_array_length(dq.question_list)
                    )
                ) FILTER(WHERE dq.id IS NOT NULL), \
                                    '[]' ::jsonb \
                            ) || \
                            COALESCE( \
                                    jsonb_agg( \
                                        DISTINCT jsonb_build_object(
                        'table', 'mechanism',
                        'type', mq.question_type,
                        'count', jsonb_array_length(mq.question_list)
                    )
                ) FILTER(WHERE mq.id IS NOT NULL), \
                                    '[]' ::jsonb \
                            ) || \
                            COALESCE( \
                                    jsonb_agg( \
                                        DISTINCT jsonb_build_object(
                        'table', 'thematic',
                        'type', tq.question_type,
                        'count', jsonb_array_length(tq.question_list)
                    )
                ) FILTER(WHERE tq.id IS NOT NULL), \
                                    '[]' ::jsonb \
                            )             as question_details
                     FROM ai_question_config qc
                              LEFT JOIN ai_knowledge_base kb ON qc.knowledge_id = kb.knowledge_id
                              LEFT JOIN ai_basic_questions bq ON qc.question_id = bq.question_id
                              LEFT JOIN ai_detailed_questions dq ON qc.question_id = dq.question_id
                              LEFT JOIN ai_mechanism_questions mq ON qc.question_id = mq.question_id
                              LEFT JOIN ai_thematic_questions tq ON qc.question_id = tq.question_id
                     GROUP BY qc.question_id, qc.question_name, qc.knowledge_id,
                              kb.knowledge_name, qc.created_at, qc.updated_at; \
                     """

        self.execute_query(view_query)
        logger.info("问题详细信息视图创建成功")

    def create_knowledge_structure_view(self):
        """创建知识结构视图（知识库-目录-文档层级关系）"""
        view_query = """
                     CREATE \
                     OR REPLACE VIEW ai_knowledge_structure_view AS
                     SELECT kb.knowledge_id, \
                            kb.knowledge_name, \
                            kp.kno_path_id, \
                            kp.kno_path_name, \
                            kp.parent, \
                            k.doc_id, \
                            k.doc_name, \
                            k.doc_type, \
                            k.doc_describe, \
                            k.doc_path, \
                            k.created_at as doc_created_at, \
                            ROW_NUMBER()    OVER (PARTITION BY kb.knowledge_id ORDER BY kp.kno_path_id, k.doc_name) as display_order
                     FROM ai_knowledge_base kb
                              LEFT JOIN ai_knowledge_path kp ON kb.knowledge_id = kp.knowledge_id
                              LEFT JOIN ai_knowledge k ON kp.kno_path_id = k.kno_path_id
                     ORDER BY kb.knowledge_id,
                              CASE WHEN kp.parent IS NULL THEN 0 ELSE 1 END,
                              kp.kno_path_id; \
                     """

        self.execute_query(view_query)
        logger.info("知识结构视图创建成功")

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
            logger.error(f"查询数据失败: {e}")
            return None

    def get_knowledge_detail(self, knowledge_id: str = None) -> Optional[List[Tuple]]:
        """
        获取知识库详细信息
        """
        query = "SELECT * FROM ai_knowledge_detail_view"
        params = None

        if knowledge_id:
            query += " WHERE knowledge_id = %s"
            params = (knowledge_id,)

        return self.execute_query(query, params)

    def get_question_detail(self, question_id: str = None) -> Optional[List[Tuple]]:
        """
        获取问题详细信息
        """
        query = "SELECT * FROM ai_question_detail_view"
        params = None

        if question_id:
            query += " WHERE question_id = %s"
            params = (question_id,)

        return self.execute_query(query, params)

    def get_knowledge_structure(self, knowledge_id: str = None) -> Optional[List[Tuple]]:
        """
        获取知识结构信息
        """
        query = "SELECT * FROM ai_knowledge_structure_view"
        params = None

        if knowledge_id:
            query += " WHERE knowledge_id = %s"
            params = (knowledge_id,)

        query += " ORDER BY display_order"

        return self.execute_query(query, params)

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()


# 使用示例
if __name__ == "__main__":
    # 配置数据库连接信息
    db_config = {
        "host": "10.210.2.223",
        "port": 5432,
        "database": "label_studio",
        "user": "labelstudio",
        "password": "Labelstudio123"
    }

    with PostgreSQLManager(**db_config) as db:
        # 创建所有表
        db.create_all_tables()

        # 检查环境信息是否已存在，避免重复插入
        existing_env = db.select("ai_environment_info", where="zlpt_base_id = %s", params=("env_001",))
        if not existing_env:
            # 示例：插入环境信息
            env_data = {
                "zlpt_base_id": "env_001",
                "zlpt_name": "成都知识平台",
                "zlpt_base_url": "https://10.220.49.200",
                "key1": "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCbPqaFZ0lgebihx",
                "key2_add": "Cw5wzjkahPKr6ZI2JNTHbHDnNbOn3Cif6GgnMBr44MhQCRPQTF2FgcxBbn3u7eGcEPMT6OZqcLzcmiMCUQRJ2MUbFI+",
                "pk": "E1vI1f+iuCQ2w8XZhRoRrmb7wBA0L63gnSwXRkJD0baL5zqlQhpSKfSH0t3opAoahwIDAQAB",
                "username": "nrgtest",
                "password": "Admin@123",
                "domain": "default"
            }
            db.insert("ai_environment_info", env_data)
        else:
            print("环境信息已存在，跳过插入")

        # 检查知识库信息是否已存在，避免重复插入
        existing_kb = db.select("ai_knowledge_base", where="knowledge_id = %s", params=("kb_001",))
        if not existing_kb:
            # 示例：插入知识库信息
            kb_data = {
                "knowledge_id": "kb_001",
                "knowledge_name": "网络协议知识库",
                "kno_root_id": "root_001",
                "chunk_size": 500,
                "chunk_overlap": 0.2,
                "sliceidentifier": ["。", "！", "!", "？", "?", "，", ",", "：", ":", "."],
                "visiblerange": 0,
                "deptidlist": [],
                "managedeptidlist": []
            }
            db.insert("ai_knowledge_base", kb_data)
        else:
            print("知识库信息已存在，跳过插入")

        # 示例：查询知识库详细信息视图
        print("知识库详细信息:")
        kb_details = db.get_knowledge_detail()
        if kb_details:
            for detail in kb_details[:3]:  # 显示前3条
                print(detail)
        else:
            print("未获取到知识库详细信息")

        # 示例：查看视图结构
        print("\n知识结构视图:")
        structure = db.get_knowledge_structure("kb_001")
        if structure:
            for item in structure:
                print(item)

        # 示例：查看问题详细信息视图
        print("\n问题详细信息视图:")
        question_view = db.select("ai_question_detail_view")
        if question_view:
            for item in question_view[:2]:
                print(item)
        else:
            print("未获取到问题详细信息")