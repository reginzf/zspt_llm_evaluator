# -*- coding: utf-8 -*-
"""
LLM评估报告管理CRUD操作模块
"""
from src.sql_funs.sql_base import PostgreSQLManager
import logging
import json

logger = logging.getLogger(__name__)


class LLMEvaluationReportManager(PostgreSQLManager):
    """LLM评估报告管理器"""
    
    TABLE_NAME = "ai_llm_evaluation_reports"
    
    def __init__(self):
        super().__init__()
    
    def create_report(self, report_name, model_name, model_id,
                      group_id, group_name, report_path,
                      qa_count=0, qa_offset=0, qa_limit=0,
                      exact_match=None, f1_score=None,
                      semantic_similarity=None, avg_inference_time=None,
                      evaluation_config=None, status='completed',
                      error_message=None):
        """创建评估报告记录"""
        try:
            data = {
                "report_name": report_name,
                "model_name": model_name,
                "model_id": model_id,
                "group_id": group_id,
                "group_name": group_name,
                "report_path": report_path,
                "qa_count": qa_count,
                "qa_offset": qa_offset,
                "qa_limit": qa_limit,
                "exact_match": exact_match,
                "f1_score": f1_score,
                "semantic_similarity": semantic_similarity,
                "avg_inference_time": avg_inference_time,
                "evaluation_config": evaluation_config or {},
                "status": status,
                "error_message": error_message
            }
            
            # 插入数据
            success = self.insert(self.TABLE_NAME, data)
            if success:
                # 查询获取刚插入的记录的ID
                query = f"SELECT id FROM {self.TABLE_NAME} WHERE report_name = %s ORDER BY created_at DESC LIMIT 1"
                result = self.execute_query(query, (report_name,))
                if result:
                    report_id = result[0][0]
                    logger.info(f"评估报告创建成功: ID={report_id}, name={report_name}")
                    return report_id
            return None
        except Exception as e:
            logger.error(f"创建评估报告失败: {e}")
            return None
    
    def get_report_by_id(self, report_id):
        """根据ID获取报告"""
        try:
            query = f"SELECT * FROM {self.TABLE_NAME} WHERE id = %s"
            result = self.execute_query(query, (report_id,))
            if result:
                return self._row_to_dict(result[0])
            return None
        except Exception as e:
            logger.error(f"获取报告失败: {e}")
            return None
    
    def list_reports(self, model_name=None, group_id=None,
                     status=None, limit=None, offset=0):
        """获取报告列表"""
        try:
            conditions = []
            params = []
            
            if model_name:
                conditions.append("model_name = %s")
                params.append(model_name)
            if group_id:
                conditions.append("group_id = %s")
                params.append(group_id)
            if status:
                conditions.append("status = %s")
                params.append(status)
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            query = f"SELECT * FROM {self.TABLE_NAME} WHERE {where_clause} ORDER BY created_at DESC"
            
            if limit:
                query += f" LIMIT {limit}"
            if offset:
                query += f" OFFSET {offset}"
            
            result = self.execute_query(query, tuple(params) if params else None)
            if result:
                return [self._row_to_dict(row) for row in result]
            return []
        except Exception as e:
            logger.error(f"获取报告列表失败: {e}")
            return []
    
    def count_reports(self, model_name=None, group_id=None, status=None):
        """统计报告数量"""
        try:
            conditions = []
            params = []
            
            if model_name:
                conditions.append("model_name = %s")
                params.append(model_name)
            if group_id:
                conditions.append("group_id = %s")
                params.append(group_id)
            if status:
                conditions.append("status = %s")
                params.append(status)
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            query = f"SELECT COUNT(*) FROM {self.TABLE_NAME} WHERE {where_clause}"
            
            result = self.execute_query(query, tuple(params) if params else None)
            return result[0][0] if result else 0
        except Exception as e:
            logger.error(f"统计报告数量失败: {e}")
            return 0
    
    def delete_report(self, report_id):
        """删除报告记录"""
        try:
            query = f"DELETE FROM {self.TABLE_NAME} WHERE id = %s"
            self.cursor.execute(query, (report_id,))
            self.connection.commit()
            logger.info(f"报告删除成功: ID={report_id}")
            return True
        except Exception as e:
            logger.error(f"删除报告失败: {e}")
            self.connection.rollback()
            return False
    
    def _row_to_dict(self, row):
        """将数据库行转换为字典"""
        from decimal import Decimal
        
        columns = [
            'id', 'report_name', 'model_name', 'model_id', 'group_id', 'group_name',
            'report_path', 'qa_count', 'qa_offset', 'qa_limit',
            'exact_match', 'f1_score', 'semantic_similarity', 'avg_inference_time',
            'evaluation_config', 'status', 'error_message', 'created_at', 'updated_at'
        ]
        
        result = {}
        for i, col in enumerate(columns):
            if i < len(row):
                value = row[i]
                # 处理JSONB字段
                if col == 'evaluation_config' and isinstance(value, str):
                    try:
                        value = json.loads(value)
                    except:
                        pass
                # 处理时间戳
                elif col in ['created_at', 'updated_at'] and hasattr(value, 'isoformat'):
                    value = value.isoformat()
                # 处理Decimal类型
                elif isinstance(value, Decimal):
                    value = float(value)
                result[col] = value
        return result
