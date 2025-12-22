"""
HTML报告渲染器模块
使用Jinja2模板引擎生成美观的HTML报告
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape

    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    print("警告: Jinja2未安装，将使用备用HTML生成方式")
    print("请安装: pip install jinja2")

METRIC_TEMPLATE_NAME = 'metrics_dashboard.html'


class HTMLRenderer:
    """HTML报告渲染器"""

    def __init__(self, template_dir: Optional[str] = None, css_dir: Optional[str] = None):
        """
        初始化HTML渲染器
        
        Args:
            template_dir: 模板目录路径，如果为None则使用默认目录
            css_dir: CSS目录路径，如果为None则使用默认目录
        """
        self.template_dir = template_dir or str(Path(__file__).parent / "templates")
        self.css_dir = css_dir or str(Path(__file__).parent / "css")
        self.css_path = Path(self.css_dir) / 'styles.css'

        if JINJA2_AVAILABLE:
            self.env = Environment(
                loader=FileSystemLoader(self.template_dir),
                autoescape=select_autoescape(['html', 'xml']),
                trim_blocks=True,
                lstrip_blocks=True
            )

            # 添加自定义过滤器
            self.env.filters['round'] = lambda x, n=2: round(x, n) if isinstance(x, (int, float)) else x
        else:
            self.env = None

    def render_metrics_dashboard(self, analysis_results: Dict[str, Any]) -> str:
        """
        使用Jinja2渲染模板
        
        Args:
            analysis_results: 模板上下文
            
        Returns:
            渲染后的HTML内容
        """
        try:
            template = self.env.get_template(METRIC_TEMPLATE_NAME)

            # 准备模板上下文
            template_context = self._prepare_template_context(analysis_results)

            # 添加CSS路径
            template_context["css_path"] = self.css_path

            # 渲染模板
            html_content = template.render(**template_context)
            return html_content

        except Exception as e:
            print(f"Jinja2渲染错误: {e}")
            raise e

    def _prepare_template_context(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        准备模板上下文数据
        
        Args:
            analysis_results: 分析结果
            
        Returns:
            模板上下文字典
        """
        summary = analysis_results.get("summary", {})
        distribution = analysis_results.get("distribution", {})
        top_performers = analysis_results.get("top_performers", {})
        top_k_analysis = analysis_results.get("top_k_analysis", {})
        correlation_matrix = analysis_results.get("correlation_matrix", {})
        performance_ranking = analysis_results.get("performance_ranking", [])

        # 准备图表数据
        metrics_data = self._prepare_chart_data(analysis_results)

        # 准备问题数据
        questions = self._prepare_question_data(analysis_results)

        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "question_count": summary.get("total_questions", 0),
            "avg_precision": summary.get("avg_precision", 0) * 100,
            "avg_recall": summary.get("avg_recall", 0) * 100,
            "avg_f1_score": summary.get("avg_f1_score", 0) * 100,
            "avg_f1": summary.get("avg_f1_score", 0) * 100,
            "avg_ndcg": summary.get("avg_ndcg", 0) * 100,
            "avg_mrr": summary.get("avg_mrr", 0) * 100,
            "avg_hit_rate": summary.get("avg_hit_rate", 0) * 100,
            "avg_coverage": summary.get("avg_coverage", 0) * 100,
            "avg_redundancy": summary.get("avg_redundancy", 0) * 100,
            "metrics_data": metrics_data,
            "questions": questions,
            "summary": summary,
            "distribution": distribution,
            "top_performers": top_performers,
            "top_k_analysis": top_k_analysis,
            "correlation_matrix": correlation_matrix or {},
            "performance_ranking": performance_ranking
        }

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
                    "precision": item.get("precision", 0),
                    "recall": item.get("recall", 0),
                    "f1_score": item.get("f1_score", 0),
                    "ndcg": item.get("ndcg", 0),
                    "mrr": item.get("mrr", 0)
                }
            }
            questions.append(question_data)

        return questions


# 兼容性函数
def generate_html_report(analysis_results: Dict[str, Any]) -> str:
    """
    
    Args:
        analysis_results: analyze_metrics函数返回的分析结果
        
    Returns:
        HTML报告内容字符串
    """
    renderer = HTMLRenderer()
    return renderer.render_metrics_dashboard(analysis_results)
