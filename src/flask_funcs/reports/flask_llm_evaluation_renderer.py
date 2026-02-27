# -*- coding: utf-8 -*-
"""
LLM评估报告渲染器

用于渲染LLM知识库问答评估报告页面
"""
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from .flask_renderer_base import FlaskHTMLRenderer

logger = logging.getLogger(__name__)


class LLMEvaluationRenderer(FlaskHTMLRenderer):
    """LLM评估报告HTML渲染器"""

    def __init__(self, css_path: Optional[str] = None):
        """
        初始化HTML渲染器

        Args:
            css_path: CSS文件路径
        """
        super().__init__(css_path or "css/qa_management.css")

    def render_evaluation_report(self, evaluation_data: Dict[str, Any], filename: str) -> str:
        """
        渲染LLM评估报告页面

        Args:
            evaluation_data: 评估数据（从JSON文件加载）
            filename: 文件名

        Returns:
            渲染后的HTML内容
        """
        try:
            # 准备模板上下文
            template_context = self._prepare_template_context(evaluation_data, filename)

            # 渲染模板 - 使用Flask的render_template
            html_content = self.render_template('llm_evaluation_report.html', **template_context)
            return html_content

        except Exception as e:
            logger.error(f"LLM评估报告渲染错误: {e}")
            return self._render_error_page(str(e))

    def _prepare_template_context(self, evaluation_data: Dict[str, Any], filename: str) -> Dict[str, Any]:
        """
        准备模板上下文数据

        Args:
            evaluation_data: 评估数据
            filename: 文件名

        Returns:
            模板上下文字典
        """
        summary = evaluation_data.get('evaluation_summary', {})
        results = evaluation_data.get('results', {})

        # 处理每个模型的结果
        model_results = []
        for model_name, result in results.items():
            model_results.append(self._prepare_model_result(model_name, result))

        return {
            'filename': filename,
            'timestamp': summary.get('timestamp', datetime.now().isoformat()),
            'total_agents': summary.get('total_agents', 0),
            'total_qa_pairs': summary.get('total_qa_pairs', 0),
            'model_results': model_results,
        }

    def _prepare_model_result(self, model_name: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        准备单个模型的评估结果

        Args:
            model_name: 模型名称
            result: 模型评估结果

        Returns:
            处理后的模型结果字典
        """
        metrics = result.get('metrics', {})
        config = result.get('model_config', {})
        responses = result.get('responses', [])
        eval_config = result.get('evaluation_config', {})

        # 准备指标数据
        metrics_data = {
            # 基础统计
            'total_samples': metrics.get('total_samples', 0),
            'successful_predictions': metrics.get('successful_predictions', 0),
            'failed_predictions': metrics.get('failed_predictions', 0),
            'success_rate': self._calc_success_rate(metrics),

            # 准确性指标
            'exact_match': self._format_percent(metrics.get('exact_match')),
            'f1_score': self._format_percent(metrics.get('f1_score')),
            'partial_match': self._format_percent(metrics.get('partial_match')),
            'semantic_similarity': self._format_percent(metrics.get('semantic_similarity')),

            # 知识库能力指标
            'answer_coverage': self._format_percent(metrics.get('answer_coverage')),
            'answer_relevance': self._format_percent(metrics.get('answer_relevance')),
            'context_utilization': self._format_percent(metrics.get('context_utilization')),
            'answer_completeness': self._format_percent(metrics.get('answer_completeness')),
            'answer_conciseness': self._format_percent(metrics.get('answer_conciseness')),

            # 效率指标
            'avg_inference_time': self._format_time(metrics.get('avg_inference_time')),
            'total_inference_time': self._format_time(metrics.get('total_inference_time')),
        }

        # 准备问答对详情
        qa_details = []
        for resp in responses:
            qa_details.append({
                'question_id': resp.get('question_id', ''),
                'question': resp.get('question', ''),
                'context': resp.get('context', ''),
                'predicted_answer': resp.get('predicted_answer', ''),
                'ground_truth': resp.get('ground_truth', []),
                'success': resp.get('success', False),
                'inference_time': self._format_time(resp.get('inference_time')),
                'error_message': resp.get('error_message', ''),
                'metadata': resp.get('metadata', {}),  # 包含token使用情况等信息
            })

        # 准备匹配类型配置
        match_types = eval_config.get('match_types', {})
        match_types_display = self._prepare_match_types_display(match_types)

        # 模型配置详情
        model_config = {
            'type': config.get('type', '-'),
            'model': config.get('model', '-'),
            'temperature': config.get('temperature', '-'),
            'max_tokens': config.get('max_tokens', '-'),
            'timeout': config.get('timeout', '-'),
            'api_url': config.get('api_url', '-'),
            'name': config.get('name', '-'),
            'version': config.get('version', '-'),
        }

        return {
            'model_name': model_name,
            'model_version': result.get('model_version', '-'),
            'model_config': model_config,
            'metrics': metrics_data,
            'qa_details': qa_details,
            'evaluation_config': {
                'sample_size': eval_config.get('sample_size', 0),
                'parallel': eval_config.get('parallel', False),
                'retry_attempts': eval_config.get('retry_attempts', 1),
                'match_types': match_types_display,
            },
        }

    def _prepare_match_types_display(self, match_types: Dict[str, Any]) -> List[Dict[str, str]]:
        """准备匹配类型配置的显示数据"""
        display_names = {
            'calculate_exact_match': '精确匹配',
            'calculate_f1_score': 'F1分数',
            'calculate_partial_match': '部分匹配',
            'calculate_semantic_similarity': '语义相似度',
            'calculate_answer_coverage': '答案覆盖率',
            'calculate_answer_relevance': '答案相关性',
            'calculate_context_utilization': '上下文利用率',
            'calculate_completeness': '答案完整性',
            'calculate_conciseness': '答案简洁性',
        }

        result = []
        for key, config in match_types.items():
            if isinstance(config, dict):
                # 获取主要配置项
                config_str = ', '.join([f"{k}={v}" for k, v in config.items() if k != 'description'])
                result.append({
                    'name': display_names.get(key, key),
                    'config': config_str if config_str else '默认配置'
                })
        return result

    def _calc_success_rate(self, metrics: Dict[str, Any]) -> str:
        """计算成功率"""
        total = metrics.get('total_samples', 0)
        successful = metrics.get('successful_predictions', 0)
        if total == 0:
            return '0.00%'
        return f"{successful / total * 100:.2f}%"

    def _format_percent(self, value: Optional[float]) -> str:
        """格式化为百分比"""
        if value is None:
            return '-'
        return f"{value * 100:.2f}%"

    def _format_time(self, value: Optional[float]) -> str:
        """格式化为时间（秒）"""
        if value is None:
            return '-'
        return f"{value:.4f}s"

    def _render_error_page(self, error_message: str) -> str:
        """渲染错误页面"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>错误 - LLM评估报告</title>
            <link rel="stylesheet" href="{self._get_css_url()}">
        </head>
        <body>
            <div class="container">
                <div class="page-header">
                    <h1>渲染错误</h1>
                </div>
                <div class="error-message" style="padding: 20px; background: #f8d7da; border-radius: 8px; color: #721c24;">
                    <p>LLM评估报告渲染失败: {error_message}</p>
                </div>
            </div>
        </body>
        </html>
        """
