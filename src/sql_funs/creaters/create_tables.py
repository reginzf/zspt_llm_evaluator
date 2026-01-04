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
        self.create_local_knowledge()
        self.create_local_knowledge_list()

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
            "zlpt_base_id": "VARCHAR(100)",  # 外键，关联环境信息
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "FOREIGN KEY (zlpt_base_id)": "REFERENCES ai_environment_info(zlpt_base_id) ON DELETE SET NULL"
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

    def create_local_knowledge(self) -> bool:
        columns = {
            "id": "SERIAL PRIMARY KEY",
            "kno_id": "VARCHAR(100) NOT NULL UNIQUE",
            "kno_name": "VARCHAR(200) NOT NULL",
            "kno_describe": "TEXT",  # 描述
            "kno_path": "VARCHAR(500)",  # 相对于ai_local_knowledge_list的相对路径
            "ls_status": "INTEGER DEFAULT 1",  # label-studio中是否完成了标准  0 已完成 1 未开始 2 进行中
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"

        }
        return self.create_table("ai_local_knowledge", columns)

    def create_local_knowledge_list(self) -> bool:
        columns = {
            "id": "SERIAL PRIMARY KEY",
            "knol_id": "VARCHAR(100) NOT NULL UNIQUE",
            "knol_name": "VARCHAR(200) NOT NULL",
            "knol_describe": "TEXT",  # 描述
            "knol_path": "VARCHAR(500)",  # 文件夹绝对目录
            "ls_status": "INTEGER DEFAULT 1",  # label-studio中是否完成了标准  0 已完成 1 未开始 2 进行中
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "kno_id": "VARCHAR(100) NOT NULL UNIQUE",
            "FOREIGN KEY (kno_id)": "REFERENCES ai_local_knowledge(kno_id) ON DELETE CASCADE"  # 上级文件夹作为外键
        }
        return self.create_table("ai_local_knowledge_list", columns)

    def create_knowledge_bind_table(self) -> bool:
        """创建知识库绑定关系表"""
        columns = {
            "id": "SERIAL PRIMARY KEY",
            "kno_id": "VARCHAR(100) NOT NULL",  # ai_local_knowledge表的kno_id
            "knowledge_id": "VARCHAR(100) NOT NULL",  # ai_knowledge_base表的knowledge_id
            "bind_status": "INTEGER DEFAULT 0 CHECK (bind_status IN (0, 1, 2, 3, 4))",  # 绑定状态: 0-未绑定, 1-绑定中, 2-已绑定, 3-解绑中, 4-已解绑
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "UNIQUE (kno_id, knowledge_id)": "",  # 确保每对kno_id和knowledge_id的组合唯一
            "FOREIGN KEY (kno_id)": "REFERENCES ai_local_knowledge(kno_id) ON DELETE CASCADE",
            "FOREIGN KEY (knowledge_id)": "REFERENCES ai_knowledge_base(knowledge_id) ON DELETE CASCADE"
        }
        return self.create_table("ai_knowledge_bind", columns)

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
        self.create_local_knowledge()
        self.create_local_knowledge_list()
        self.create_knowledge_bind_table()  # 新增绑定关系表


if __name__ == '__main__':
    with CreateTables() as ct:
        ct.create_all_tables()
