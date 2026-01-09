from src.sql_funs.sql_base import PostgreSQLManager
import logging

logger = logging.getLogger(__name__)


class LabelStudioCrud(PostgreSQLManager):

    def label_studio_list(self, label_studio_id=None, label_studio_url=None):
        """获取Label-Studio环境列表"""
        exact_match_fields = ['label_studio_id']
        partial_match_fields = ['label_studio_url']
        allowed_fileds = exact_match_fields + partial_match_fields
        data = {}
        if label_studio_id:
            data['label_studio_id'] = label_studio_id
        if label_studio_url:
            data['label_studio_url'] = label_studio_url

        query, values = self.gen_select_query("ai_label_studio_info",
                                              exact_match_fields=exact_match_fields,
                                              partial_match_fields=partial_match_fields,
                                              allowed_fileds=allowed_fileds, **data)
        try:
            return self.execute_query(query, values)
        except Exception as e:
            logger.error(f"获取Label-Studio环境列表时发生错误: {str(e)}")
            return []

    def label_studio_insert(self, label_studio_id, label_studio_url, label_studio_api_key):
        """插入Label-Studio环境信息"""
        try:
            data = {
                'label_studio_id': label_studio_id,
                'label_studio_url': label_studio_url,
                'label_studio_api_key': label_studio_api_key
            }
            return self.insert('ai_label_studio_info', data)
        except Exception as e:
            logger.error(f"插入Label-Studio环境信息时发生错误: {str(e)}")
            return False

    def label_studio_update(self, label_studio_id, label_studio_url=None, label_studio_api_key=None):
        """更新Label-Studio环境信息"""
        try:
            updates = {}

            if label_studio_url:
                updates['label_studio_url'] = label_studio_url
            if label_studio_api_key:
                updates['label_studio_api_key'] = label_studio_api_key

            if not updates:
                return False

            return self.update('ai_label_studio_info', updates, label_studio_id=label_studio_id)
        except Exception as e:
            logger.error(f"更新Label-Studio环境信息时发生错误: {str(e)}")
            return False

    def label_studio_delete(self, label_studio_id):
        """删除Label-Studio环境信息"""
        try:
            return self.delete('ai_label_studio_info', label_studio_id=label_studio_id)
        except Exception as e:
            logger.error(f"删除Label-Studio环境信息时发生错误: {str(e)}")
            return False

    def label_studio_bind_get(self, kno_id=None, label_studio_id=None):
        """获取Label-Studio绑定关系"""
        data = {}
        if kno_id:
            data['kno_id'] = kno_id
        if label_studio_id:
            data['label_studio_id'] = label_studio_id
        exact_match_fields = ['kno_id', 'label_studio_id', 'bind_status']
        partial_match_fields = []
        allowed_fileds = exact_match_fields + partial_match_fields
        query, values = self.gen_select_query("ai_label_studio_bind",
                                              exact_match_fields=exact_match_fields,
                                              partial_match_fields=partial_match_fields,
                                              allowed_fileds=allowed_fileds, **data)
        try:
            return self.execute_query(query, values)
        except Exception as e:
            logger.error(f"获取Label-Studio绑定关系时发生错误: {str(e)}")
            return []

    def label_studio_bind_create(self, kno_id, label_studio_id, bind_status=2):
        """创建Label-Studio绑定关系"""
        try:
            data = {
                'kno_id': kno_id,
                'label_studio_id': label_studio_id,
                'bind_status': bind_status
            }
            return self.insert('ai_label_studio_bind', data)
        except Exception as e:
            logger.error(f"创建Label-Studio绑定关系时发生错误: {str(e)}")
            return False

    def label_studio_bind_update(self, kno_id, label_studio_id, bind_status=None):
        """更新Label-Studio绑定关系"""
        try:
            updates = {}

            if bind_status is not None:
                updates['bind_status'] = bind_status

            if not updates:
                return False

            return self.update('ai_label_studio_bind', updates, kno_id=kno_id, label_studio_id=label_studio_id)
        except Exception as e:
            logger.error(f"更新Label-Studio绑定关系时发生错误: {str(e)}")
            return False

    def label_studio_bind_delete(self, kno_id, label_studio_id):
        """删除Label-Studio绑定关系"""
        try:
            return self.delete('ai_label_studio_bind', kno_id=kno_id, label_studio_id=label_studio_id)
        except Exception as e:
            logger.error(f"删除Label-Studio绑定关系时发生错误: {str(e)}")
            return False

    def _label_studio_to_json(self, row):
        """将Label-Studio数据库记录转换为JSON格式"""
        if not row:
            return None

        return {
            'label_studio_id': row[0] if len(row) > 0 else None,
            'label_studio_url': row[1] if len(row) > 1 else None,
            'label_studio_api_key': row[2] if len(row) > 2 else None,
            'created_at': row[3].isoformat() if len(row) > 3 and row[3] else None,
            'updated_at': row[4].isoformat() if len(row) > 4 and row[4] else None,
        }

    def _label_studio_bind_to_json(self, row):
        """将Label-Studio绑定记录转换为JSON格式"""
        if not row:
            return None

        return {
            'id': row[0] if len(row) > 0 else None,
            'kno_id': row[1] if len(row) > 1 else None,
            'label_studio_id': row[2] if len(row) > 2 else None,
            'bind_status': row[3] if len(row) > 3 else None,
            'created_at': row[4].isoformat() if len(row) > 4 and row[4] else None,
            'updated_at': row[5].isoformat() if len(row) > 5 and row[5] else None,
        }

    # 新增：标注任务相关的方法
    def annotation_task_list(self, task_name=None, local_knowledge_id=None, label_studio_env_id=None,
                             question_set_id=None, label_studio_project_id=None,
                             task_status=None):
        """获取标注任务列表"""
        exact_match_fields = ['local_knowledge_id', 'label_studio_env_id', 'question_set_id', 'label_studio_project_id',
                              'task_status']
        partial_match_fields = ['task_name']
        allowed_fileds = exact_match_fields + partial_match_fields
        data = {}
        for ele in allowed_fileds:
            if locals().get(ele):
                data[ele] = locals()[ele]

        query, values = self.gen_select_query("ai_annotation_tasks",
                                              exact_match_fields=exact_match_fields,
                                              partial_match_fields=partial_match_fields,
                                              allowed_fileds=allowed_fileds, **data)
        try:
            return self.execute_query(query, values)
        except Exception as e:
            logger.error(f"获取标注任务列表时发生错误: {str(e)}")
            return []

    def annotation_task_create(self, task_id, task_name, local_knowledge_id, question_set_id,
                               label_studio_env_id, label_studio_project_id=None,
                               total_chunks=0, annotated_chunks=0, task_status='未开始'):
        """创建标注任务"""
        try:
            data = {
                'task_id': task_id,
                'task_name': task_name,
                'local_knowledge_id': local_knowledge_id,
                'question_set_id': question_set_id,
                'label_studio_env_id': label_studio_env_id,
                'label_studio_project_id': label_studio_project_id,
                'total_chunks': total_chunks,
                'annotated_chunks': annotated_chunks,
                'task_status': task_status
            }
            return self.insert('ai_annotation_tasks', data)
        except Exception as e:
            logger.error(f"创建标注任务时发生错误: {str(e)}")
            return False

    def annotation_task_update(self, task_id, task_name=None, task_status=None,
                               total_chunks=None, annotated_chunks=None):
        """更新标注任务"""
        try:
            updates = {}

            if task_name is not None:
                updates['task_name'] = task_name
            if task_status is not None:
                updates['task_status'] = task_status
            if total_chunks is not None:
                updates['total_chunks'] = total_chunks
            if annotated_chunks is not None:
                updates['annotated_chunks'] = annotated_chunks

            if not updates:
                return False

            return self.update('ai_annotation_tasks', updates, task_id=task_id)
        except Exception as e:
            logger.error(f"更新标注任务时发生错误: {str(e)}")
            return False

    def annotation_task_delete(self, task_id):
        """删除标注任务"""
        try:
            return self.delete('ai_annotation_tasks', task_id=task_id)
        except Exception as e:
            logger.error(f"删除标注任务时发生错误: {str(e)}")
            return False

    def annotation_task_count_by_env(self, label_studio_env_id):
        """获取特定环境下标注任务的数量"""
        try:
            query = "SELECT COUNT(*) FROM ai_annotation_tasks WHERE label_studio_env_id = %s"
            result = self.execute_query(query, (label_studio_env_id,))
            return result[0][0] if result else 0
        except Exception as e:
            logger.error(f"获取环境任务数量时发生错误: {str(e)}")
            return 0

    def _annotation_task_to_json(self, row):
        """将标注任务数据库记录转换为JSON格式"""
        if not row:
            return None

        return {
            'task_id': row[0] if len(row) > 0 else None,
            'task_name': row[1] if len(row) > 1 else None,
            'local_knowledge_id': row[2] if len(row) > 2 else None,
            'question_set_id': row[3] if len(row) > 3 else None,
            'label_studio_env_id': row[4] if len(row) > 4 else None,
            'label_studio_project_id': row[5] if len(row) > 5 else None,
            'total_chunks': row[6] if len(row) > 6 else 0,
            'annotated_chunks': row[7] if len(row) > 7 else 0,
            'task_status': row[8] if len(row) > 8 else '未开始',
            'created_at': row[9].isoformat() if len(row) > 9 and row[9] else None,
            'updated_at': row[10].isoformat() if len(row) > 10 and row[10] else None,
        }
