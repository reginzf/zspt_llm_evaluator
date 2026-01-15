from src.sql_funs.sql_base import PostgreSQLManager


class CreateViews(PostgreSQLManager):
    def create_views(self):
        """创建视图"""
        self.create_annotation_metric_tasks_view()
        self.create_annotation_task_extended_view()

    def create_annotation_metric_tasks_view(self):
        """创建标注任务与指标任务关联视图"""
        view_query = """
                     CREATE
                     OR REPLACE VIEW ai_annotation_metric_tasks_view AS
                     SELECT at.task_id,
                            at.task_name,
                            at.local_knowledge_id,
                            at.question_set_id,
                            at.label_studio_env_id,
                            at.knowledge_base_id,
                            at.label_studio_project_id,
                            at.total_chunks,
                            at.annotated_chunks,
                            at.task_status,
                            at.created_at as task_created_at,
                            at.updated_at as task_updated_at,
                            at.annotation_type,
                            mt.status     as metric_status,
                            mt.search_type,
                            mt.report_path,
                            mt.created_at as metric_created_at,
                            mt.updated_at as metric_updated_at
                     FROM ai_annotation_tasks at
                    LEFT JOIN ai_metric_tasks mt
                     ON at.task_id = mt.task_id \
                     """

        self.execute_query(view_query)

    def create_annotation_task_extended_view(self):
        """创建标注任务扩展视图，包含知识库名称和问题集名称等信息"""
        view_query = """
                     CREATE
                     OR REPLACE VIEW ai_annotation_task_extended_view AS
                     SELECT 
                            at.task_id,
                            at.task_name,
                            at.local_knowledge_id,
                            at.question_set_id,
                            at.label_studio_env_id,
                            at.knowledge_base_id,
                            at.label_studio_project_id,
                            at.total_chunks,
                            at.annotated_chunks,
                            at.task_status,
                            at.created_at as task_created_at,
                            at.updated_at as task_updated_at,
                            at.annotation_type,
                            COALESCE(kb.knowledge_name, '未知知识库') as knowledge_base_name,
                            COALESCE(qc.question_name, '未知问题集') as question_set_name
                     FROM ai_annotation_tasks at
                     LEFT JOIN ai_knowledge_base kb ON at.knowledge_base_id = kb.knowledge_id
                     LEFT JOIN ai_question_config qc ON at.question_set_id = qc.question_id
                     """

        self.execute_query(view_query)

if __name__ == '__main__':
    with CreateViews() as cv:
        cv.create_views()