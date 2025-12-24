from src.sql_funs.sql_base import PostgreSQLManager


class CreateTables(PostgreSQLManager):
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
