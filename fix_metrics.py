#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复报告问题详情中的指标数据
从MinIO的JSON文件中读取正确的指标并更新到数据库
"""
import json
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.sql_funs.llm_evaluation_report_crud import LLMEvaluationReportManager
from src.sql_funs.llm_evaluation_question_details_crud import LLMEvaluationQuestionDetailsManager
from src.utils.minio_client import get_llm_evaluation_client

def fix_report_metrics(report_id: int):
    """修复指定报告的问题详情指标"""
    print(f"正在修复报告 ID={report_id} 的指标数据...")
    
    # 获取报告信息
    with LLMEvaluationReportManager() as report_manager:
        report = report_manager.get_report_by_id(report_id)
        if not report:
            print(f"报告不存在: ID={report_id}")
            return False
        
        report_path = report.get('report_path')
        print(f"报告路径: {report_path}")
    
    # 从MinIO读取报告JSON
    try:
        client = get_llm_evaluation_client()
        object_name = report_path.lstrip('/')
        data = client.get_file_content(object_name)
        
        if not data:
            print("无法从MinIO读取报告内容")
            return False
        
        report_data = json.loads(data.decode('utf-8'))
        
        # 获取question_metrics
        results = report_data.get('results', {})
        for agent_name, agent_data in results.items():
            question_metrics = agent_data.get('question_metrics', {})
            
            print(f"找到 {len(question_metrics)} 个问题的指标数据")
            
            # 更新数据库
            with LLMEvaluationQuestionDetailsManager() as details_manager:
                updated_count = 0
                
                for qid, metrics in question_metrics.items():
                    # 更新每个问题的指标
                    success = details_manager.update_metrics(
                        report_id=report_id,
                        question_id=str(qid),
                        exact_match=metrics.get('exact_match', 0.0),
                        f1_score=metrics.get('f1_score', 0.0),
                        semantic_similarity=metrics.get('semantic_similarity', 0.0),
                        answer_coverage=metrics.get('answer_coverage', 0.0),
                        answer_relevance=metrics.get('answer_relevance', 0.0),
                        context_utilization=metrics.get('context_utilization', 0.0),
                        answer_completeness=metrics.get('answer_completeness', 0.0),
                        answer_conciseness=metrics.get('answer_conciseness', 0.0)
                    )
                    if success:
                        updated_count += 1
                
                print(f"成功更新 {updated_count} 条记录的指标")
                return updated_count > 0
                
    except Exception as e:
        print(f"修复失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    # 修复报告ID 9
    fix_report_metrics(9)
