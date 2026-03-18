"""
指标数据分析器模块
提供metric_all数据的分析和统计功能
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
import warnings

warnings.filterwarnings('ignore')

# 指标中文映射
METRIC_NAMES_CN = {
    "precision": "精确率",
    "recall": "召回率",
    "f1_score": "F1分数",
    "average_precision": "平均精确率",
    "ndcg": "NDCG",
    "mrr": "MRR",
    "hit_rate": "命中率",
    "coverage": "覆盖率",
    "redundancy": "冗余度",
    "true_positives": "真正例",
    "false_positives": "假正例",
    "false_negatives": "假负例",
    "total_relevant": "总相关数",
    "total_retrieved": "总检索数"
}


class MetricsAnalyzer:
    """指标数据分析器"""

    def __init__(self, metric_all: Dict[str, Dict[str, Any]]):
        """
        初始化分析器
        
        Args:
            metric_all: 包含所有问题指标数据的字典
        """
        self.metric_all = metric_all
        self.df = self._create_dataframe()

    def _create_dataframe(self) -> pd.DataFrame:
        """将metric_all转换为DataFrame"""
        records = []

        for question, metrics in self.metric_all.items():
            record = {"question": question}

            # 添加基础指标
            for key in ["precision", "type", "recall", "f1_score", "average_precision",
                        "ndcg", "mrr", "hit_rate", "coverage", "redundancy",
                        "true_positives", "false_positives", "false_negatives",
                        "total_relevant", "total_retrieved"]:
                if key in metrics:
                    record[key] = metrics[key]

            # 添加Top K指标（展平）
            for k, value in metrics.get("precision_at_k", {}).items():
                record[f"precision@{k}"] = value
            for k, value in metrics.get("recall_at_k", {}).items():
                record[f"recall@{k}"] = value

            records.append(record)

        return pd.DataFrame(records)

    def get_summary_statistics(self) -> Dict[str, Any]:
        """获取汇总统计信息"""
        summary = {
            "total_questions": len(self.metric_all),
            "avg_precision": float(self.df['precision'].mean()),
            "avg_recall": float(self.df['recall'].mean()),
            "avg_f1_score": float(self.df['f1_score'].mean()),
            "avg_average_precision": float(self.df.get('average_precision', pd.Series([0])).mean()),
            "avg_ndcg": float(self.df.get('ndcg', pd.Series([0])).mean()),
            "avg_mrr": float(self.df.get('mrr', pd.Series([0])).mean()),
            "avg_hit_rate": float(self.df.get('hit_rate', pd.Series([0])).mean()),
            "avg_coverage": float(self.df.get('coverage', pd.Series([0])).mean()),
            "avg_redundancy": float(self.df.get('redundancy', pd.Series([0])).mean()),
        }

        return summary

    def get_distribution_analysis(self) -> Dict[str, Dict[str, float]]:
        """获取指标分布分析"""
        distribution = {
            "precision": {
                "mean": float(self.df['precision'].mean()),
                "std": float(self.df['precision'].std()),
                "min": float(self.df['precision'].min()),
                "max": float(self.df['precision'].max()),
                "median": float(self.df['precision'].median()),
                "q25": float(self.df['precision'].quantile(0.25)),
                "q75": float(self.df['precision'].quantile(0.75))
            },
            "recall": {
                "mean": float(self.df['recall'].mean()),
                "std": float(self.df['recall'].std()),
                "min": float(self.df['recall'].min()),
                "max": float(self.df['recall'].max()),
                "median": float(self.df['recall'].median()),
                "q25": float(self.df['recall'].quantile(0.25)),
                "q75": float(self.df['recall'].quantile(0.75))
            },
            "f1_score": {
                "mean": float(self.df['f1_score'].mean()),
                "std": float(self.df['f1_score'].std()),
                "min": float(self.df['f1_score'].min()),
                "max": float(self.df['f1_score'].max()),
                "median": float(self.df['f1_score'].median()),
                "q25": float(self.df['f1_score'].quantile(0.25)),
                "q75": float(self.df['f1_score'].quantile(0.75))
            }
        }

        return distribution

    def get_top_performers(self) -> Dict[str, Dict[str, Any]]:
        """获取最佳表现问题"""
        top_performers = {
            "best_f1": {
                "question": self.df.loc[self.df['f1_score'].idxmax(), 'question'],
                "f1_score": float(self.df['f1_score'].max()),
                "precision": float(self.df.loc[self.df['f1_score'].idxmax(), 'precision']),
                "recall": float(self.df.loc[self.df['f1_score'].idxmax(), 'recall'])
            },
            "worst_f1": {
                "question": self.df.loc[self.df['f1_score'].idxmin(), 'question'],
                "f1_score": float(self.df['f1_score'].min()),
                "precision": float(self.df.loc[self.df['f1_score'].idxmin(), 'precision']),
                "recall": float(self.df.loc[self.df['f1_score'].idxmin(), 'recall'])
            },
            "best_precision": {
                "question": self.df.loc[self.df['precision'].idxmax(), 'question'],
                "precision": float(self.df['precision'].max()),
                "recall": float(self.df.loc[self.df['precision'].idxmax(), 'recall']),
                "f1_score": float(self.df.loc[self.df['precision'].idxmax(), 'f1_score'])
            },
            "best_recall": {
                "question": self.df.loc[self.df['recall'].idxmax(), 'question'],
                "recall": float(self.df['recall'].max()),
                "precision": float(self.df.loc[self.df['recall'].idxmax(), 'precision']),
                "f1_score": float(self.df.loc[self.df['recall'].idxmax(), 'f1_score'])
            }
        }

        return top_performers

    def get_top_k_analysis(self) -> Dict[str, Dict[str, Dict[str, float]]]:
        """获取Top K指标分析"""
        top_k_analysis = {}

        # 计算Top K指标
        top_k_cols = [col for col in self.df.columns if col.startswith('precision@') or col.startswith('recall@')]
        for col in top_k_cols:
            metric_type = 'precision' if 'precision' in col else 'recall'
            k_value = col.split('@')[1]
            if metric_type not in top_k_analysis:
                top_k_analysis[metric_type] = {}
            top_k_analysis[metric_type][k_value] = {
                "mean": float(self.df[col].mean()),
                "std": float(self.df[col].std()),
                "min": float(self.df[col].min()),
                "max": float(self.df[col].max())
            }

        return top_k_analysis

    def get_correlation_matrix(self) -> Dict[str, Dict[str, float]]:
        """获取指标相关性矩阵"""
        correlation_matrix = {}

        correlation_metrics = ['precision', 'recall', 'f1_score', 'average_precision', 'ndcg', 'mrr']
        available_corr = [m for m in correlation_metrics if m in self.df.columns]

        if len(available_corr) > 1:
            try:
                corr_matrix = self.df[available_corr].corr()
                for i, metric1 in enumerate(available_corr):
                    correlation_matrix[metric1] = {}
                    for j, metric2 in enumerate(available_corr):
                        correlation_matrix[metric1][metric2] = float(corr_matrix.iloc[i, j])
            except Exception as e:
                print(f"计算相关性矩阵时出错: {e}")
                # 返回单位矩阵作为默认值
                for metric1 in available_corr:
                    correlation_matrix[metric1] = {}
                    for metric2 in available_corr:
                        correlation_matrix[metric1][metric2] = 1.0 if metric1 == metric2 else 0.0
        else:
            # 如果可用指标不足，返回单位矩阵
            for metric1 in correlation_metrics:
                correlation_matrix[metric1] = {}
                for metric2 in correlation_metrics:
                    correlation_matrix[metric1][metric2] = 1.0 if metric1 == metric2 else 0.0

        return correlation_matrix

    def get_performance_ranking(self, top_n: int = 20) -> List[Dict[str, Any]]:
        """获取性能排名"""
        ranked_df = self.df.copy()
        # 处理 f1_score 为 None 或 NaN 的情况，先填充为 -1 避免排名出错
        ranked_df['f1_score'] = ranked_df['f1_score'].fillna(-1)
        ranked_df['rank'] = ranked_df['f1_score'].rank(ascending=False, method='min').astype(int)
        ranked_df = ranked_df.sort_values('rank')

        performance_ranking = []
        for _, row in ranked_df.head(top_n).iterrows():
            performance_ranking.append({
                "rank": int(row['rank']),
                "question": row['question'],
                "q_type": row['type'],
                "f1_score": float(row['f1_score']),
                "precision": float(row['precision']),
                "recall": float(row['recall']),
                "average_precision": float(row.get('average_precision', 0)),
                "ndcg": float(row.get('ndcg', 0)),
                "mrr": float(row.get('mrr', 0))
            })

        return performance_ranking

    def get_metric_cn_name(self, metric_name: str) -> str:
        """获取指标的中文名称"""
        return METRIC_NAMES_CN.get(metric_name, metric_name)

    def print_summary(self):
        """打印汇总统计信息"""
        print("=" * 80)
        print("切片召回质量评估结果汇总")
        print("=" * 80)

        # 基础统计
        print(f"\n📊 总体统计:")
        print(f"   评估问题数量: {len(self.metric_all)}")

        # 计算平均指标
        summary = self.get_summary_statistics()

        print(f"\n📈 平均指标:")
        for metric in ["avg_precision", "avg_recall", "avg_f1_score", "avg_average_precision", "avg_ndcg", "avg_mrr"]:
            if metric in summary:
                cn_name = self.get_metric_cn_name(metric.replace('avg_', ''))
                print(f"   {cn_name}: {summary[metric]:.4f}")

        # 最佳和最差问题
        top_performers = self.get_top_performers()

        print(f"\n🏆 最佳表现问题 (按F1分数):")
        best_f1 = top_performers.get("best_f1", {})
        print(f"   问题: {best_f1.get('question', '')[:60]}...")
        print(f"   F1分数: {best_f1.get('f1_score', 0):.4f}, "
              f"精确率: {best_f1.get('precision', 0):.4f}, "
              f"召回率: {best_f1.get('recall', 0):.4f}")

        print(f"\n⚠️  最差表现问题 (按F1分数):")
        worst_f1 = top_performers.get("worst_f1", {})
        print(f"   问题: {worst_f1.get('question', '')[:60]}...")
        print(f"   F1分数: {worst_f1.get('f1_score', 0):.4f}, "
              f"精确率: {worst_f1.get('precision', 0):.4f}, "
              f"召回率: {worst_f1.get('recall', 0):.4f}")

        # 指标分布
        print(f"\n📊 指标分布:")
        distribution = self.get_distribution_analysis()
        for metric in ["precision", "recall", "f1_score"]:
            if metric in distribution:
                cn_name = self.get_metric_cn_name(metric)
                stats = distribution[metric]
                print(f"   {cn_name}: 均值={stats['mean']:.4f}, "
                      f"标准差={stats['std']:.4f}, "
                      f"范围=[{stats['min']:.4f}, {stats['max']:.4f}]")


# 分析指标数据的函数
def analyze_metrics(metric_all: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    分析metric_all数据，返回汇总统计和详细分析结果
    
    Args:
        metric_all: 包含所有问题指标数据的字典
        
    Returns:
        包含分析结果的字典
    """
    analyzer = MetricsAnalyzer(metric_all)

    analysis_results = {
        "summary": analyzer.get_summary_statistics(),
        "distribution": analyzer.get_distribution_analysis(),
        "top_performers": analyzer.get_top_performers(),
        "top_k_analysis": analyzer.get_top_k_analysis(),
        "correlation_matrix": analyzer.get_correlation_matrix(),
        "performance_ranking": analyzer.get_performance_ranking()
    }

    return analysis_results