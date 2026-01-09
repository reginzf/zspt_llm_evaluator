from src.sql_funs.sql_base import PostgreSQLManager
import logging

logger = logging.getLogger(__name__)


class LabelStudioCrud(PostgreSQLManager):


    def label_studio_list(self):
        """获取所有Label-Studio环境列表"""
        try:
            query = "SELECT * FROM ai_label_studio_info ORDER BY created_at DESC"
            return self.fetch_all(query)
        except Exception as e:
            logger.error(f"获取Label-Studio环境列表时发生错误: {str(e)}")
            return []

    def label_studio_get_by_id(self, label_studio_id):
        """根据ID获取特定Label-Studio环境信息"""
        try:
            query = "SELECT * FROM ai_label_studio_info WHERE label_studio_id = %s"
            result = self.fetch_one(query, (label_studio_id,))
            return result
        except Exception as e:
            logger.error(f"获取Label-Studio环境信息时发生错误: {str(e)}")
            return None

    def label_studio_insert(self, label_studio_id, label_studio_url, label_studio_api_key):
        """插入Label-Studio环境信息"""
        try:
            query = """
                INSERT INTO ai_label_studio_info (label_studio_id, label_studio_url, label_studio_api_key)
                VALUES (%s, %s, %s)
            """
            result = self.execute_query(query, (label_studio_id, label_studio_url, label_studio_api_key))
            return result
        except Exception as e:
            logger.error(f"插入Label-Studio环境信息时发生错误: {str(e)}")
            return False

    def label_studio_update(self, label_studio_id, label_studio_url=None, label_studio_api_key=None):
        """更新Label-Studio环境信息"""
        try:
            updates = []
            params = []
            
            if label_studio_url:
                updates.append("label_studio_url = %s")
                params.append(label_studio_url)
            if label_studio_api_key:
                updates.append("label_studio_api_key = %s")
                params.append(label_studio_api_key)
            
            if not updates:
                return False
                
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.extend([label_studio_id])
            
            query = f"UPDATE ai_label_studio_info SET {', '.join(updates)} WHERE label_studio_id = %s"
            result = self.execute_query(query, params)
            return result
        except Exception as e:
            logger.error(f"更新Label-Studio环境信息时发生错误: {str(e)}")
            return False

    def label_studio_delete(self, label_studio_id):
        """删除Label-Studio环境信息"""
        try:
            query = "DELETE FROM ai_label_studio_info WHERE label_studio_id = %s"
            result = self.execute_query(query, (label_studio_id,))
            return result
        except Exception as e:
            logger.error(f"删除Label-Studio环境信息时发生错误: {str(e)}")
            return False

    def label_studio_bind_list(self):
        """获取所有Label-Studio绑定关系列表"""
        try:
            query = """
                SELECT b.*, e.label_studio_url, k.knowledge_name 
                FROM ai_label_studio_bind b
                LEFT JOIN ai_label_studio_info e ON b.label_studio_id = e.label_studio_id
                LEFT JOIN ai_knowledge_base k ON b.knowledge_id = k.knowledge_id
                ORDER BY b.created_at DESC
            """
            return self.fetch_all(query)
        except Exception as e:
            logger.error(f"获取Label-Studio绑定关系列表时发生错误: {str(e)}")
            return []

    def label_studio_bind_get(self, kno_id=None, label_studio_id=None):
        """获取Label-Studio绑定关系"""
        try:
            query = "SELECT * FROM ai_label_studio_bind WHERE 1=1"
            params = []
            
            if kno_id:
                query += " AND kno_id = %s"
                params.append(kno_id)
            if label_studio_id:
                query += " AND label_studio_id = %s"
                params.append(label_studio_id)
                
            return self.fetch_all(query, tuple(params))
        except Exception as e:
            logger.error(f"获取Label-Studio绑定关系时发生错误: {str(e)}")
            return []

    def label_studio_bind_create(self, kno_id, label_studio_id, bind_status=2):
        """创建Label-Studio绑定关系"""
        try:
            query = """
                INSERT INTO ai_label_studio_bind (kno_id, label_studio_id, bind_status)
                VALUES (%s, %s, %s)
            """
            result = self.execute_query(query, (kno_id, label_studio_id, bind_status))
            return result
        except Exception as e:
            logger.error(f"创建Label-Studio绑定关系时发生错误: {str(e)}")
            return False

    def label_studio_bind_update(self, kno_id, label_studio_id, bind_status=None):
        """更新Label-Studio绑定关系"""
        try:
            updates = []
            params = []
            
            if bind_status is not None:
                updates.append("bind_status = %s")
                params.append(bind_status)
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.extend([kno_id, label_studio_id])
            
            query = "UPDATE ai_label_studio_bind SET " + ", ".join(updates) + " WHERE kno_id = %s AND label_studio_id = %s"
            result = self.execute_query(query, params)
            return result
        except Exception as e:
            logger.error(f"更新Label-Studio绑定关系时发生错误: {str(e)}")
            return False

    def label_studio_bind_delete(self, kno_id, label_studio_id):
        """删除Label-Studio绑定关系"""
        try:
            query = "DELETE FROM ai_label_studio_bind WHERE kno_id = %s AND label_studio_id = %s"
            result = self.execute_query(query, (kno_id, label_studio_id))
            return result
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
    def annotation_task_list(self, local_knowledge_id=None, label_studio_env_id=None):
        """获取标注任务列表"""
        try:
            query = """
                SELECT * FROM ai_annotation_tasks 
                WHERE 1=1
            """
            params = []
            
            if local_knowledge_id:
                query += " AND local_knowledge_id = %s"
                params.append(local_knowledge_id)
            if label_studio_env_id:
                query += " AND label_studio_env_id = %s"
                params.append(label_studio_env_id)
                
            query += " ORDER BY created_at DESC"
            return self.fetch_all(query, tuple(params))
        except Exception as e:
            logger.error(f"获取标注任务列表时发生错误: {str(e)}")
            return []

    def annotation_task_get_by_id(self, task_id):
        """根据ID获取特定标注任务"""
        try:
            query = "SELECT * FROM ai_annotation_tasks WHERE task_id = %s"
            result = self.fetch_one(query, (task_id,))
            return result
        except Exception as e:
            logger.error(f"获取标注任务信息时发生错误: {str(e)}")
            return None

    def annotation_task_create(self, task_id, task_name, local_knowledge_id, question_set_id, 
                              label_studio_env_id, label_studio_project_id=None, 
                              total_chunks=0, annotated_chunks=0, task_status='未开始'):
        """创建标注任务"""
        try:
            query = """
                INSERT INTO ai_annotation_tasks (
                    task_id, task_name, local_knowledge_id, question_set_id,
                    label_studio_env_id, label_studio_project_id, total_chunks,
                    annotated_chunks, task_status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            result = self.execute_query(query, (
                task_id, task_name, local_knowledge_id, question_set_id,
                label_studio_env_id, label_studio_project_id, total_chunks,
                annotated_chunks, task_status
            ))
            return result
        except Exception as e:
            logger.error(f"创建标注任务时发生错误: {str(e)}")
            return False

    def annotation_task_update(self, task_id, task_name=None, task_status=None, 
                               total_chunks=None, annotated_chunks=None, 
                               label_studio_project_id=None):
        """更新标注任务"""
        try:
            updates = []
            params = []
            
            if task_name is not None:
                updates.append("task_name = %s")
                params.append(task_name)
            if task_status is not None:
                updates.append("task_status = %s")
                params.append(task_status)
            if total_chunks is not None:
                updates.append("total_chunks = %s")
                params.append(total_chunks)
            if annotated_chunks is not None:
                updates.append("annotated_chunks = %s")
                params.append(annotated_chunks)
            if label_studio_project_id is not None:
                updates.append("label_studio_project_id = %s")
                params.append(label_studio_project_id)
            
            if not updates:
                return False
                
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(task_id)
            
            query = "UPDATE ai_annotation_tasks SET " + ", ".join(updates) + " WHERE task_id = %s"
            result = self.execute_query(query, params)
            return result
        except Exception as e:
            logger.error(f"更新标注任务时发生错误: {str(e)}")
            return False

    def annotation_task_delete(self, task_id):
        """删除标注任务"""
        try:
            query = "DELETE FROM ai_annotation_tasks WHERE task_id = %s"
            result = self.execute_query(query, (task_id,))
            return result
        except Exception as e:
            logger.error(f"删除标注任务时发生错误: {str(e)}")
            return False

    def annotation_task_get_by_env_and_knowledge(self, label_studio_env_id, local_knowledge_id):
        """获取特定环境和知识库下的标注任务"""
        try:
            query = """
                SELECT * FROM ai_annotation_tasks 
                WHERE label_studio_env_id = %s AND local_knowledge_id = %s
                ORDER BY created_at DESC
            """
            return self.fetch_all(query, (label_studio_env_id, local_knowledge_id))
        except Exception as e:
            logger.error(f"获取环境和知识库下的标注任务时发生错误: {str(e)}")
            return []

    def annotation_task_count_by_env(self, label_studio_env_id):
        """获取特定环境下标注任务的数量"""
        try:
            query = "SELECT COUNT(*) FROM ai_annotation_tasks WHERE label_studio_env_id = %s"
            result = self.fetch_one(query, (label_studio_env_id,))
            return result[0] if result else 0
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