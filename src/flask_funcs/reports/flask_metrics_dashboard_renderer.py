import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from .flask_renderer_base import FlaskHTMLRenderer
TYPE_DISPLAY_NAMES = {
    "factual": "事实型",
    "contextual": "上下文型",
    "conceptual": "概念型",
    "reasoning": "推理型",
    "application": "应用型"
}

class MetricsDashboardRenderer(FlaskHTMLRenderer):


    def __init__(self, css_path: Optional[str] = None):
        """
        初始化HTML渲染器

        Args:
            css_path: CSS文件路径
        """
        # 调用父类初始化
        super().__init__(css_path or "css/styles.css")

    def render_metrics_dashboard(self, analysis_results: Dict[str, Any], metric_data) -> str:
        """
        渲染指标仪表板页面

        Args:
            analysis_results: 分析结果
            metric_data: 原始指标数据

        Returns:
            渲染后的HTML内容
        """
        try:
            # 准备模板上下文
            template_context = self._prepare_template_context(analysis_results)

            # 添加可视化数据
            visualize_data = self._prepare_visualize_data(metric_data)
            template_context["visualize_data"] = visualize_data

            # 添加JavaScript文件URL
            template_context["js_url"] = self._get_js_url("metrics_dashboard.js")

            # 渲染模板
            html_content = self.render_template(
                'metrics_dashboard_flask.html',
                **template_context
            )
            return html_content

        except Exception as e:
            logging.error(f"Flask渲染错误: {e}")
            # 返回简单的错误页面
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>错误</title>
                <link rel="stylesheet" href="{self._get_css_url()}">
            </head>
            <body>
                <div class="container">
                    <h1>渲染错误</h1>
                    <p>指标仪表板渲染失败: {str(e)}</p>
                </div>
            </body>
            </html>
            """

    def _prepare_visualize_data(self, metric_all: Dict[str, Any]) -> Dict[str, Any]:
        """
        准备可视化数据

        Args:
            metric_all: 原始指标数据

        Returns:
            可视化数据字典
        """
        try:
            # 导入MetricsVisualizer
            from .visualize_metrics import MetricsVisualizer

            # 创建可视化器
            visualizer = MetricsVisualizer(metric_all)

            # 生成交互式仪表板HTML（不保存文件）
            plotly_html = visualizer.create_interactive_dashboard(save_to_html=False)

            # 准备可视化数据
            visualize_data = {
                "plotly_html": plotly_html,
                "has_visualization": True,
                "question_count": len(metric_all),
                "available_metrics": [
                    "precision", "recall", "f1_score", "average_precision",
                    "ndcg", "mrr", "hit_rate", "coverage"
                ]
            }

            return visualize_data

        except Exception as e:
            logging.error(f"准备可视化数据时出错: {e}")
            return {
                "plotly_html": "<div class='visualization-error'>可视化数据生成失败</div>",
                "has_visualization": False,
                "question_count": 0,
                "available_metrics": []
            }

    def _prepare_template_context(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        准备模板上下文数据

        Args:
            analysis_results: 分析结果

        Returns:
            模板上下文字典
        """
        return {
            "timestamp": self._prepare_timestamp(),
            "question_count": self._prepare_question_count(analysis_results),
            "avg_precision": self._prepare_avg_precision(analysis_results),
            "avg_recall": self._prepare_avg_recall(analysis_results),
            "avg_f1_score": self._prepare_avg_f1_score(analysis_results),
            "avg_f1": self._prepare_avg_f1(analysis_results),
            "avg_ndcg": self._prepare_avg_ndcg(analysis_results),
            "avg_mrr": self._prepare_avg_mrr(analysis_results),
            "avg_hit_rate": self._prepare_avg_hit_rate(analysis_results),
            "avg_coverage": self._prepare_avg_coverage(analysis_results),
            "avg_redundancy": self._prepare_avg_redundancy(analysis_results),
            "metrics_data": self._prepare_chart_data(analysis_results),
            "questions": self._prepare_question_data(analysis_results),
            "summary": self._prepare_summary(analysis_results),
            "distribution": self._prepare_distribution(analysis_results),
            "top_performers": self._prepare_top_performers(analysis_results),
            "top_k_analysis": self._prepare_top_k_analysis(analysis_results),
            "correlation_matrix": self._prepare_correlation_matrix(analysis_results),
            "performance_ranking": self._prepare_performance_ranking(analysis_results)
        }

    def _prepare_timestamp(self) -> str:
        """准备时间戳"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _prepare_question_count(self, analysis_results: Dict[str, Any]) -> int:
        """准备问题数量"""
        summary = analysis_results.get("summary", {})
        return summary.get("total_questions", 0)

    def _prepare_avg_precision(self, analysis_results: Dict[str, Any]) -> float:
        """准备平均精确度"""
        summary = analysis_results.get("summary", {})
        return summary.get("avg_precision", 0) * 100

    def _prepare_avg_recall(self, analysis_results: Dict[str, Any]) -> float:
        """准备平均召回率"""
        summary = analysis_results.get("summary", {})
        return summary.get("avg_recall", 0) * 100

    def _prepare_avg_f1_score(self, analysis_results: Dict[str, Any]) -> float:
        """准备平均F1分数"""
        summary = analysis_results.get("summary", {})
        return summary.get("avg_f1_score", 0) * 100

    def _prepare_avg_f1(self, analysis_results: Dict[str, Any]) -> float:
        """准备平均F1分数（别名）"""
        summary = analysis_results.get("summary", {})
        return summary.get("avg_f1_score", 0) * 100

    def _prepare_avg_ndcg(self, analysis_results: Dict[str, Any]) -> float:
        """准备平均NDCG"""
        summary = analysis_results.get("summary", {})
        return summary.get("avg_ndcg", 0) * 100

    def _prepare_avg_mrr(self, analysis_results: Dict[str, Any]) -> float:
        """准备平均MRR"""
        summary = analysis_results.get("summary", {})
        return summary.get("avg_mrr", 0) * 100

    def _prepare_avg_hit_rate(self, analysis_results: Dict[str, Any]) -> float:
        """准备平均命中率"""
        summary = analysis_results.get("summary", {})
        return summary.get("avg_hit_rate", 0) * 100

    def _prepare_avg_coverage(self, analysis_results: Dict[str, Any]) -> float:
        """准备平均覆盖率"""
        summary = analysis_results.get("summary", {})
        return summary.get("avg_coverage", 0) * 100

    def _prepare_avg_redundancy(self, analysis_results: Dict[str, Any]) -> float:
        """准备平均冗余度"""
        summary = analysis_results.get("summary", {})
        return summary.get("avg_redundancy", 0) * 100

    def _prepare_summary(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """准备摘要数据"""
        return analysis_results.get("summary", {})

    def _prepare_distribution(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """准备分布数据"""
        return analysis_results.get("distribution", {})

    def _prepare_top_performers(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """准备最佳表现者数据"""
        return analysis_results.get("top_performers", {})

    def _prepare_top_k_analysis(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """准备Top-K分析数据"""
        return analysis_results.get("top_k_analysis", {})

    def _prepare_correlation_matrix(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """准备相关性矩阵数据"""
        return analysis_results.get("correlation_matrix", {}) or {}

    def _prepare_performance_ranking(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """准备性能排名数据"""
        return analysis_results.get("performance_ranking", [])

    def _prepare_chart_data(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        准备图表数据

        Args:
            analysis_results: 分析结果

        Returns:
            图表数据字典
        """
        summary = analysis_results.get("summary", {})
        top_k_analysis = analysis_results.get("top_k_analysis", {})
        performance_ranking = analysis_results.get("performance_ranking", [])

        # Top K标签和数据
        top_k_labels = []
        avg_precision_at_k = []
        avg_recall_at_k = []

        if "precision" in top_k_analysis:
            for k in sorted(top_k_analysis["precision"].keys(), key=int):
                top_k_labels.append(f"@{k}")
                avg_precision_at_k.append(top_k_analysis["precision"][k].get("mean", 0))

        if "recall" in top_k_analysis:
            for k in sorted(top_k_analysis["recall"].keys(), key=int):
                avg_recall_at_k.append(top_k_analysis["recall"][k].get("mean", 0))

        # F1分数分布 - 基于performance_ranking计算
        f1_distribution_labels = ["差 (<0.4)", "中 (0.4-0.7)", "好 (>0.7)"]
        f1_distribution_data = [0, 0, 0]

        for item in performance_ranking:
            f1_score = item.get("f1_score", 0)
            if f1_score < 0.4:
                f1_distribution_data[0] += 1
            elif f1_score <= 0.7:
                f1_distribution_data[1] += 1
            else:
                f1_distribution_data[2] += 1

        # 相关性数据 - 基于performance_ranking计算准确率和召回率的相关性
        correlation_data = []
        for item in performance_ranking:
            precision = item.get("precision", 0)
            recall = item.get("recall", 0)
            question = item.get("question", "")
            if precision > 0 and recall > 0:  # 只添加有效数据
                correlation_data.append({
                    "x": precision,
                    "y": recall,
                    "label": question[:30] + "..." if len(question) > 30 else question
                })

        return {
            "top_k_labels": top_k_labels,
            "avg_precision_at_k": avg_precision_at_k,
            "avg_recall_at_k": avg_recall_at_k,
            "f1_distribution_labels": f1_distribution_labels,
            "f1_distribution_data": f1_distribution_data,
            "avg_average_precision": summary.get("avg_average_precision", 0),
            "avg_ndcg": summary.get("avg_ndcg", 0),
            "avg_mrr": summary.get("avg_mrr", 0),
            "avg_hit_rate": summary.get("avg_hit_rate", 0),
            "avg_coverage": summary.get("avg_coverage", 0),
            "correlation_data": correlation_data
        }

    def _prepare_question_data(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        准备问题数据

        Args:
            analysis_results: 分析结果

        Returns:
            问题数据列表
        """
        questions = []
        performance_ranking = analysis_results.get("performance_ranking", [])

        for item in performance_ranking[:20]:  # 只取前20个
            question_data = {
                "text": item.get("question", ""),
                "metrics": {
                    "q_type": TYPE_DISPLAY_NAMES[item.get("q_type", "")],
                    "precision": item.get("precision", 0),
                    "recall": item.get("recall", 0),
                    "f1_score": item.get("f1_score", 0),
                    "ndcg": item.get("ndcg", 0),
                    "mrr": item.get("mrr", 0)
                }
            }
            questions.append(question_data)

        return questions