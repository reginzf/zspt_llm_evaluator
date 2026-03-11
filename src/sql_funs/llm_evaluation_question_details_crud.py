# -*- coding: utf-8 -*-
"""
LLM评估问题详情CRUD操作模块

用于存储和管理每个问题的详细评估指标
"""
from src.sql_funs.sql_base import PostgreSQLManager
import logging
import json
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class LLMEvaluationQuestionDetailsManager(PostgreSQLManager):
    """LLM评估问题详情管理器"""
    
    TABLE_NAME = "ai_llm_evaluation_question_details"
    
    def __init__(self):
        super().__init__()
    
    def create_detail(
        self,
        report_id: int,
        question_id: str,
        question: str,
        context: str,
        predicted_answer: str,
        ground_truth: List[str],
        success: bool = True,
        inference_time: float = 0.0,
        exact_match: float = 0.0,
        f1_score: float = 0.0,
        semantic_similarity: float = 0.0,
        answer_coverage: float = 0.0,
        answer_relevance: float = 0.0,
        context_utilization: float = 0.0,
        answer_completeness: float = 0.0,
        answer_conciseness: float = 0.0,
        error_message: str = None,
        metadata: Dict = None
    ) -> Optional[int]:
        """
        创建单个问题详情记录
        
        Args:
            report_id: 关联的报告ID
            question_id: 问题ID
            question: 问题文本
            context: 上下文
            predicted_answer: 模型预测答案
            ground_truth: 标准答案列表
            success: 是否成功
            inference_time: 推理时间
            exact_match: 精确匹配率
            f1_score: F1分数
            semantic_similarity: 语义相似度
            answer_coverage: 答案覆盖率
            answer_relevance: 答案相关性
            context_utilization: 上下文利用率
            answer_completeness: 答案完整性
            answer_conciseness: 答案简洁性
            error_message: 错误信息
            metadata: 额外元数据
            
        Returns:
            创建的记录ID，失败返回None
        """
        try:
            data = {
                "report_id": report_id,
                "question_id": question_id,
                "question": question,
                "context": context or "",
                "predicted_answer": predicted_answer,
                "ground_truth": json.dumps(ground_truth) if isinstance(ground_truth, list) else ground_truth,
                "success": success,
                "inference_time": inference_time,
                "exact_match": exact_match,
                "f1_score": f1_score,
                "semantic_similarity": semantic_similarity,
                "answer_coverage": answer_coverage,
                "answer_relevance": answer_relevance,
                "context_utilization": context_utilization,
                "answer_completeness": answer_completeness,
                "answer_conciseness": answer_conciseness,
                "error_message": error_message,
                "metadata": metadata or {}
            }
            
            success = self.insert(self.TABLE_NAME, data)
            if success:
                # 查询获取刚插入的记录的ID
                query = f"""
                    SELECT id FROM {self.TABLE_NAME} 
                    WHERE report_id = %s AND question_id = %s 
                    ORDER BY created_at DESC LIMIT 1
                """
                result = self.execute_query(query, (report_id, question_id))
                if result:
                    detail_id = result[0][0]
                    logger.debug(f"问题详情创建成功: ID={detail_id}")
                    return detail_id
            return None
        except Exception as e:
            logger.error(f"创建问题详情失败: {e}")
            return None
    
    def batch_create_details(
        self,
        report_id: int,
        responses: List[Dict[str, Any]]
    ) -> int:
        """
        批量创建问题详情记录
        
        Args:
            report_id: 关联的报告ID
            responses: 响应列表，每个元素包含问题详情
            
        Returns:
            成功创建的记录数
        """
        success_count = 0
        
        for resp in responses:
            try:
                metrics = resp.get('metrics', {})
                
                detail_id = self.create_detail(
                    report_id=report_id,
                    question_id=str(resp.get('question_id', '')),
                    question=resp.get('question', ''),
                    context=resp.get('context', ''),
                    predicted_answer=resp.get('predicted_answer', ''),
                    ground_truth=resp.get('ground_truth', []),
                    success=resp.get('success', False),
                    inference_time=resp.get('inference_time', 0.0),
                    exact_match=metrics.get('exact_match', 0.0),
                    f1_score=metrics.get('f1_score', 0.0),
                    semantic_similarity=metrics.get('semantic_similarity', 0.0),
                    answer_coverage=metrics.get('answer_coverage', 0.0),
                    answer_relevance=metrics.get('answer_relevance', 0.0),
                    context_utilization=metrics.get('context_utilization', 0.0),
                    answer_completeness=metrics.get('answer_completeness', 0.0),
                    answer_conciseness=metrics.get('answer_conciseness', 0.0),
                    error_message=resp.get('error_message'),
                    metadata=resp.get('metadata', {})
                )
                
                if detail_id:
                    success_count += 1
                    
            except Exception as e:
                logger.error(f"批量创建问题详情时出错: {e}")
                continue
        
        logger.info(f"批量创建问题详情完成: 成功={success_count}/{len(responses)}")
        return success_count
    
    def get_details_by_report_id(
        self,
        report_id: int,
        limit: int = None,
        offset: int = 0,
        order_by: str = None,
        order_desc: bool = True
    ) -> List[Dict[str, Any]]:
        """
        根据报告ID获取问题详情列表
        
        Args:
            report_id: 报告ID
            limit: 返回数量限制
            offset: 偏移量
            order_by: 排序字段
            order_desc: 是否降序
            
        Returns:
            问题详情列表
        """
        try:
            query = f"SELECT * FROM {self.TABLE_NAME} WHERE report_id = %s"
            params = [report_id]
            
            if order_by:
                direction = "DESC" if order_desc else "ASC"
                query += f" ORDER BY {order_by} {direction}"
            else:
                query += " ORDER BY id"
            
            if limit:
                query += f" LIMIT {limit}"
            if offset:
                query += f" OFFSET {offset}"
            
            result = self.execute_query(query, tuple(params))
            if result:
                return [self._row_to_dict(row) for row in result]
            return []
        except Exception as e:
            logger.error(f"获取问题详情列表失败: {e}")
            return []
    
    def get_detail_by_id(self, detail_id: int) -> Optional[Dict[str, Any]]:
        """
        根据ID获取问题详情
        
        Args:
            detail_id: 详情记录ID
            
        Returns:
            问题详情字典，不存在返回None
        """
        try:
            query = f"SELECT * FROM {self.TABLE_NAME} WHERE id = %s"
            result = self.execute_query(query, (detail_id,))
            if result:
                return self._row_to_dict(result[0])
            return None
        except Exception as e:
            logger.error(f"获取问题详情失败: {e}")
            return None
    
    def get_statistics_by_report_id(self, report_id: int) -> Dict[str, Any]:
        """
        获取指定报告的问题详情统计信息
        
        Args:
            report_id: 报告ID
            
        Returns:
            统计信息字典
        """
        try:
            query = f"""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) as success_count,
                    AVG(exact_match) as avg_exact_match,
                    AVG(f1_score) as avg_f1_score,
                    AVG(semantic_similarity) as avg_semantic_similarity,
                    AVG(answer_coverage) as avg_answer_coverage,
                    AVG(answer_relevance) as avg_answer_relevance,
                    AVG(context_utilization) as avg_context_utilization,
                    AVG(answer_completeness) as avg_answer_completeness,
                    AVG(answer_conciseness) as avg_answer_conciseness,
                    AVG(inference_time) as avg_inference_time,
                    MIN(f1_score) as min_f1_score,
                    MAX(f1_score) as max_f1_score,
                    MIN(exact_match) as min_exact_match,
                    MAX(exact_match) as max_exact_match,
                    MIN(semantic_similarity) as min_semantic_similarity,
                    MAX(semantic_similarity) as max_semantic_similarity
                FROM {self.TABLE_NAME}
                WHERE report_id = %s
            """
            
            result = self.execute_query(query, (report_id,))
            if result and result[0]:
                row = result[0]
                return {
                    'total': row[0] or 0,
                    'success_count': row[1] or 0,
                    'avg_exact_match': float(row[2]) if row[2] else 0.0,
                    'avg_f1_score': float(row[3]) if row[3] else 0.0,
                    'avg_semantic_similarity': float(row[4]) if row[4] else 0.0,
                    'avg_answer_coverage': float(row[5]) if row[5] else 0.0,
                    'avg_answer_relevance': float(row[6]) if row[6] else 0.0,
                    'avg_context_utilization': float(row[7]) if row[7] else 0.0,
                    'avg_answer_completeness': float(row[8]) if row[8] else 0.0,
                    'avg_answer_conciseness': float(row[9]) if row[9] else 0.0,
                    'avg_inference_time': float(row[10]) if row[10] else 0.0,
                    'min_f1_score': float(row[11]) if row[11] else 0.0,
                    'max_f1_score': float(row[12]) if row[12] else 0.0,
                    'min_exact_match': float(row[13]) if row[13] else 0.0,
                    'max_exact_match': float(row[14]) if row[14] else 0.0,
                    'min_semantic_similarity': float(row[15]) if row[15] else 0.0,
                    'max_semantic_similarity': float(row[16]) if row[16] else 0.0,
                }
            return {}
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}
    
    def get_best_worst_questions(
        self,
        report_id: int,
        metric: str = 'f1_score',
        top_n: int = 10
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        获取最佳和最差表现的问题
        
        Args:
            report_id: 报告ID
            metric: 排序指标
            top_n: 返回数量
            
        Returns:
            {"best": [...], "worst": [...]}
        """
        try:
            # 验证指标字段有效性
            valid_metrics = [
                'exact_match', 'f1_score', 'semantic_similarity',
                'answer_coverage', 'answer_relevance', 'context_utilization',
                'answer_completeness', 'answer_conciseness'
            ]
            if metric not in valid_metrics:
                metric = 'f1_score'
            
            # 获取最佳
            best_query = f"""
                SELECT * FROM {self.TABLE_NAME}
                WHERE report_id = %s
                ORDER BY {metric} DESC
                LIMIT %s
            """
            best_result = self.execute_query(best_query, (report_id, top_n))
            best_list = [self._row_to_dict(row) for row in best_result] if best_result else []
            
            # 获取最差
            worst_query = f"""
                SELECT * FROM {self.TABLE_NAME}
                WHERE report_id = %s
                ORDER BY {metric} ASC
                LIMIT %s
            """
            worst_result = self.execute_query(worst_query, (report_id, top_n))
            worst_list = [self._row_to_dict(row) for row in worst_result] if worst_result else []
            
            return {
                'best': best_list,
                'worst': worst_list
            }
        except Exception as e:
            logger.error(f"获取最佳/最差问题失败: {e}")
            return {'best': [], 'worst': []}
    
    def filter_questions(
        self,
        report_id: int,
        metric: str = None,
        min_value: float = None,
        max_value: float = None,
        success_only: bool = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        根据条件筛选问题
        
        Args:
            report_id: 报告ID
            metric: 指标字段名
            min_value: 最小值
            max_value: 最大值
            success_only: 是否只返回成功的
            limit: 返回数量限制
            
        Returns:
            符合条件的问题列表
        """
        try:
            query = f"SELECT * FROM {self.TABLE_NAME} WHERE report_id = %s"
            params = [report_id]
            
            if metric and (min_value is not None or max_value is not None):
                if min_value is not None:
                    query += f" AND {metric} >= %s"
                    params.append(min_value)
                if max_value is not None:
                    query += f" AND {metric} <= %s"
                    params.append(max_value)
            
            if success_only is not None:
                query += " AND success = %s"
                params.append(success_only)
            
            if metric:
                query += f" ORDER BY {metric} DESC"
            else:
                query += " ORDER BY id"
            
            query += f" LIMIT {limit}"
            
            result = self.execute_query(query, tuple(params))
            if result:
                return [self._row_to_dict(row) for row in result]
            return []
        except Exception as e:
            logger.error(f"筛选问题失败: {e}")
            return []
    
    def delete_by_report_id(self, report_id: int) -> bool:
        """
        根据报告ID删除所有相关问题详情
        
        Args:
            report_id: 报告ID
            
        Returns:
            是否成功
        """
        try:
            query = f"DELETE FROM {self.TABLE_NAME} WHERE report_id = %s"
            self.cursor.execute(query, (report_id,))
            self.connection.commit()
            logger.info(f"已删除报告 {report_id} 的所有问题详情")
            return True
        except Exception as e:
            logger.error(f"删除问题详情失败: {e}")
            self.connection.rollback()
            return False
    
    def update_metrics(
        self,
        report_id: int,
        question_id: str,
        exact_match: float = 0.0,
        f1_score: float = 0.0,
        semantic_similarity: float = 0.0,
        answer_coverage: float = 0.0,
        answer_relevance: float = 0.0,
        context_utilization: float = 0.0,
        answer_completeness: float = 0.0,
        answer_conciseness: float = 0.0
    ) -> bool:
        """
        更新问题详情的指标数据
        
        Args:
            report_id: 报告ID
            question_id: 问题ID
            exact_match: 精确匹配率
            f1_score: F1分数
            semantic_similarity: 语义相似度
            answer_coverage: 答案覆盖率
            answer_relevance: 答案相关性
            context_utilization: 上下文利用率
            answer_completeness: 答案完整性
            answer_conciseness: 答案简洁性
            
        Returns:
            是否成功
        """
        try:
            query = f"""
                UPDATE {self.TABLE_NAME} SET
                    exact_match = %s,
                    f1_score = %s,
                    semantic_similarity = %s,
                    answer_coverage = %s,
                    answer_relevance = %s,
                    context_utilization = %s,
                    answer_completeness = %s,
                    answer_conciseness = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE report_id = %s AND question_id = %s
            """
            self.cursor.execute(query, (
                exact_match, f1_score, semantic_similarity,
                answer_coverage, answer_relevance, context_utilization,
                answer_completeness, answer_conciseness,
                report_id, question_id
            ))
            self.connection.commit()
            return self.cursor.rowcount > 0
        except Exception as e:
            logger.error(f"更新问题指标失败: {e}")
            self.connection.rollback()
            return False
    
    def _row_to_dict(self, row) -> Dict[str, Any]:
        """将数据库行转换为字典"""
        from decimal import Decimal
        
        columns = [
            'id', 'report_id', 'question_id', 'question', 'context',
            'predicted_answer', 'ground_truth', 'success', 'inference_time',
            'exact_match', 'f1_score', 'semantic_similarity',
            'answer_coverage', 'answer_relevance', 'context_utilization',
            'answer_completeness', 'answer_conciseness',
            'error_message', 'metadata', 'created_at', 'updated_at'
        ]
        
        result = {}
        for i, col in enumerate(columns):
            if i < len(row):
                value = row[i]
                # 处理JSONB字段
                if col in ['ground_truth', 'metadata'] and isinstance(value, str):
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
