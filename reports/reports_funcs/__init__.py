"""
问答系统召回质量评估报告生成模块
提供metric_all数据的分析、可视化和报告生成功能
"""

__version__ = "1.0.2"


# 导出主要功能
from .metrics_analyzer import MetricsAnalyzer, analyze_metrics
from .html_renderer import HTMLRenderer, generate_html_report
from .visualize_metrics import MetricsVisualizer
from .generate_report import load_metric_data, generate_reports_from_metric_files

__all__ = [
    "MetricsAnalyzer",
    "analyze_metrics",
    "HTMLRenderer",
    "generate_html_report",
    "MetricsVisualizer",
    "load_metric_data",
    "generate_reports_from_metric_files"
]
