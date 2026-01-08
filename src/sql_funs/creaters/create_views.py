from src.sql_funs.sql_base import PostgreSQLManager


class CreateViews(PostgreSQLManager):
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
                        'content', bq.question_content
                    )
                ) FILTER(WHERE bq.id IS NOT NULL), \
                                    '[]' ::jsonb \
                            ) || \
                            COALESCE( \
                                    jsonb_agg( \
                                        DISTINCT jsonb_build_object(
                        'table', 'detailed',
                        'type', dq.question_type,
                        'content', dq.question_content
                    )
                ) FILTER(WHERE dq.id IS NOT NULL), \
                                    '[]' ::jsonb \
                            ) || \
                            COALESCE( \
                                    jsonb_agg( \
                                        DISTINCT jsonb_build_object(
                        'table', 'mechanism',
                        'type', mq.question_type,
                        'content', mq.question_content
                    )
                ) FILTER(WHERE mq.id IS NOT NULL), \
                                    '[]' ::jsonb \
                            ) || \
                            COALESCE( \
                                    jsonb_agg( \
                                        DISTINCT jsonb_build_object(
                        'table', 'thematic',
                        'type', tq.question_type,
                        'content', tq.question_content
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