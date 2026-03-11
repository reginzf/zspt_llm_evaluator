from src.sql_funs.sql_base import PostgreSQLManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CreateTables(PostgreSQLManager):
    # 通用字段定义
    COMMON_FIELDS = {
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    }

    # 问题表的通用字段定义
    QUESTION_TABLE_FIELDS = {
        "id": "SERIAL",
        "question_id": "VARCHAR(100) NOT NULL",
        "question_set_id": "VARCHAR(100) NOT NULL",
        "question_type": "VARCHAR(50) NOT NULL CHECK (question_type IN ('factual', 'contextual', 'conceptual', 'reasoning', 'application'))",
        "question_content": "TEXT NOT NULL",
        "chunk_ids": "JSONB DEFAULT '[]'::jsonb",  # 关联回答切片的ID列表
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        "FOREIGN KEY (question_set_id)": "REFERENCES ai_question_config(question_id) ON DELETE CASCADE"
    }

    def _create_table_with_common_fields(self, table_name: str, additional_columns: dict) -> bool:
        """辅助方法：创建包含通用字段的表"""
        columns = additional_columns.copy()
        columns.update(self.COMMON_FIELDS)
        return self.create_table(table_name, columns)

    def create_environment_table(self) -> bool:
        """1. 创建环境信息表"""
        columns = {
            "zlpt_base_id": "VARCHAR(100) NOT NULL",
            "zlpt_name": "VARCHAR(200) NOT NULL",
            "zlpt_base_url": "VARCHAR(500) NOT NULL",
            "key1": "TEXT",
            "key2_add": "TEXT",
            "pk": "TEXT",
            "username": "VARCHAR(100) NOT NULL",
            "password": "VARCHAR(100) NOT NULL",
            "domain": "VARCHAR(100) DEFAULT 'default'",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "project_name": "VARCHAR(200)",
            "project_id": "VARCHAR(100)"
        }

        return self.create_table("ai_environment_info", columns)

    def _create_environment_indexes(self):
        """为 ai_environment_info 表创建索引"""
        indexes = [
            ("idx_environment_zlpt_base_id", "CREATE INDEX idx_environment_zlpt_base_id ON ai_environment_info(zlpt_base_id)"),
            ("idx_environment_zlpt_name", "CREATE INDEX idx_environment_zlpt_name ON ai_environment_info(zlpt_name)"),
            ("idx_environment_project_id", "CREATE INDEX idx_environment_project_id ON ai_environment_info(project_id)"),
            ("idx_environment_project_name", "CREATE INDEX idx_environment_project_name ON ai_environment_info(project_name)"),
        ]
        
        for index_name, create_sql in indexes:
            try:
                self.cursor.execute(f"DROP INDEX IF EXISTS {index_name}")
                self.cursor.execute(create_sql)
                self.connection.commit()
                logger.info(f"索引 {index_name} 创建成功")
            except Exception as e:
                self.connection.rollback()
                logger.warning(f"索引 {index_name} 创建失败：{e}")

    def create_knowledge_base_table(self) -> bool:
        """2. 创建知识库表"""
        columns = {
            "knowledge_id": "VARCHAR(100) NOT NULL",
            "knowledge_name": "VARCHAR(200) NOT NULL",
            "kno_root_id": "VARCHAR(100)",
            "chunk_size": "INTEGER DEFAULT 500",
            "chunk_overlap": "INTEGER DEFAULT 10",
            "sliceidentifier": "JSONB DEFAULT '[]'::jsonb",
            "visiblerange": "INTEGER DEFAULT 0",
            "deptidlist": "JSONB DEFAULT '[]'::jsonb",
            "managedeptidlist": "JSONB DEFAULT '[]'::jsonb",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "zlpt_id": "VARCHAR(100)",  # 外键，关联环境信息
            "FOREIGN KEY (zlpt_id)": "REFERENCES ai_environment_info(zlpt_base_id) ON DELETE SET NULL"
        }

        return self.create_table("ai_knowledge_base", columns)

    def create_knowledge_path_table(self) -> bool:
        """3. 创建知识库目录表"""
        columns = {
            "kno_path_id": "VARCHAR(100) NOT NULL",
            "kno_path_name": "VARCHAR(200) NOT NULL",
            "knowledge_id": "VARCHAR(100) NOT NULL",
            "parent": "VARCHAR(100)",
            "doc_map": "JSONB DEFAULT '{}'::jsonb",
            "FOREIGN KEY (knowledge_id)": "REFERENCES ai_knowledge_base(knowledge_id) ON DELETE CASCADE",
            "FOREIGN KEY (parent)": "REFERENCES ai_knowledge_path(kno_path_id) ON DELETE CASCADE"
        }

        return self._create_table_with_common_fields("ai_knowledge_path", columns)

    def create_label_studio_table(self) -> bool:
        """4. 创建 label-studio 信息表"""
        columns = {
            "label_studio_id": "VARCHAR(100) NOT NULL",
            "label_studio_url": "VARCHAR(500) NOT NULL",
            "label_studio_api_key": "VARCHAR(200) NOT NULL",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "project_count": "INTEGER DEFAULT 0",
        }

        return self.create_table("ai_label_studio_info", columns)

    def create_knowledge_table(self) -> bool:
        """5. 创建知识表"""
        columns = {
            "doc_id": "VARCHAR(100) NOT NULL",
            "doc_name": "VARCHAR(200) NOT NULL",
            "doc_type": "VARCHAR(50) NOT NULL",
            "doc_describe": "TEXT",
            "doc_path": "VARCHAR(500) NOT NULL",
            "kno_path_id": "VARCHAR(100) NOT NULL",
            "knowledge_id": "VARCHAR(100) NOT NULL",
            "FOREIGN KEY (kno_path_id)": "REFERENCES ai_knowledge_path(kno_path_id) ON DELETE CASCADE",
            "FOREIGN KEY (knowledge_id)": "REFERENCES ai_knowledge_base(knowledge_id) ON DELETE CASCADE"
        }

        return self._create_table_with_common_fields("ai_knowledge", columns)

    def create_question_config_table(self) -> bool:
        """6. 创建问题配置文件表"""
        columns = {
            "question_id": "VARCHAR(100) NOT NULL",
            "question_name": "VARCHAR(200) NOT NULL",
            "knowledge_id": "VARCHAR(100)",
            "last_updated": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",  # 最后更新时间
            "FOREIGN KEY (knowledge_id)": "REFERENCES ai_knowledge_base(knowledge_id) ON DELETE CASCADE",
            "question_set_type": "VARCHAR(50) NOT NULL CHECK (question_set_type IN ('basic', 'detailed', 'mechanism', 'thematic'))",
            "question_count": "INTEGER DEFAULT 0"  # 问题数量统计
        }

        return self._create_table_with_common_fields("ai_question_config", columns)

    def _create_question_table(self, table_name: str) -> bool:
        """辅助方法：创建问题表"""
        return self.create_table(table_name, self.QUESTION_TABLE_FIELDS)

    def create_basic_questions_table(self) -> bool:
        """7. 创建基础问题表"""
        return self._create_question_table("ai_basic_questions")

    def create_detailed_questions_table(self) -> bool:
        """8. 创建详细问题表"""
        return self._create_question_table("ai_detailed_questions")

    def create_mechanism_questions_table(self) -> bool:
        """9. 创建机制问题表"""
        return self._create_question_table("ai_mechanism_questions")

    def create_thematic_questions_table(self) -> bool:
        """10. 创建主题问题表"""
        return self._create_question_table("ai_thematic_questions")

    def create_local_knowledge(self) -> bool:
        columns = {
            "id": "SERIAL",
            "kno_id": "VARCHAR(100) NOT NULL UNIQUE",
            "kno_name": "VARCHAR(200) NOT NULL",
            "kno_describe": "TEXT",  # 描述
            "kno_path": "VARCHAR(500)",  # 相对于ai_local_knowledge_list的相对路径
            "ls_status": "INTEGER DEFAULT 1",  # label-studio中是否完成了标准  0 已完成 1 未开始 2 进行中
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "knowledge_domain": "VARCHAR(200)",  # 知识域名
            "domain_description": "TEXT",  # 知识域描述
            "required_background": "JSONB DEFAULT '[]'::jsonb",  # 背景知识(JSONB类型存储List[str])
            "required_skills": "JSONB DEFAULT '[]'::jsonb",  # 标注LLM能力(JSONB类型存储List[str])

        }
        return self.create_table("ai_local_knowledge", columns)

    def _create_local_knowledge_indexes(self):
        """为 ai_local_knowledge 表创建索引"""
        indexes = [
            ("idx_local_knowledge_kno_id", "CREATE UNIQUE INDEX idx_local_knowledge_kno_id ON ai_local_knowledge(kno_id)"),
            ("idx_local_knowledge_name", "CREATE INDEX idx_local_knowledge_name ON ai_local_knowledge(kno_name)"),
            ("idx_local_knowledge_ls_status", "CREATE INDEX idx_local_knowledge_ls_status ON ai_local_knowledge(ls_status)"),
        ]
        
        for index_name, create_sql in indexes:
            try:
                self.cursor.execute(f"DROP INDEX IF EXISTS {index_name}")
                self.cursor.execute(create_sql)
                self.connection.commit()
                logger.info(f"索引 {index_name} 创建成功")
            except Exception as e:
                self.connection.rollback()
                logger.warning(f"索引 {index_name} 创建失败：{e}")

    def create_local_knowledge_list(self) -> bool:
        columns = {
            "id": "SERIAL",
            "knol_id": "VARCHAR(100) NOT NULL UNIQUE",
            "knol_name": "VARCHAR(200) NOT NULL",
            "knol_describe": "TEXT",  # 描述
            "knol_path": "VARCHAR(500)",  # 文件夹绝对目录
            "ls_status": "INTEGER DEFAULT 1",  # label-studio中是否完成了标准  0 已同步 1 未开始 2 同步中
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "kno_id": "VARCHAR(100) NOT NULL UNIQUE",
            "FOREIGN KEY (kno_id)": "REFERENCES ai_local_knowledge(kno_id) ON DELETE CASCADE"  # 上级文件夹作为外键
        }
        return self.create_table("ai_local_knowledge_list", columns)

    def create_local_knowledge_file_upload_table(self) -> bool:
        """创建本地知识库文件上传记录表"""
        columns = {
            "id": "SERIAL",
            "knol_id": "VARCHAR(100) NOT NULL",  # 本地知识库文件ID，关联ai_local_knowledge_list表
            "knowledge_base_id": "VARCHAR(100) NOT NULL",  # 知识库ID，关联ai_knowledge_base表
            "upload_status": "INTEGER DEFAULT 1",  # 上传状态: 0-已上传, 1-未上传, 2-上传中
            "upload_time": "TIMESTAMP DEFAULT NULL",  # 上传时间
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "FOREIGN KEY (knol_id)": "REFERENCES ai_local_knowledge_list(knol_id) ON DELETE CASCADE",  # 关联本地知识库文件
            "FOREIGN KEY (knowledge_base_id)": "REFERENCES ai_knowledge_base(knowledge_id) ON DELETE CASCADE",  # 关联知识库
            "UNIQUE (knol_id, knowledge_base_id)": ""  # 确保同一个文件在一个知识库中只能有一个记录
        }

        return self.create_table("ai_local_knowledge_file_upload", columns)

    def create_knowledge_bind_table(self) -> bool:
        """创建知识库绑定关系表"""
        columns = {
            "id": "SERIAL",
            "kno_id": "VARCHAR(100) NOT NULL",  # ai_local_knowledge表的kno_id
            "knowledge_id": "VARCHAR(100) NOT NULL",  # ai_knowledge_base表的knowledge_id
            "bind_status": "INTEGER DEFAULT 0 CHECK (bind_status IN (0, 1, 2, 3, 4))",
            # 绑定状态: 0-未绑定, 1-绑定中, 2-已绑定, 3-解绑中, 4-已解绑
            "UNIQUE (kno_id, knowledge_id)": "",  # 确保每对kno_id和knowledge_id的组合唯一
            "FOREIGN KEY (kno_id)": "REFERENCES ai_local_knowledge(kno_id) ON DELETE CASCADE",
            "FOREIGN KEY (knowledge_id)": "REFERENCES ai_knowledge_base(knowledge_id) ON DELETE CASCADE"
        }
        return self._create_table_with_common_fields("ai_knowledge_bind", columns)

    def create_label_studio_bind_table(self):
        """创建本地知识库与Label Studio绑定关系表"""
        columns = {
            "id": "SERIAL",
            "kno_id": "VARCHAR(100) NOT NULL",  # ai_local_knowledge表的kno_id
            "label_studio_id": "VARCHAR(100) NOT NULL",  # ai_label_studio_info表的label_studio_id
            "bind_status": "INTEGER DEFAULT 0 CHECK (bind_status IN (0, 1, 2, 3, 4))",
            # 绑定状态: 0-未绑定, 1-绑定中, 2-已绑定, 3-解绑中, 4-已解绑
            "UNIQUE (kno_id, label_studio_id)": "",  # 确保每对kno_id和label_studio_id的组合唯一
            "FOREIGN KEY (kno_id)": "REFERENCES ai_local_knowledge(kno_id) ON DELETE CASCADE",
            "FOREIGN KEY (label_studio_id)": "REFERENCES ai_label_studio_info(label_studio_id) ON DELETE CASCADE"
        }
        return self._create_table_with_common_fields("ai_label_studio_bind", columns)

    def create_annotation_tasks_table(self):
        """创建标注任务表"""
        columns = {
            "task_id": "VARCHAR(100) NOT NULL",
            "task_name": "VARCHAR(200) NOT NULL",
            "local_knowledge_id": "VARCHAR(100) NOT NULL",
            "question_set_id": "VARCHAR(100) NOT NULL",
            "label_studio_env_id": "VARCHAR(100) NOT NULL",
            "label_studio_project_id": "VARCHAR(100)",  # Label-Studio中创建的project ID
            "total_chunks": "INTEGER DEFAULT 0",  # 需要标注的切片总数
            "annotated_chunks": "INTEGER DEFAULT 0",  # 已标注切片数量
            "task_status": "VARCHAR(20) DEFAULT '未开始' CHECK (task_status IN ('未开始', '进行中', '已完成'))",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "knowledge_base_id": "VARCHAR(100)",
            "annotation_type": "VARCHAR(20) CHECK (annotation_type IN ('llm', 'manual', 'mlb'))",
            "FOREIGN KEY (local_knowledge_id)": "REFERENCES ai_local_knowledge(kno_id) ON DELETE CASCADE",
            "FOREIGN KEY (question_set_id)": "REFERENCES ai_question_config(question_id) ON DELETE CASCADE",
            "FOREIGN KEY (label_studio_env_id)": "REFERENCES ai_label_studio_info(label_studio_id) ON DELETE CASCADE",
            "FOREIGN KEY (knowledge_base_id)": "REFERENCES ai_knowledge_base(knowledge_id) ON DELETE CASCADE",
        }
        return self.create_table("ai_annotation_tasks", columns)

    def _create_annotation_tasks_indexes(self):
        """为 ai_annotation_tasks 表创建索引"""
        indexes = [
            ("idx_annotation_task_id", "CREATE UNIQUE INDEX idx_annotation_task_id ON ai_annotation_tasks(task_id)"),
            ("idx_annotation_local_knowledge_id", "CREATE INDEX idx_annotation_local_knowledge_id ON ai_annotation_tasks(local_knowledge_id)"),
            ("idx_annotation_question_set_id", "CREATE INDEX idx_annotation_question_set_id ON ai_annotation_tasks(question_set_id)"),
            ("idx_annotation_label_studio_env_id", "CREATE INDEX idx_annotation_label_studio_env_id ON ai_annotation_tasks(label_studio_env_id)"),
            ("idx_annotation_task_status", "CREATE INDEX idx_annotation_task_status ON ai_annotation_tasks(task_status)"),
            ("idx_annotation_knowledge_base_id", "CREATE INDEX idx_annotation_knowledge_base_id ON ai_annotation_tasks(knowledge_base_id)"),
            ("idx_annotation_type", "CREATE INDEX idx_annotation_type ON ai_annotation_tasks(annotation_type)"),
        ]
        
        for index_name, create_sql in indexes:
            try:
                self.cursor.execute(f"DROP INDEX IF EXISTS {index_name}")
                self.cursor.execute(create_sql)
                self.connection.commit()
                logger.info(f"索引 {index_name} 创建成功")
            except Exception as e:
                self.connection.rollback()
                logger.warning(f"索引 {index_name} 创建失败：{e}")

    def create_metric_tasks_table(self):
        """11. 创建指标任务表"""
        columns = {
            "task_id": "VARCHAR(100) NOT NULL",
            "status": "VARCHAR(20) NOT NULL DEFAULT '初始化'",
            "search_type": "VARCHAR(50) CHECK (search_type IN ('vectorSearch', 'hybridSearch', 'augmentedSearch'))",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "knowledge_base_id": "VARCHAR(100)",  # 新增：知识库ID字段
            "match_type": "VARCHAR(20) CHECK (match_type IN ('chunkTextMatch', 'chunkIdMatch'))",
            "metric_task_id": "VARCHAR(20)",
            "FOREIGN KEY (task_id)": "REFERENCES ai_annotation_tasks(task_id) ON DELETE CASCADE",
            "FOREIGN KEY (knowledge_base_id)": "REFERENCES ai_knowledge_base(knowledge_id) ON DELETE SET NULL"
        }
        return self.create_table("ai_metric_tasks", columns)

    def _create_metric_tasks_indexes(self):
        """为 ai_metric_tasks 表创建索引"""
        indexes = [
            ("idx_metric_task_id", "CREATE UNIQUE INDEX idx_metric_task_id ON ai_metric_tasks(task_id)"),
            ("idx_metric_status", "CREATE INDEX idx_metric_status ON ai_metric_tasks(status)"),
            ("idx_metric_knowledge_base_id", "CREATE INDEX idx_metric_knowledge_base_id ON ai_metric_tasks(knowledge_base_id)"),
            ("idx_metric_search_type", "CREATE INDEX idx_metric_search_type ON ai_metric_tasks(search_type)"),
        ]
        
        for index_name, create_sql in indexes:
            try:
                self.cursor.execute(f"DROP INDEX IF EXISTS {index_name}")
                self.cursor.execute(create_sql)
                self.connection.commit()
                logger.info(f"索引 {index_name} 创建成功")
            except Exception as e:
                self.connection.rollback()
                logger.warning(f"索引 {index_name} 创建失败：{e}")

    def create_report_table(self):
        """12. 创建报告表"""
        columns = {
            "report_id": "VARCHAR(100) NOT NULL",
            "search_type": "VARCHAR(20) CHECK (search_type IN ('vectorSearch', 'hybridSearch', 'augmentedSearch'))",
            "filepath": "VARCHAR(500) NOT NULL",
            "task_id": "VARCHAR(100)",
            "status": "VARCHAR(20) NOT NULL DEFAULT '待处理'",
            "error_msg": "TEXT",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "match_type": "VARCHAR(20) DEFAULT NULL",
            "metric_task_id": "VARCHAR(20)"
        }
        return self.create_table("ai_reports", columns)

    def create_all_tables(self):
        """创建所有表并创建索引"""
        self.create_environment_table()
        self._create_environment_indexes()  # 创建环境表索引
            
        self.create_knowledge_base_table()
        self.create_knowledge_path_table()
        self.create_label_studio_table()
        self.create_knowledge_table()
        self.create_question_config_table()
        self.create_basic_questions_table()
        self.create_detailed_questions_table()
        self.create_mechanism_questions_table()
        self.create_thematic_questions_table()
            
        self.create_local_knowledge()
        self._create_local_knowledge_indexes()  # 创建本地知识库索引
            
        self.create_local_knowledge_list()
        self.create_knowledge_bind_table()  # 新增绑定关系表
        self.create_label_studio_bind_table()  # 新增 localknowledge 和 labelstudio 的绑定关系表
            
        self.create_annotation_tasks_table()
        self._create_annotation_tasks_indexes()  # 创建标注任务索引
            
        self.create_metric_tasks_table()
        self._create_metric_tasks_indexes()  # 创建指标任务索引
            
        self.create_report_table()
        self.create_local_knowledge_file_upload_table()
        self.create_ai_qa_data_group_table()  # 新增 AI 问答对分组表
        self.create_ai_qa_data_table()  # 新增 AI 问答对数据表
        self.create_llm_models_table()
        self.create_llm_evaluation_reports_table()
        self.create_llm_evaluation_question_details_table()  # 新增 LLM 评估问题详情表

    # ==================== AI问答对数据表 ====================

    def create_ai_qa_data_group_table(self) -> bool:
        """
        创建AI问答对分组表
        
        用于管理问答对分组，前端可创建不同的测试用途分组
        """
        columns = {
            "id": "SERIAL",
            "group_uuid": "UUID DEFAULT gen_random_uuid() UNIQUE NOT NULL",
            "name": "VARCHAR(200) NOT NULL",
            "purpose": "TEXT",  # 用途描述
            "test_type": "VARCHAR(50) CHECK (test_type IN ('accuracy', 'performance', 'robustness', 'comprehensive', 'custom'))",
            "language": "VARCHAR(20) DEFAULT 'zh'",  # 语言
            "difficulty_range": "VARCHAR(50)",  # 难度范围，如 "1-5"
            "tags": "JSONB DEFAULT '[]'::jsonb",  # 标签列表
            "source_count": "INTEGER DEFAULT 0",  # 来源数据集数量统计
            "qa_count": "INTEGER DEFAULT 0",  # 问答对数量统计
            "is_active": "BOOLEAN DEFAULT TRUE",  # 是否激活
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "metadata": "JSONB DEFAULT '{}'::jsonb"  # 额外配置信息
        }

        success = self.create_table("ai_qa_data_group", columns)

        if success:
            # 创建索引
            self._create_ai_qa_data_group_indexes()

        return success

    def _create_ai_qa_data_group_indexes(self):
        """为ai_qa_data_group表创建索引"""
        indexes = [
            ("idx_qa_group_name", "CREATE INDEX idx_qa_group_name ON ai_qa_data_group(name)"),
            ("idx_qa_group_test_type", "CREATE INDEX idx_qa_group_test_type ON ai_qa_data_group(test_type)"),
            ("idx_qa_group_is_active",
             "CREATE INDEX idx_qa_group_is_active ON ai_qa_data_group(is_active) WHERE is_active = TRUE"),
            ("idx_qa_group_created_at", "CREATE INDEX idx_qa_group_created_at ON ai_qa_data_group(created_at DESC)"),
            ("idx_qa_group_tags", "CREATE INDEX idx_qa_group_tags ON ai_qa_data_group USING GIN(tags)"),
        ]

        for index_name, create_sql in indexes:
            try:
                self.cursor.execute(f"DROP INDEX IF EXISTS {index_name}")
                self.cursor.execute(create_sql)
                self.connection.commit()
                logger.info(f"索引 {index_name} 创建成功")
            except Exception as e:
                self.connection.rollback()
                # 对于向量索引，如果是因为扩展不存在导致的错误，给出更友好的提示
                if index_name == "idx_qa_data_vector" and "vector_cosine_ops" in str(e):
                    logger.warning(f"向量索引 {index_name} 创建失败，可能是pgvector扩展未安装: {e}")
                elif "gin_trgm_ops" in str(e):
                    logger.warning(f"全文搜索索引 {index_name} 创建失败，可能是pg_trgm扩展未安装: {e}")
                else:
                    logger.warning(f"索引 {index_name} 创建失败: {e}")

    def create_ai_qa_data_table(self) -> bool:
        """
        创建AI问答对数据表
        
        存储具体的问答对数据，支持分区、索引优化和TOAST技术
        """
        # 定义表结构
        columns = {
            "id": "BIGSERIAL",
            "qa_uuid": "UUID DEFAULT gen_random_uuid() NOT NULL",
            "group_id": "INTEGER NOT NULL",
            "question": "TEXT NOT NULL",
            "answers": "JSONB NOT NULL",  # 支持多种结构的答案存储
            "context": "TEXT",  # 上下文/背景信息
            "question_type": "VARCHAR(50) CHECK (question_type IN ('factual', 'contextual', 'conceptual', 'reasoning', 'application', 'multi_choice'))",
            "source_dataset": "VARCHAR(200)",  # 源数据集名称
            "hf_dataset_id": "VARCHAR(200)",  # HuggingFace原始ID
            "language": "VARCHAR(20) DEFAULT 'zh'",
            "difficulty_level": "INTEGER CHECK (difficulty_level BETWEEN 1 AND 10)",
            "category": "VARCHAR(100)",  # 分类标签
            "sub_category": "VARCHAR(100)",  # 子分类
            "tags": "JSONB DEFAULT '[]'::jsonb",  # 标签列表
            # 固定元数据
            "fixed_metadata": "JSONB DEFAULT '{}'::jsonb",
            # 动态可扩展元数据
            "dynamic_metadata": "JSONB DEFAULT '{}'::jsonb",
            # 向量化字段（可选）

            # 统计字段
            "question_length": "INTEGER",  # 问题长度
            "answer_length": "INTEGER",  # 答案长度
            "context_length": "INTEGER",  # 上下文长度
            # 时间戳
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            # 分区键
            "created_month": "DATE NOT NULL",
            # 主键和外键约束

            "FOREIGN KEY (group_id)": "REFERENCES ai_qa_data_group(id) ON DELETE CASCADE"
        }

        try:
            # 检查并创建pgvector扩展
            try:
                self.cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                logger.info("pgvector扩展创建成功或已存在")
            except Exception as ext_error:
                logger.warning(f"pgvector扩展创建失败: {ext_error}")
                logger.warning("将继续创建表，但向量相关功能可能不可用")
                # 从columns中移除向量字段
                columns.pop("vector_embedding", None)

            # 检查并创建pg_trgm扩展
            try:
                self.cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
                logger.info("pg_trgm扩展创建成功或已存在")
            except Exception as ext_error:
                logger.warning(f"pg_trgm扩展创建失败: {ext_error}")
                logger.warning("全文搜索功能可能受限")

            self.connection.commit()

            # 使用标准create_table方法创建表
            result = self.create_table("ai_qa_data", columns)

            if result:
                # 创建分区
                self._create_ai_qa_data_partitions()

                # 创建索引
                self._create_ai_qa_data_indexes()

                # 设置TOAST存储策略
                self._set_ai_qa_data_toast_strategy()

                logger.info("表 ai_qa_data 创建成功")
                return True
            else:
                logger.error("使用create_table方法创建表 ai_qa_data 失败")
                return False

        except Exception as e:
            self.connection.rollback()
            logger.error(f"创建表 ai_qa_data 失败: {e}")
            return False

    def _create_ai_qa_data_partitions(self):
        """创建ai_qa_data表的分区"""
        from datetime import datetime, timedelta

        # 创建未来12个月的分区
        current_date = datetime.now()

        for i in range(-3, 12):  # 包含前3个月和未来12个月
            partition_date = current_date + timedelta(days=30 * i)
            year_month = partition_date.strftime('%Y_%m')
            start_date = partition_date.replace(day=1).strftime('%Y-%m-%d')

            # 计算下个月的第一天
            if partition_date.month == 12:
                next_month = partition_date.replace(year=partition_date.year + 1, month=1, day=1)
            else:
                next_month = partition_date.replace(month=partition_date.month + 1, day=1)
            end_date = next_month.strftime('%Y-%m-%d')

            partition_name = f"ai_qa_data_{year_month}"

            create_partition_sql = f"""
            CREATE TABLE IF NOT EXISTS {partition_name} 
            PARTITION OF ai_qa_data
            FOR VALUES FROM ('{start_date}') TO ('{end_date}');
            """

            try:
                self.cursor.execute(create_partition_sql)
                self.connection.commit()
                logger.info(f"分区 {partition_name} 创建成功")
            except Exception as e:
                self.connection.rollback()
                logger.warning(f"分区 {partition_name} 创建失败: {e}")

    def _create_ai_qa_data_indexes(self):
        """为ai_qa_data表创建索引"""
        indexes = [
            # 主键索引（自动创建）
            # 外键索引
            ("idx_qa_data_group_id", "CREATE INDEX idx_qa_data_group_id ON ai_qa_data(group_id)"),
            # 复合索引
            ("idx_qa_data_group_difficulty",
             "CREATE INDEX idx_qa_data_group_difficulty ON ai_qa_data(group_id, difficulty_level)"),
            ("idx_qa_data_group_category", "CREATE INDEX idx_qa_data_group_category ON ai_qa_data(group_id, category)"),
            ("idx_qa_data_group_created",
             "CREATE INDEX idx_qa_data_group_created ON ai_qa_data(group_id, created_at DESC)"),
            # 全文搜索索引
            ("idx_qa_data_question_trgm",
             "CREATE INDEX idx_qa_data_question_trgm ON ai_qa_data USING GIN(question gin_trgm_ops)"),
            ("idx_qa_data_context_trgm",
             "CREATE INDEX idx_qa_data_context_trgm ON ai_qa_data USING GIN(context gin_trgm_ops)"),
            # JSONB字段GIN索引
            ("idx_qa_data_answers", "CREATE INDEX idx_qa_data_answers ON ai_qa_data USING GIN(answers)"),
            ("idx_qa_data_fixed_metadata",
             "CREATE INDEX idx_qa_data_fixed_metadata ON ai_qa_data USING GIN(fixed_metadata)"),
            ("idx_qa_data_dynamic_metadata",
             "CREATE INDEX idx_qa_data_dynamic_metadata ON ai_qa_data USING GIN(dynamic_metadata)"),
            ("idx_qa_data_tags", "CREATE INDEX idx_qa_data_tags ON ai_qa_data USING GIN(tags)"),
            # 向量索引（使用ivfflat）- 只在vector扩展可用时创建
            ("idx_qa_data_vector",
             "CREATE INDEX idx_qa_data_vector ON ai_qa_data USING ivfflat (vector_embedding vector_cosine_ops)"),
            # 条件索引
            ("idx_qa_data_high_difficulty",
             "CREATE INDEX idx_qa_data_high_difficulty ON ai_qa_data(group_id, difficulty_level) WHERE difficulty_level >= 7"),
            # 源数据集索引
            ("idx_qa_data_source", "CREATE INDEX idx_qa_data_source ON ai_qa_data(source_dataset, hf_dataset_id)"),
            # 语言索引
            ("idx_qa_data_language", "CREATE INDEX idx_qa_data_language ON ai_qa_data(language)"),
        ]

        for index_name, create_sql in indexes:
            try:
                self.cursor.execute(f"DROP INDEX IF EXISTS {index_name}")
                self.cursor.execute(create_sql)
                self.connection.commit()
                logger.info(f"索引 {index_name} 创建成功")
            except Exception as e:
                self.connection.rollback()
                # 对于向量索引，如果是因为扩展不存在导致的错误，给出更友好的提示
                if index_name == "idx_qa_data_vector" and "vector_cosine_ops" in str(e):
                    logger.warning(f"向量索引 {index_name} 创建失败，可能是pgvector扩展未安装: {e}")
                elif "gin_trgm_ops" in str(e):
                    logger.warning(f"全文搜索索引 {index_name} 创建失败，可能是pg_trgm扩展未安装: {e}")
                else:
                    logger.warning(f"索引 {index_name} 创建失败: {e}")

    def _set_ai_qa_data_toast_strategy(self):
        """设置ai_qa_data表的TOAST存储策略"""
        toast_settings = [
            # 大文本字段使用EXTERNAL策略（不压缩，快速访问）
            ("ALTER TABLE ai_qa_data ALTER COLUMN question SET STORAGE EXTERNAL"),
            ("ALTER TABLE ai_qa_data ALTER COLUMN context SET STORAGE EXTERNAL"),
            ("ALTER TABLE ai_qa_data ALTER COLUMN answers SET STORAGE EXTERNAL"),
            # JSONB字段使用MAIN策略（适度压缩）
            ("ALTER TABLE ai_qa_data ALTER COLUMN fixed_metadata SET STORAGE MAIN"),
            ("ALTER TABLE ai_qa_data ALTER COLUMN dynamic_metadata SET STORAGE MAIN"),
            # 设置表的填充因子为90%，留出空间用于HOT更新
            ("ALTER TABLE ai_qa_data SET (fillfactor = 90)"),
        ]

        for sql in toast_settings:
            try:
                self.cursor.execute(sql)
                self.connection.commit()
            except Exception as e:
                self.connection.rollback()
                logger.warning(f"TOAST设置失败: {e}")

    def create_ai_qa_data_partitions_for_month(self, year: int, month: int) -> bool:
        """
        为指定月份创建分区
        
        Args:
            year: 年份
            month: 月份
            
        Returns:
            bool: 创建成功返回True
        """
        from datetime import datetime

        year_month = f"{year}_{month:02d}"
        start_date = datetime(year, month, 1).strftime('%Y-%m-%d')

        if month == 12:
            end_date = datetime(year + 1, 1, 1).strftime('%Y-%m-%d')
        else:
            end_date = datetime(year, month + 1, 1).strftime('%Y-%m-%d')

        partition_name = f"ai_qa_data_{year_month}"

        create_partition_sql = f"""
        CREATE TABLE IF NOT EXISTS {partition_name} 
        PARTITION OF ai_qa_data
        FOR VALUES FROM ('{start_date}') TO ('{end_date}');
        """

        try:
            self.cursor.execute(create_partition_sql)
            self.connection.commit()
            logger.info(f"分区 {partition_name} 创建成功")
            return True
        except Exception as e:
            self.connection.rollback()
            logger.error(f"分区 {partition_name} 创建失败: {e}")
            return False

    def create_llm_models_table(self) -> bool:
        """创建LLM模型配置表"""
        columns = {
            "id": "SERIAL",
            "name": "VARCHAR(100) NOT NULL UNIQUE",
            "type": "VARCHAR(50) NOT NULL",
            "api_key": "TEXT NOT NULL",
            "api_url": "VARCHAR(500) NOT NULL",
            "model": "VARCHAR(100)",
            "temperature": "DECIMAL(3,2) DEFAULT 0.7",
            "max_tokens": "INTEGER DEFAULT 2048",
            "timeout": "INTEGER DEFAULT 30",
            "version": "VARCHAR(50)",
            "status": "VARCHAR(20) DEFAULT 'unknown'",
            "last_check": "TIMESTAMP",
            "is_active": "BOOLEAN DEFAULT TRUE"
        }
        columns.update(self.COMMON_FIELDS)

        success = self.create_table("ai_llm_models", columns)
        if success:
            logger.info("✓ llm_models 表创建成功")
        return success

    def create_llm_evaluation_reports_table(self) -> bool:
        """创建LLM评估报告表"""
        columns = {
            "id": "SERIAL",
            "report_name": "VARCHAR(200) NOT NULL",
            "model_name": "VARCHAR(100) NOT NULL",
            "model_id": "INTEGER NOT NULL",
            "group_id": "INTEGER NOT NULL",
            "group_name": "VARCHAR(100)",
            "report_path": "TEXT NOT NULL",
            "qa_count": "INTEGER DEFAULT 0",
            "qa_offset": "INTEGER DEFAULT 0",
            "qa_limit": "INTEGER DEFAULT 0",
            "exact_match": "DECIMAL(5,4)",
            "f1_score": "DECIMAL(5,4)",
            "semantic_similarity": "DECIMAL(5,4)",
            "avg_inference_time": "DECIMAL(10,4)",
            "evaluation_config": "JSONB DEFAULT '{}'::jsonb",
            "status": "VARCHAR(20) DEFAULT 'completed'",
            "error_message": "TEXT"
        }
        columns.update(self.COMMON_FIELDS)

        success = self.create_table("ai_llm_evaluation_reports", columns)
        if success:
            logger.info("✓ llm_evaluation_reports 表创建成功")
        return success

    def create_llm_evaluation_question_details_table(self) -> bool:
        """创建LLM评估问题详情表"""
        columns = {
            "id": "SERIAL",
            "report_id": "INTEGER NOT NULL",
            "question_id": "VARCHAR(100) NOT NULL",
            "question": "TEXT NOT NULL",
            "context": "TEXT",
            "predicted_answer": "TEXT NOT NULL",
            "ground_truth": "JSONB NOT NULL DEFAULT '[]'::jsonb",
            "success": "BOOLEAN DEFAULT TRUE",
            "inference_time": "DECIMAL(10,4) DEFAULT 0",
            "exact_match": "DECIMAL(5,4) DEFAULT 0",
            "f1_score": "DECIMAL(5,4) DEFAULT 0",
            "semantic_similarity": "DECIMAL(5,4) DEFAULT 0",
            "answer_coverage": "DECIMAL(5,4) DEFAULT 0",
            "answer_relevance": "DECIMAL(5,4) DEFAULT 0",
            "context_utilization": "DECIMAL(5,4) DEFAULT 0",
            "answer_completeness": "DECIMAL(5,4) DEFAULT 0",
            "answer_conciseness": "DECIMAL(5,4) DEFAULT 0",
            "error_message": "TEXT",
            "metadata": "JSONB DEFAULT '{}'::jsonb"
        }
        columns.update(self.COMMON_FIELDS)
        # 添加外键约束
        columns["FOREIGN KEY (report_id)"] = "REFERENCES ai_llm_evaluation_reports(id) ON DELETE CASCADE"

        success = self.create_table("ai_llm_evaluation_question_details", columns)
        if success:
            logger.info("✓ llm_evaluation_question_details 表创建成功")
            # 创建索引
            self._create_llm_evaluation_question_details_indexes()
        return success

    def _create_llm_evaluation_question_details_indexes(self):
        """为 ai_llm_evaluation_question_details 表创建索引"""
        indexes = [
            ("idx_eval_qdetails_report_id", f"CREATE INDEX idx_eval_qdetails_report_id ON ai_llm_evaluation_question_details(report_id)"),
            ("idx_eval_qdetails_question_id", f"CREATE INDEX idx_eval_qdetails_question_id ON ai_llm_evaluation_question_details(question_id)"),
            ("idx_eval_qdetails_success", f"CREATE INDEX idx_eval_qdetails_success ON ai_llm_evaluation_question_details(success)"),
            ("idx_eval_qdetails_f1_score", f"CREATE INDEX idx_eval_qdetails_f1_score ON ai_llm_evaluation_question_details(f1_score)"),
            ("idx_eval_qdetails_exact_match", f"CREATE INDEX idx_eval_qdetails_exact_match ON ai_llm_evaluation_question_details(exact_match)"),
            ("idx_eval_qdetails_semantic_sim", f"CREATE INDEX idx_eval_qdetails_semantic_sim ON ai_llm_evaluation_question_details(semantic_similarity)"),
        ]
        
        for index_name, create_sql in indexes:
            try:
                self.cursor.execute(f"DROP INDEX IF EXISTS {index_name}")
                self.cursor.execute(create_sql)
                self.connection.commit()
                logger.info(f"索引 {index_name} 创建成功")
            except Exception as e:
                self.connection.rollback()
                logger.warning(f"索引 {index_name} 创建失败: {e}")


if __name__ == '__main__':
    with CreateTables() as ct:
        ct.create_all_tables()
        # ct.migrate_add_fields('ai_metric_tasks',{'metric_task_id':'VARCHAR(20)'})
