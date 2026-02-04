from src.sql_funs.sql_base import PostgreSQLManager


class CreateTables(PostgreSQLManager):
    # 通用字段定义
    COMMON_FIELDS = {
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    }

    # 问题表的通用字段定义
    QUESTION_TABLE_FIELDS = {
        "id": "SERIAL PRIMARY KEY",
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
            "zlpt_base_id": "VARCHAR(100) PRIMARY KEY",
            "zlpt_name": "VARCHAR(200) NOT NULL",
            "zlpt_base_url": "VARCHAR(500) NOT NULL",
            "key1": "TEXT",
            "key2_add": "TEXT",
            "pk": "TEXT",
            "username": "VARCHAR(100) NOT NULL",
            "password": "VARCHAR(100) NOT NULL",
            "domain": "VARCHAR(100) DEFAULT 'default'",
        }

        return self._create_table_with_common_fields("ai_environment_info", columns)

    def create_knowledge_base_table(self) -> bool:
        """2. 创建知识库表"""
        columns = {
            "knowledge_id": "VARCHAR(100) PRIMARY KEY",
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
            "kno_path_id": "VARCHAR(100) PRIMARY KEY",
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
            "label_studio_id": "VARCHAR(100) PRIMARY KEY",
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
            "doc_id": "VARCHAR(100) PRIMARY KEY",
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
            "question_id": "VARCHAR(100) PRIMARY KEY",
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
            "id": "SERIAL PRIMARY KEY",
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

    def create_local_knowledge_list(self) -> bool:
        columns = {
            "id": "SERIAL PRIMARY KEY",
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
            "id": "SERIAL PRIMARY KEY",
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
            "id": "SERIAL PRIMARY KEY",
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
            "id": "SERIAL PRIMARY KEY",
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
            "task_id": "VARCHAR(100) PRIMARY KEY",
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
            "knowledge_base_id": "VARCHAR(100) NOT NULL",
            "annotation_type": "VARCHAR(20) CHECK (annotation_type IN ('llm', 'manual', 'mlb'))",
            "FOREIGN KEY (local_knowledge_id)": "REFERENCES ai_local_knowledge(kno_id) ON DELETE CASCADE",
            "FOREIGN KEY (question_set_id)": "REFERENCES ai_question_config(question_id) ON DELETE CASCADE",
            "FOREIGN KEY (label_studio_env_id)": "REFERENCES ai_label_studio_info(label_studio_id) ON DELETE CASCADE",
            "FOREIGN KEY (knowledge_base_id)": "REFERENCES ai_knowledge_base(knowledge_id) ON DELETE CASCADE",
        }
        return self.create_table("ai_annotation_tasks", columns)

    def create_metric_tasks_table(self):
        """11. 创建指标任务表"""
        columns = {
            "task_id": "VARCHAR(100)",
            "status": "VARCHAR(20) NOT NULL DEFAULT '初始化'",
            "search_type": "VARCHAR(50) CHECK (search_type IN ('vectorSearch', 'hybridSearch', 'augmentedSearch'))",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "knowledge_base_id": "VARCHAR(100)",  # 新增：知识库ID字段
            "match_type": "VARCHAR(20) CHECK (match_type IN ('chunkTextMatch', 'chunkIdMatch'))",
            "metric_task_id":"VARCHAR(20) PRIMARY KEY",
            "FOREIGN KEY (task_id)": "REFERENCES ai_annotation_tasks(task_id) ON DELETE CASCADE",
            "FOREIGN KEY (knowledge_base_id)": "REFERENCES ai_knowledge_base(knowledge_id) ON DELETE SET NULL"  # 可以为NULL
        }
        return self.create_table("ai_metric_tasks", columns)

    def create_report_table(self):
        """12. 创建报告表"""
        columns = {
            "report_id": "VARCHAR(100) PRIMARY KEY",
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
        self.create_label_studio_bind_table()  # 新增localknowledge和labelstudio的绑定关系表
        self.create_annotation_tasks_table()  # 新增标注任务表
        self.create_metric_tasks_table()  # 新增指标任务表
        self.create_report_table()
        self.create_local_knowledge_file_upload_table()


if __name__ == '__main__':
    with CreateTables() as ct:
        ct.create_all_tables()
        # ct.migrate_add_fields('ai_metric_tasks',{'metric_task_id':'VARCHAR(20)'})