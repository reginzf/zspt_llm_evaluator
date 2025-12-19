"""
HTML报告渲染器模块
使用Jinja2模板引擎生成美观的HTML报告
"""

import os
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


class HTMLRenderer:
    """HTML报告渲染器"""
    
    def __init__(self, template_dir: Optional[str] = None):
        """
        初始化HTML渲染器
        
        Args:
            template_dir: 模板目录路径，如果为None则使用默认目录
        """
        self.template_dir = template_dir or str(Path(__file__).parent / "templates")
        
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
        渲染指标仪表板HTML
        
        Args:
            analysis_results: 分析结果字典
            
        Returns:
            HTML内容字符串
        """
        if self.env and JINJA2_AVAILABLE:
            return self._render_with_jinja2("metrics_dashboard.html", analysis_results)
        else:
            return self._render_fallback(analysis_results)
    
    def render_summary_report(self, analysis_results: Dict[str, Any]) -> str:
        """
        渲染摘要报告HTML
        
        Args:
            analysis_results: 分析结果字典
            
        Returns:
            HTML内容字符串
        """
        if self.env and JINJA2_AVAILABLE:
            return self._render_with_jinja2("summary_report.html", analysis_results)
        else:
            return self._render_fallback(analysis_results)
    
    def _render_with_jinja2(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        使用Jinja2渲染模板
        
        Args:
            template_name: 模板文件名
            context: 模板上下文
            
        Returns:
            渲染后的HTML内容
        """
        try:
            template = self.env.get_template(template_name)
            
            # 准备模板上下文
            template_context = self._prepare_template_context(context)
            
            # 渲染模板
            html_content = template.render(**template_context)
            return html_content
            
        except Exception as e:
            print(f"Jinja2渲染错误: {e}")
            return self._render_fallback(context)
    
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
            "correlation_matrix": correlation_matrix,
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
    
    def _render_fallback(self, analysis_results: Dict[str, Any]) -> str:
        """
        备用HTML生成方式（当Jinja2不可用时）
        
        Args:
            analysis_results: 分析结果
            
        Returns:
            HTML内容字符串
        """
        summary = analysis_results.get("summary", {})
        
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>问答系统召回质量评估报告</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: #667eea;
            color: white;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        .metric-card {{
            background: white;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .metric-value {{
            font-size: 1.5em;
            font-weight: bold;
            margin: 5px 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #f8f9fa;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>问答系统召回质量评估报告</h1>
        <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>评估问题数量: {summary.get('total_questions', 0)}</p>
    </div>
    
    <div class="summary">
        <div class="metric-card">
            <h3>平均精确率</h3>
            <div class="metric-value">{summary.get('avg_precision', 0):.4f}</div>
        </div>
        <div class="metric-card">
            <h3>平均召回率</h3>
            <div class="metric-value">{summary.get('avg_recall', 0):.4f}</div>
        </div>
        <div class="metric-card">
            <h3>平均F1分数</h3>
            <div class="metric-value">{summary.get('avg_f1_score', 0):.4f}</div>
        </div>
        <div class="metric-card">
            <h3>平均NDCG</h3>
            <div class="metric-value">{summary.get('avg_ndcg', 0):.4f}</div>
        </div>
    </div>
    
    <h2>性能排名 (Top 10)</h2>
    <table>
        <thead>
            <tr>
                <th>排名</th>
                <th>问题</th>
                <th>F1分数</th>
                <th>精确率</th>
                <th>召回率</th>
            </tr>
        </thead>
        <tbody>
"""

        performance_ranking = analysis_results.get("performance_ranking", [])
        for i, item in enumerate(performance_ranking[:10], 1):
            question_short = item.get("question", "")[:50] + "..." if len(item.get("question", "")) > 50 else item.get("question", "")
            html_content += f"""
            <tr>
                <td>{i}</td>
                <td title="{item.get('question', '')}">{question_short}</td>
                <td>{item.get('f1_score', 0):.4f}</td>
                <td>{item.get('precision', 0):.4f}</td>
                <td>{item.get('recall', 0):.4f}</td>
            </tr>
"""

        html_content += """
        </tbody>
    </table>
    
    <div style="margin-top: 30px; text-align: center; color: #666;">
        <p>报告生成工具: HTMLRenderer (备用模式)</p>
        <p>注: 建议安装Jinja2以获得更好的报告体验</p>
    </div>
</body>
</html>
"""
        
        return html_content
    
    def save_html_report(self, analysis_results: Dict[str, Any], output_file: str, 
                        template_name: str = "metrics_dashboard.html") -> bool:
        """
        保存HTML报告到文件
        
        Args:
            analysis_results: 分析结果
            output_file: 输出文件路径
            template_name: 模板名称
            
        Returns:
            是否成功保存
        """
        try:
            # 渲染HTML
            if template_name == "metrics_dashboard.html":
                html_content = self.render_metrics_dashboard(analysis_results)
            else:
                html_content = self.render_summary_report(analysis_results)
            
            # 确保输出目录存在
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存文件
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"✅ HTML报告已保存到: {output_file}")
            return True
            
        except Exception as e:
            print(f"❌ 保存HTML报告时出错: {e}")
            return False


# 兼容性函数
def generate_html_report(analysis_results: Dict[str, Any]) -> str:
    """
    兼容性函数，用于替换原有的generate_html_report函数
    
    Args:
        analysis_results: analyze_metrics函数返回的分析结果
        
    Returns:
        HTML报告内容字符串
    """
    renderer = HTMLRenderer()
    return renderer.render_metrics_dashboard(analysis_results)