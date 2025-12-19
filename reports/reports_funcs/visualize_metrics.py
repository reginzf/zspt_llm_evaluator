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

        # 1. 精确率 vs 召回率散点图
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

        # 2. F1分数分布直方图
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

        # 3. Top K精确率
        top_k_cols = [col for col in self.df.columns if col.startswith('precision@')]
        if top_k_cols:
            k_values = [int(col.split('@')[1]) for col in top_k_cols]
            avg_precision_at_k = [self.df[col].mean() for col in top_k_cols]

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

        # 4. Top K召回率
        top_k_cols = [col for col in self.df.columns if col.startswith('recall@')]
        if top_k_cols:
            k_values = [int(col.split('@')[1]) for col in top_k_cols]
            avg_recall_at_k = [self.df[col].mean() for col in top_k_cols]

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

        # 5. 排序指标对比
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

        # 6. 命中率与覆盖率散点图
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

        # 7. 问题性能热图
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

        # 8. 指标相关性热图
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

        # 9. 性能排名条形图
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

    def create_static_report(self, output_dir: str = "./report_data"):
        """创建静态报告（PNG图片）"""
        import os
        os.makedirs(output_dir, exist_ok=True)

        # 设置样式
        plt.style.use('seaborn-v0_8-darkgrid')

        # 1. 精确率-召回率散点图
        plt.figure(figsize=(12, 8))
        scatter = plt.scatter(self.df['recall'], self.df['precision'],
                              c=self.df['f1_score'], cmap='viridis', s=100, alpha=0.7)
        plt.colorbar(scatter, label='F1分数')
        plt.xlabel('召回率', fontsize=12)
        plt.ylabel('精确率', fontsize=12)
        plt.title('精确率 vs 召回率 (颜色表示F1分数)', fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(f"{output_dir}/precision_recall_scatter.png", dpi=150, bbox_inches='tight')
        plt.close()

        # 2. 指标分布箱线图
        plt.figure(figsize=(14, 8))
        metrics_to_plot = ['precision', 'recall', 'f1_score', 'average_precision', 'ndcg', 'mrr']
        available_metrics = [m for m in metrics_to_plot if m in self.df.columns]

        data_to_plot = [self.df[m] for m in available_metrics]
        cn_labels = [METRIC_NAMES_CN.get(m, m) for m in available_metrics]

        bp = plt.boxplot(data_to_plot, labels=cn_labels, patch_artist=True)

        # 设置颜色
        colors = ['#FF9999', '#66B2FF', '#99FF99', '#FFCC99', '#FF99CC', '#99FFFF']
        for patch, color in zip(bp['boxes'], colors[:len(available_metrics)]):
            patch.set_facecolor(color)

        plt.ylabel('指标值', fontsize=12)
        plt.title('指标分布箱线图', fontsize=14, fontweight='bold')
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(f"{output_dir}/metrics_boxplot.png", dpi=150, bbox_inches='tight')
        plt.close()

        # 3. Top K指标趋势图
        plt.figure(figsize=(14, 6))

        # Top K精确率
        plt.subplot(1, 2, 1)
        top_k_cols = [col for col in self.df.columns if col.startswith('precision@')]
        if top_k_cols:
            k_values = [int(col.split('@')[1]) for col in top_k_cols]
            avg_precision_at_k = [self.df[col].mean() for col in top_k_cols]

            plt.plot(k_values, avg_precision_at_k, 'o-', linewidth=3, markersize=8, color='green')
            plt.xlabel('K值', fontsize=12)
            plt.ylabel('平均精确率', fontsize=12)
            plt.title('Top K精确率趋势', fontsize=13, fontweight='bold')
            plt.grid(True, alpha=0.3)

        # Top K召回率
        plt.subplot(1, 2, 2)
        top_k_cols = [col for col in self.df.columns if col.startswith('recall@')]
        if top_k_cols:
            k_values = [int(col.split('@')[1]) for col in top_k_cols]
            avg_recall_at_k = [self.df[col].mean() for col in top_k_cols]

            plt.plot(k_values, avg_recall_at_k, 's-', linewidth=3, markersize=8, color='orange')
            plt.xlabel('K值', fontsize=12)
            plt.ylabel('平均召回率', fontsize=12)
            plt.title('Top K召回率趋势', fontsize=13, fontweight='bold')
            plt.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(f"{output_dir}/top_k_trends.png", dpi=150, bbox_inches='tight')
        plt.close()

        # 4. 性能排名条形图
        plt.figure(figsize=(14, 10))
        top_n = min(20, len(self.df))
        top_questions = self.df.nlargest(top_n, 'f1_score')

        y_pos = np.arange(len(top_questions))
        bars = plt.barh(y_pos, top_questions['f1_score'], color='skyblue', alpha=0.7)

        # 添加数值标签
        for i, (bar, score) in enumerate(zip(bars, top_questions['f1_score'])):
            plt.text(score + 0.01, bar.get_y() + bar.get_height() / 2,
                     f'{score:.3f}', va='center', fontsize=9)

        plt.yticks(y_pos, [f"Q{i + 1}" for i in range(len(top_questions))])
        plt.xlabel('F1分数', fontsize=12)
        plt.title(f'Top {top_n} 问题性能排名', fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3, axis='x')
        plt.tight_layout()
        plt.savefig(f"{output_dir}/performance_ranking.png", dpi=150, bbox_inches='tight')
        plt.close()

        # 5. 指标相关性热图
        plt.figure(figsize=(10, 8))
        correlation_metrics = ['precision', 'recall', 'f1_score', 'average_precision', 'ndcg', 'mrr']
        available_corr = [m for m in correlation_metrics if m in self.df.columns]

        if len(available_corr) > 1:
            corr_matrix = self.df[available_corr].corr()
            cn_labels = [METRIC_NAMES_CN.get(m, m) for m in available_corr]

            sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm',
                        center=0, square=True, linewidths=1,
                        xticklabels=cn_labels, yticklabels=cn_labels)
            plt.title('指标相关性热图', fontsize=14, fontweight='bold')
            plt.tight_layout()
            plt.savefig(f"{output_dir}/correlation_heatmap.png", dpi=150, bbox_inches='tight')
            plt.close()

        print(f"✅ 静态报告图片已保存到: {output_dir}/")

    def export_to_excel(self, output_file: str = "metrics_report.xlsx"):
        """导出为Excel文件"""
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # 1. 详细数据表
            self.df.to_excel(writer, sheet_name='详细数据', index=False)

            # 2. 汇总统计表
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

            # 3. Top K指标表
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

            # 4. 问题排名表
            ranked_df = self.df.copy()
            ranked_df['排名'] = ranked_df['f1_score'].rank(ascending=False, method='min').astype(int)
            ranked_df = ranked_df.sort_values('排名')

            # 只保留关键列
            display_cols = ['排名', 'question', 'precision', 'recall', 'f1_score',
                            'average_precision', 'ndcg', 'mrr']
            available_cols = [col for col in display_cols if col in ranked_df.columns]
            ranked_df[available_cols].to_excel(writer, sheet_name='问题排名', index=False)

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


# 兼容性函数
def analyze_metrics(metric_all: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    分析metric_all数据，返回汇总统计和详细分析结果
    
    Args:
        metric_all: 包含所有问题指标数据的字典
        
    Returns:
        包含分析结果的字典
    """
    from .metrics_analyzer import analyze_metrics as analyze_metrics_new
    return analyze_metrics_new(metric_all)


def generate_html_report(analysis_results: Dict[str, Any]) -> str:
    """
    根据分析结果生成HTML报告
    
    Args:
        analysis_results: analyze_metrics函数返回的分析结果
        
    Returns:
        HTML报告内容字符串
    """
    from .html_renderer import generate_html_report as generate_html_report_new
    return generate_html_report_new(analysis_results)
