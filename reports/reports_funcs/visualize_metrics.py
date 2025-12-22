"""
metric_all数据可视化展示模块
提供多种美观直观的方式展示切片召回质量评估结果
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings

warnings.filterwarnings('ignore')

# 设置中文字体（如果系统支持）
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

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


class MetricsVisualizer:
    """指标可视化展示器"""

    def __init__(self, metric_all: Dict[str, Dict[str, Any]]):
        """
        初始化可视化器
        
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
            for key in ["precision", "recall", "f1_score", "average_precision",
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

    def _get_top_k_columns(self, prefix: str) -> tuple:
        """获取指定前缀的Top K列名及相关数据"""
        columns = [col for col in self.df.columns if col.startswith(prefix)]
        if not columns:
            return [], []

        k_values = [int(col.split('@')[1]) for col in columns]
        avg_values = [self.df[col].mean() for col in columns]
        return k_values, avg_values

    def _create_pr_scatter_plot(self, fig: go.Figure) -> None:
        """创建精确率-召回率散点图"""
        fig.add_trace(
            go.Scatter(
                x=self.df['recall'],
                y=self.df['precision'],
                mode='markers',
                marker=dict(
                    size=10,
                    color=self.df['f1_score'],
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="F1分数")
                ),
                text=self.df['question'].str[:50],
                hoverinfo='text+x+y',
                name='问题'
            ),
            row=1, col=1
        )
        fig.update_xaxes(title_text="召回率", row=1, col=1)
        fig.update_yaxes(title_text="精确率", row=1, col=1)

    def _create_f1_histogram(self, fig: go.Figure) -> None:
        """创建F1分数分布直方图"""
        fig.add_trace(
            go.Histogram(
                x=self.df['f1_score'],
                nbinsx=20,
                marker_color='skyblue',
                name='F1分布'
            ),
            row=1, col=2
        )
        fig.update_xaxes(title_text="F1分数", row=1, col=2)
        fig.update_yaxes(title_text="数量", row=1, col=2)

    def _create_precision_at_k_plot(self, fig: go.Figure) -> None:
        """创建Top K精确率折线图"""
        k_values, avg_precision_at_k = self._get_top_k_columns('precision@')
        if k_values:
            fig.add_trace(
                go.Scatter(
                    x=k_values,
                    y=avg_precision_at_k,
                    mode='lines+markers',
                    line=dict(color='green', width=3),
                    marker=dict(size=10),
                    name='平均精确率@K'
                ),
                row=1, col=3
            )
            fig.update_xaxes(title_text="K值", row=1, col=3)
            fig.update_yaxes(title_text="精确率", row=1, col=3)

    def _create_recall_at_k_plot(self, fig: go.Figure) -> None:
        """创建Top K召回率折线图"""
        k_values, avg_recall_at_k = self._get_top_k_columns('recall@')
        if k_values:
            fig.add_trace(
                go.Scatter(
                    x=k_values,
                    y=avg_recall_at_k,
                    mode='lines+markers',
                    line=dict(color='orange', width=3),
                    marker=dict(size=10),
                    name='平均召回率@K'
                ),
                row=2, col=1
            )
            fig.update_xaxes(title_text="K值", row=2, col=1)
            fig.update_yaxes(title_text="召回率", row=2, col=1)

    def _create_ranking_metrics_bar(self, fig: go.Figure) -> None:
        """创建排序指标对比柱状图"""
        ranking_metrics = ['average_precision', 'ndcg', 'mrr']
        available_metrics = [m for m in ranking_metrics if m in self.df.columns]

        if available_metrics:
            avg_values = [self.df[m].mean() for m in available_metrics]
            cn_names = [METRIC_NAMES_CN.get(m, m) for m in available_metrics]

            fig.add_trace(
                go.Bar(
                    x=cn_names,
                    y=avg_values,
                    marker_color=['#FF6B6B', '#4ECDC4', '#45B7D1'],
                    name='排序指标'
                ),
                row=2, col=2
            )
            fig.update_xaxes(title_text="指标", row=2, col=2)
            fig.update_yaxes(title_text="平均值", row=2, col=2)

    def _create_hit_coverage_scatter(self, fig: go.Figure) -> None:
        """创建命中率与覆盖率散点图"""
        if 'hit_rate' in self.df.columns and 'coverage' in self.df.columns:
            fig.add_trace(
                go.Scatter(
                    x=self.df['coverage'],
                    y=self.df['hit_rate'],
                    mode='markers',
                    marker=dict(
                        size=10,
                        color=self.df['f1_score'],
                        colorscale='Plasma',
                        showscale=False
                    ),
                    text=self.df['question'].str[:50],
                    hoverinfo='text+x+y',
                    name='命中率vs覆盖率'
                ),
                row=2, col=3
            )
            fig.update_xaxes(title_text="覆盖率", row=2, col=3)
            fig.update_yaxes(title_text="命中率", row=2, col=3)

    def _create_performance_heatmap(self, fig: go.Figure) -> None:
        """创建问题性能热图"""
        top_questions = self.df.nlargest(10, 'f1_score')
        metrics_for_heatmap = ['precision', 'recall', 'f1_score', 'average_precision', 'ndcg']
        available_for_heatmap = [m for m in metrics_for_heatmap if m in top_questions.columns]

        if len(available_for_heatmap) > 0:
            heatmap_data = top_questions[available_for_heatmap].values.T
            cn_labels = [METRIC_NAMES_CN.get(m, m) for m in available_for_heatmap]

            fig.add_trace(
                go.Heatmap(
                    z=heatmap_data,
                    x=[f"Q{i + 1}" for i in range(len(top_questions))],
                    y=cn_labels,
                    colorscale='YlOrRd',
                    showscale=True,
                    colorbar=dict(title="指标值")
                ),
                row=3, col=1
            )

    def _create_correlation_heatmap(self, fig: go.Figure) -> None:
        """创建指标相关性热图"""
        correlation_metrics = ['precision', 'recall', 'f1_score', 'average_precision', 'ndcg', 'mrr']
        available_corr = [m for m in correlation_metrics if m in self.df.columns]

        if len(available_corr) > 1:
            corr_matrix = self.df[available_corr].corr()
            cn_labels_corr = [METRIC_NAMES_CN.get(m, m) for m in available_corr]

            fig.add_trace(
                go.Heatmap(
                    z=corr_matrix.values,
                    x=cn_labels_corr,
                    y=cn_labels_corr,
                    colorscale='RdBu',
                    zmid=0,
                    showscale=True,
                    colorbar=dict(title="相关系数")
                ),
                row=3, col=2
            )

    def _create_performance_ranking_bar(self, fig: go.Figure) -> None:
        """创建性能排名条形图"""
        top_n = min(15, len(self.df))
        top_questions = self.df.nlargest(top_n, 'f1_score')

        fig.add_trace(
            go.Bar(
                y=[f"Q{i + 1}" for i in range(len(top_questions))],
                x=top_questions['f1_score'],
                orientation='h',
                marker_color='lightgreen',
                text=[f"{score:.3f}" for score in top_questions['f1_score']],
                textposition='auto',
                name='F1分数排名'
            ),
            row=3, col=3
        )
        fig.update_xaxes(title_text="F1分数", row=3, col=3)

    def create_interactive_dashboard(self, output_file: str = "metrics_dashboard.html"):
        """创建交互式仪表板"""
        # 创建子图
        fig = make_subplots(
            rows=3, cols=3,
            subplot_titles=('精确率 vs 召回率', 'F1分数分布', 'Top K精确率',
                            'Top K召回率', '排序指标对比', '命中率与覆盖率',
                            '问题性能热图', '指标相关性', '性能排名'),
            specs=[[{'type': 'scatter'}, {'type': 'histogram'}, {'type': 'scatter'}],
                   [{'type': 'scatter'}, {'type': 'bar'}, {'type': 'scatter'}],
                   [{'type': 'heatmap'}, {'type': 'heatmap'}, {'type': 'bar'}]]
        )

        # 添加各个子图
        self._create_pr_scatter_plot(fig)
        self._create_f1_histogram(fig)
        self._create_precision_at_k_plot(fig)
        self._create_recall_at_k_plot(fig)
        self._create_ranking_metrics_bar(fig)
        self._create_hit_coverage_scatter(fig)
        self._create_performance_heatmap(fig)
        self._create_correlation_heatmap(fig)
        self._create_performance_ranking_bar(fig)

        # 更新布局
        fig.update_layout(
            height=1200,
            width=1600,
            title_text="切片召回质量评估仪表板",
            showlegend=False,
            template="plotly_white"
        )

        # 保存为HTML文件
        fig.write_html(output_file)
        print(f"✅ 交互式仪表板已保存到: {output_file}")

        return fig

    def _create_detailed_sheet(self, writer) -> None:
        """创建详细数据表"""
        self.df.to_excel(writer, sheet_name='详细数据', index=False)

    def _create_summary_sheet(self, writer) -> None:
        """创建汇总统计表"""
        summary_data = []
        for metric in ['precision', 'recall', 'f1_score', 'average_precision', 'ndcg', 'mrr']:
            if metric in self.df.columns:
                cn_name = METRIC_NAMES_CN.get(metric, metric)
                summary_data.append({
                    '指标': cn_name,
                    '平均值': self.df[metric].mean(),
                    '中位数': self.df[metric].median(),
                    '标准差': self.df[metric].std(),
                    '最小值': self.df[metric].min(),
                    '最大值': self.df[metric].max(),
                    '25%分位数': self.df[metric].quantile(0.25),
                    '75%分位数': self.df[metric].quantile(0.75)
                })

        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='汇总统计', index=False)

    def _create_top_k_sheet(self, writer) -> None:
        """创建Top K指标表"""
        top_k_data = []
        for col in self.df.columns:
            if col.startswith('precision@') or col.startswith('recall@'):
                metric_type = '精确率' if 'precision' in col else '召回率'
                k_value = col.split('@')[1]
                top_k_data.append({
                    '指标类型': metric_type,
                    'K值': k_value,
                    '平均值': self.df[col].mean(),
                    '标准差': self.df[col].std()
                })

        if top_k_data:
            top_k_df = pd.DataFrame(top_k_data)
            top_k_df.to_excel(writer, sheet_name='Top_K指标', index=False)

    def _create_ranking_sheet(self, writer) -> None:
        """创建问题排名表"""
        ranked_df = self.df.copy()
        ranked_df['排名'] = ranked_df['f1_score'].rank(ascending=False, method='min').astype(int)
        ranked_df = ranked_df.sort_values('排名')

        # 只保留关键列
        display_cols = ['排名', 'question', 'precision', 'recall', 'f1_score',
                        'average_precision', 'ndcg', 'mrr']
        available_cols = [col for col in display_cols if col in ranked_df.columns]
        ranked_df[available_cols].to_excel(writer, sheet_name='问题排名', index=False)

    def export_to_excel(self, output_file: str = "metrics_report.xlsx"):
        """导出为Excel文件"""
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # 创建各个工作表
            self._create_detailed_sheet(writer)
            self._create_summary_sheet(writer)
            self._create_top_k_sheet(writer)
            self._create_ranking_sheet(writer)

        print(f"✅ Excel报告已保存到: {output_file}")

    def run_all_visualizations(self, output_prefix: str = "metrics"):
        """运行所有可视化"""
        print("🚀 开始生成所有可视化报告...")

        # 1. 创建交互式仪表板
        self.create_interactive_dashboard(f"{output_prefix}_dashboard.html")

        # 2. 创建静态报告图片
        self.create_static_report(f"./{output_prefix}_reports")

        # 3. 导出Excel
        self.export_to_excel(f"{output_prefix}_report.xlsx")

        print("\n🎉 所有可视化报告生成完成！")
        print(f"📁 输出文件:")
        print(f"   - {output_prefix}_dashboard.html (交互式仪表板)")
        print(f"   - {output_prefix}_reports/ (静态图片)")
        print(f"   - {output_prefix}_report.xlsx (Excel报告)")


if __name__ == '__main__':
    from reports.reports_funcs.generate_report import load_metric_data
    from pathlib import Path

    data = load_metric_data(
        r'D:\pyworkplace\git_place\ai-ken\reports\report_data\ospf\metric_chunk_id_augmentedSearch_400_0.json',
        Path(r'D:\pyworkplace\git_place\ai-ken\reports\report_data\ospf'))
    mev = MetricsVisualizer(data)
    mev.create_interactive_dashboard("ospf_dashboard.html")
