"""
问答系统召回质量评估报告生成模块
提供metric_all数据的分析、可视化和报告生成功能
"""

__version__ = "1.0.2"


# 导出主要功能
from .metrics_analyzer import MetricsAnalyzer, analyze_metrics
from .visualize_metrics import MetricsVisualizer
from utils.pub_funs import load_metric_data

__all__ = [
    "MetricsAnalyzer",
    "analyze_metrics",
    "MetricsVisualizer"
]