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

    def show_summary_statistics(self):
        """显示汇总统计信息"""
        print("=" * 80)
        print("切片召回质量评估结果汇总")
        print("=" * 80)

        # 基础统计
        print(f"\n📊 总体统计:")
        print(f"   评估问题数量: {len(self.metric_all)}")

        # 计算平均指标
        avg_metrics = {}
        for metric in ["precision", "recall", "f1_score", "average_precision", "ndcg", "mrr"]:
            if metric in self.df.columns:
                avg_metrics[metric] = self.df[metric].mean()

        print(f"\n📈 平均指标:")
        for metric, value in avg_metrics.items():
            cn_name = METRIC_NAMES_CN.get(metric, metric)
            print(f"   {cn_name}: {value:.4f}")

        # 最佳和最差问题
        print(f"\n🏆 最佳表现问题 (按F1分数):")
        best_idx = self.df["f1_score"].idxmax()
        best_row = self.df.loc[best_idx]
        print(f"   问题: {best_row['question'][:60]}...")
        print(
            f"   F1分数: {best_row['f1_score']:.4f}, 精确率: {best_row['precision']:.4f}, 召回率: {best_row['recall']:.4f}")

        print(f"\n⚠️  最差表现问题 (按F1分数):")
        worst_idx = self.df["f1_score"].idxmin()
        worst_row = self.df.loc[worst_idx]
        print(f"   问题: {worst_row['question'][:60]}...")
        print(
            f"   F1分数: {worst_row['f1_score']:.4f}, 精确率: {worst_row['precision']:.4f}, 召回率: {worst_row['recall']:.4f}")

        # 指标分布
        print(f"\n📊 指标分布:")
        for metric in ["precision", "recall", "f1_score"]:
            if metric in self.df.columns:
                cn_name = METRIC_NAMES_CN.get(metric, metric)
                print(f"   {cn_name}: 均值={self.df[metric].mean():.4f}, "
                      f"标准差={self.df[metric].std():.4f}, "
                      f"范围=[{self.df[metric].min():.4f}, {self.df[metric].max():.4f}]")

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

    def generate_html_report_old(self, output_file: str = "metrics_report.html"):
        """生成HTML格式的完整报告"""
        from datetime import datetime

        # 计算统计信息
        avg_precision = self.df['precision'].mean()
        avg_recall = self.df['recall'].mean()
        avg_f1 = self.df['f1_score'].mean()

        # 生成HTML内容
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>切片召回质量评估报告</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px;
                    margin-bottom: 30px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }}
                .summary-cards {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }}
                .card {{
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    text-align: center;
                }}
                .card h3 {{
                    margin-top: 0;
                    color: #555;
                }}
                .card-value {{
                    font-size: 2.5em;
                    font-weight: bold;
                    margin: 10px 0;
                }}
                .card-good {{ color: #4CAF50; }}
                .card-medium {{ color: #FF9800; }}
                .card-poor {{ color: #F44336; }}
                .table-container {{
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    margin-bottom: 30px;
                    overflow-x: auto;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                }}
                th, td {{
                    padding: 12px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }}
                th {{
                    background-color: #f8f9fa;
                    font-weight: bold;
                }}
                tr:hover {{
                    background-color: #f5f5f5;
                }}
                .metric-badge {{
                    display: inline-block;
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 0.9em;
                    font-weight: bold;
                }}
                .badge-good {{ background-color: #d4edda; color: #155724; }}
                .badge-medium {{ background-color: #fff3cd; color: #856404; }}
                .badge-poor {{ background-color: #f8d7da; color: #721c24; }}
                .footer {{
                    text-align: center;
                    margin-top: 40px;
                    color: #666;
                    font-size: 0.9em;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 切片召回质量评估报告</h1>
                <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 评估问题数量: {len(self.metric_all)}</p>
            </div>
            
            <div class="summary-cards">
                <div class="card">
                    <h3>平均精确率</h3>
                    <div class="card-value {'card-good' if avg_precision > 0.7 else 'card-medium' if avg_precision > 0.5 else 'card-poor'}">
                        {avg_precision:.4f}
                    </div>
                    <p>检索结果的相关性程度</p>
                </div>
                
                <div class="card">
                    <h3>平均召回率</h3>
                    <div class="card-value {'card-good' if avg_recall > 0.7 else 'card-medium' if avg_recall > 0.5 else 'card-poor'}">
                        {avg_recall:.4f}
                    </div>
                    <p>检索到的相关文档比例</p>
                </div>
                
                <div class="card">
                    <h3>平均F1分数</h3>
                    <div class="card-value {'card-good' if avg_f1 > 0.7 else 'card-medium' if avg_f1 > 0.5 else 'card-poor'}">
                        {avg_f1:.4f}
                    </div>
                    <p>精确率和召回率的调和平均</p>
                </div>
                
                <div class="card">
                    <h3>最佳F1分数</h3>
                    <div class="card-value card-good">
                        {self.df['f1_score'].max():.4f}
                    </div>
                    <p>单个问题的最佳表现</p>
                </div>
            </div>
            
            <div class="table-container">
                <h2>📋 问题性能排名 (Top 10)</h2>
                <table>
                    <thead>
                        <tr>
                            <th>排名</th>
                            <th>问题</th>
                            <th>精确率</th>
                            <th>召回率</th>
                            <th>F1分数</th>
                            <th>AP</th>
                            <th>NDCG</th>
                            <th>状态</th>
                        </tr>
                    </thead>
                    <tbody>
        """

        # 添加表格行
        top_10 = self.df.nlargest(10, 'f1_score')
        for i, (_, row) in enumerate(top_10.iterrows(), 1):
            f1_score = row['f1_score']
            if f1_score > 0.7:
                status_class = "badge-good"
                status_text = "优秀"
            elif f1_score > 0.5:
                status_class = "badge-medium"
                status_text = "良好"
            else:
                status_class = "badge-poor"
                status_text = "需改进"

            question_short = row['question'][:80] + "..." if len(row['question']) > 80 else row['question']

            html_content += f"""
                        <tr>
                            <td>{i}</td>
                            <td title="{row['question']}">{question_short}</td>
                            <td>{row['precision']:.4f}</td>
                            <td>{row['recall']:.4f}</td>
                            <td>{row['f1_score']:.4f}</td>
                            <td>{row.get('average_precision', 0):.4f}</td>
                            <td>{row.get('ndcg', 0):.4f}</td>
                            <td><span class="metric-badge {status_class}">{status_text}</span></td>
                        </tr>
            """

        html_content += """
                    </tbody>
                </table>
            </div>
            
            <div class="table-container">
                <h2>📈 指标统计摘要</h2>
                <table>
                    <thead>
                        <tr>
                            <th>指标</th>
                            <th>平均值</th>
                            <th>中位数</th>
                            <th>标准差</th>
                            <th>最小值</th>
                            <th>最大值</th>
                        </tr>
                    </thead>
                    <tbody>
        """

        # 添加指标统计行
        metrics_stats = ['precision', 'recall', 'f1_score', 'average_precision', 'ndcg', 'mrr']
        for metric in metrics_stats:
            if metric in self.df.columns:
                cn_name = METRIC_NAMES_CN.get(metric, metric)
                html_content += f"""
                        <tr>
                            <td>{cn_name}</td>
                            <td>{self.df[metric].mean():.4f}</td>
                            <td>{self.df[metric].median():.4f}</td>
                            <td>{self.df[metric].std():.4f}</td>
                            <td>{self.df[metric].min():.4f}</td>
                            <td>{self.df[metric].max():.4f}</td>
                        </tr>
                """

        html_content += """
                    </tbody>
                </table>
            </div>
            
            <div class="footer">
                <p>报告生成工具: MetricsVisualizer | 版本: 1.0.0</p>
                <p>注: 此报告基于切片召回质量评估结果自动生成</p>
            </div>
        </body>
        </html>
        """

        # 保存HTML文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"✅ HTML报告已保存到: {output_file}")

    def run_all_visualizations(self, output_prefix: str = "metrics"):
        """运行所有可视化"""
        print("🚀 开始生成所有可视化报告...")

        # 1. 显示汇总统计
        self.show_summary_statistics()

        # 2. 创建交互式仪表板
        self.create_interactive_dashboard(f"{output_prefix}_dashboard.html")

        # 3. 创建静态报告图片
        self.create_static_report(f"./{output_prefix}_reports")

        # 4. 导出Excel
        self.export_to_excel(f"{output_prefix}_report.xlsx")

        # 5. 生成HTML报告
        self.generate_html_report(f"{output_prefix}_report.html")

        print("\n🎉 所有可视化报告生成完成！")
        print(f"📁 输出文件:")
        print(f"   - {output_prefix}_dashboard.html (交互式仪表板)")
        print(f"   - {output_prefix}_reports/ (静态图片)")
        print(f"   - {output_prefix}_report.xlsx (Excel报告)")
        print(f"   - {output_prefix}_report.html (HTML报告)")


# 分析指标数据的函数
def analyze_metrics(metric_all: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    分析metric_all数据，返回汇总统计和详细分析结果
    
    Args:
        metric_all: 包含所有问题指标数据的字典
        
    Returns:
        包含分析结果的字典
    """
    visualizer = MetricsVisualizer(metric_all)
    df = visualizer.df

    # 计算基本统计
    analysis_results = {
        "summary": {
            "total_questions": len(metric_all),
            "avg_precision": float(df['precision'].mean()),
            "avg_recall": float(df['recall'].mean()),
            "avg_f1_score": float(df['f1_score'].mean()),
            "avg_average_precision": float(df.get('average_precision', pd.Series([0])).mean()),
            "avg_ndcg": float(df.get('ndcg', pd.Series([0])).mean()),
            "avg_mrr": float(df.get('mrr', pd.Series([0])).mean()),
            "avg_hit_rate": float(df.get('hit_rate', pd.Series([0])).mean()),
            "avg_coverage": float(df.get('coverage', pd.Series([0])).mean()),
            "avg_redundancy": float(df.get('redundancy', pd.Series([0])).mean()),
        },
        "distribution": {
            "precision": {
                "mean": float(df['precision'].mean()),
                "std": float(df['precision'].std()),
                "min": float(df['precision'].min()),
                "max": float(df['precision'].max()),
                "median": float(df['precision'].median()),
                "q25": float(df['precision'].quantile(0.25)),
                "q75": float(df['precision'].quantile(0.75))
            },
            "recall": {
                "mean": float(df['recall'].mean()),
                "std": float(df['recall'].std()),
                "min": float(df['recall'].min()),
                "max": float(df['recall'].max()),
                "median": float(df['recall'].median()),
                "q25": float(df['recall'].quantile(0.25)),
                "q75": float(df['recall'].quantile(0.75))
            },
            "f1_score": {
                "mean": float(df['f1_score'].mean()),
                "std": float(df['f1_score'].std()),
                "min": float(df['f1_score'].min()),
                "max": float(df['f1_score'].max()),
                "median": float(df['f1_score'].median()),
                "q25": float(df['f1_score'].quantile(0.25)),
                "q75": float(df['f1_score'].quantile(0.75))
            }
        },
        "top_performers": {
            "best_f1": {
                "question": df.loc[df['f1_score'].idxmax(), 'question'],
                "f1_score": float(df['f1_score'].max()),
                "precision": float(df.loc[df['f1_score'].idxmax(), 'precision']),
                "recall": float(df.loc[df['f1_score'].idxmax(), 'recall'])
            },
            "worst_f1": {
                "question": df.loc[df['f1_score'].idxmin(), 'question'],
                "f1_score": float(df['f1_score'].min()),
                "precision": float(df.loc[df['f1_score'].idxmin(), 'precision']),
                "recall": float(df.loc[df['f1_score'].idxmin(), 'recall'])
            },
            "best_precision": {
                "question": df.loc[df['precision'].idxmax(), 'question'],
                "precision": float(df['precision'].max()),
                "recall": float(df.loc[df['precision'].idxmax(), 'recall']),
                "f1_score": float(df.loc[df['precision'].idxmax(), 'f1_score'])
            },
            "best_recall": {
                "question": df.loc[df['recall'].idxmax(), 'question'],
                "recall": float(df['recall'].max()),
                "precision": float(df.loc[df['recall'].idxmax(), 'precision']),
                "f1_score": float(df.loc[df['recall'].idxmax(), 'f1_score'])
            }
        },
        "top_k_analysis": {},
        "correlation_matrix": {},
        "performance_ranking": []
    }

    # 计算Top K指标
    top_k_cols = [col for col in df.columns if col.startswith('precision@') or col.startswith('recall@')]
    for col in top_k_cols:
        metric_type = 'precision' if 'precision' in col else 'recall'
        k_value = col.split('@')[1]
        if metric_type not in analysis_results["top_k_analysis"]:
            analysis_results["top_k_analysis"][metric_type] = {}
        analysis_results["top_k_analysis"][metric_type][k_value] = {
            "mean": float(df[col].mean()),
            "std": float(df[col].std()),
            "min": float(df[col].min()),
            "max": float(df[col].max())
        }

    # 计算相关性矩阵
    correlation_metrics = ['precision', 'recall', 'f1_score', 'average_precision', 'ndcg', 'mrr']
    available_corr = [m for m in correlation_metrics if m in df.columns]

    if len(available_corr) > 1:
        corr_matrix = df[available_corr].corr()
        for i, metric1 in enumerate(available_corr):
            analysis_results["correlation_matrix"][metric1] = {}
            for j, metric2 in enumerate(available_corr):
                analysis_results["correlation_matrix"][metric1][metric2] = float(corr_matrix.iloc[i, j])

    # 生成性能排名
    ranked_df = df.copy()
    ranked_df['rank'] = ranked_df['f1_score'].rank(ascending=False, method='min').astype(int)
    ranked_df = ranked_df.sort_values('rank')

    for _, row in ranked_df.head(20).iterrows():
        analysis_results["performance_ranking"].append({
            "rank": int(row['rank']),
            "question": row['question'],
            "f1_score": float(row['f1_score']),
            "precision": float(row['precision']),
            "recall": float(row['recall']),
            "average_precision": float(row.get('average_precision', 0)),
            "ndcg": float(row.get('ndcg', 0)),
            "mrr": float(row.get('mrr', 0))
        })

    return analysis_results


def generate_html_report(analysis_results: Dict[str, Any]) -> str:
    """
    根据分析结果生成HTML报告
    
    Args:
        analysis_results: analyze_metrics函数返回的分析结果
        
    Returns:
        HTML报告内容字符串
    """
    from datetime import datetime

    summary = analysis_results["summary"]
    distribution = analysis_results["distribution"]
    top_performers = analysis_results["top_performers"]
    top_k_analysis = analysis_results["top_k_analysis"]
    correlation_matrix = analysis_results["correlation_matrix"]
    performance_ranking = analysis_results["performance_ranking"]

    # 生成HTML内容
    html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>问答系统召回质量评估报告</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .header {{
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 40px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 25px;
            margin-bottom: 40px;
        }}
        .card {{
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s ease;
        }}
        .card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 16px rgba(0,0,0,0.15);
        }}
        .card h3 {{
            margin-top: 0;
            color: #555;
            font-size: 1.2em;
            margin-bottom: 15px;
        }}
        .card-value {{
            font-size: 2.8em;
            font-weight: bold;
            margin: 15px 0;
        }}
        .card-good {{ color: #28a745; }}
        .card-medium {{ color: #ffc107; }}
        .card-poor {{ color: #dc3545; }}
        .card-description {{
            color: #666;
            font-size: 0.95em;
            margin-top: 10px;
        }}
        .section {{
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        .section h2 {{
            color: #1e3c72;
            margin-top: 0;
            padding-bottom: 15px;
            border-bottom: 2px solid #e9ecef;
        }}
        .table-container {{
            overflow-x: auto;
            margin-top: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        th, td {{
            padding: 14px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: bold;
            color: #495057;
        }}
        tr:hover {{
            background-color: #f8f9fa;
        }}
        .metric-badge {{
            display: inline-block;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: bold;
        }}
        .badge-excellent {{ background-color: #d4edda; color: #155724; }}
        .badge-good {{ background-color: #cce5ff; color: #004085; }}
        .badge-fair {{ background-color: #fff3cd; color: #856404; }}
        .badge-poor {{ background-color: #f8d7da; color: #721c24; }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        .stat-item {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-label {{
            font-size: 0.9em;
            color: #6c757d;
            margin-bottom: 5px;
        }}
        .stat-value {{
            font-size: 1.5em;
            font-weight: bold;
            color: #1e3c72;
        }}
        .top-performer {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin: 15px 0;
            border-left: 4px solid #1e3c72;
        }}
        .top-performer h4 {{
            margin-top: 0;
            color: #1e3c72;
        }}
        .footer {{
            text-align: center;
            margin-top: 50px;
            color: #6c757d;
            font-size: 0.9em;
            padding-top: 20px;
            border-top: 1px solid #dee2e6;
        }}
        .highlight {{
            background: linear-gradient(120deg, #a1c4fd 0%, #c2e9fb 100%);
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }}
        .insight {{
            background: #e8f4f8;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
            border-left: 4px solid #17a2b8;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 问答系统召回质量评估报告</h1>
        <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 评估问题数量: {summary['total_questions']}</p>
        <p>本报告基于切片召回质量评估结果自动生成，用于分析问答系统的检索性能</p>
    </div>
    
    <div class="summary-cards">
        <div class="card">
            <h3>🎯 平均精确率</h3>
            <div class="card-value {'card-good' if summary['avg_precision'] > 0.7 else 'card-medium' if summary['avg_precision'] > 0.5 else 'card-poor'}">
                {summary['avg_precision']:.4f}
            </div>
            <div class="card-description">检索结果的相关性程度，值越高表示检索越准确</div>
        </div>
        
        <div class="card">
            <h3>🔍 平均召回率</h3>
            <div class="card-value {'card-good' if summary['avg_recall'] > 0.7 else 'card-medium' if summary['avg_recall'] > 0.5 else 'card-poor'}">
                {summary['avg_recall']:.4f}
            </div>
            <div class="card-description">检索到的相关文档比例，值越高表示覆盖越全面</div>
        </div>
        
        <div class="card">
            <h3>⚖️ 平均F1分数</h3>
            <div class="card-value {'card-good' if summary['avg_f1_score'] > 0.7 else 'card-medium' if summary['avg_f1_score'] > 0.5 else 'card-poor'}">
                {summary['avg_f1_score']:.4f}
            </div>
            <div class="card-description">精确率和召回率的调和平均，综合性能指标</div>
        </div>
        
        <div class="card">
            <h3>📈 平均NDCG</h3>
            <div class="card-value {'card-good' if summary['avg_ndcg'] > 0.7 else 'card-medium' if summary['avg_ndcg'] > 0.5 else 'card-poor'}">
                {summary['avg_ndcg']:.4f}
            </div>
            <div class="card-description">排序质量评估指标，考虑相关文档的位置</div>
        </div>
    </div>
    
    <div class="highlight">
        <h3>📋 报告摘要</h3>
        <p>本次评估共分析了 <strong>{summary['total_questions']}</strong> 个问题。系统整体表现：</p>
        <ul>
            <li><strong>精确率</strong>: {summary['avg_precision']:.2%} - 检索结果的相关性良好</li>
            <li><strong>召回率</strong>: {summary['avg_recall']:.2%} - 相关文档覆盖程度适中</li>
            <li><strong>F1分数</strong>: {summary['avg_f1_score']:.2%} - 综合性能表现{'优秀' if summary['avg_f1_score'] > 0.7 else '良好' if summary['avg_f1_score'] > 0.5 else '一般'}</li>
            <li><strong>排序质量</strong>: NDCG {summary['avg_ndcg']:.2%} - 检索结果排序{'合理' if summary['avg_ndcg'] > 0.7 else '一般'}</li>
        </ul>
    </div>
    
    <div class="section">
        <h2>📊 指标分布统计</h2>
        <div class="stats-grid">
            <div class="stat-item">
                <div class="stat-label">精确率分布</div>
                <div class="stat-value">{distribution['precision']['mean']:.4f}</div>
                <div>范围: {distribution['precision']['min']:.4f} - {distribution['precision']['max']:.4f}</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">召回率分布</div>
                <div class="stat-value">{distribution['recall']['mean']:.4f}</div>
                <div>范围: {distribution['recall']['min']:.4f} - {distribution['recall']['max']:.4f}</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">F1分数分布</div>
                <div class="stat-value">{distribution['f1_score']['mean']:.4f}</div>
                <div>范围: {distribution['f1_score']['min']:.4f} - {distribution['f1_score']['max']:.4f}</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">标准差</div>
                <div class="stat-value">{distribution['f1_score']['std']:.4f}</div>
                <div>F1分数波动程度</div>
            </div>
        </div>
        
        <div class="insight">
            <h4>📈 分布分析</h4>
            <p>指标标准差为 {distribution['f1_score']['std']:.4f}，表示不同问题的性能波动{'较小' if distribution['f1_score']['std'] < 0.15 else '适中' if distribution['f1_score']['std'] < 0.25 else '较大'}。</p>
            <p>中位数({distribution['f1_score']['median']:.4f})与平均值({distribution['f1_score']['mean']:.4f})的差异{'较小' if abs(distribution['f1_score']['median'] - distribution['f1_score']['mean']) < 0.05 else '明显'}，表明数据分布{'相对对称' if abs(distribution['f1_score']['median'] - distribution['f1_score']['mean']) < 0.05 else '存在偏斜'}。</p>
        </div>
    </div>
    
    <div class="section">
        <h2>🏆 最佳表现问题</h2>
        
        <div class="top-performer">
            <h4>🥇 最佳F1分数</h4>
            <p><strong>问题</strong>: {top_performers['best_f1']['question'][:100]}...</p>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-label">F1分数</div>
                    <div class="stat-value">{top_performers['best_f1']['f1_score']:.4f}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">精确率</div>
                    <div class="stat-value">{top_performers['best_f1']['precision']:.4f}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">召回率</div>
                    <div class="stat-value">{top_performers['best_f1']['recall']:.4f}</div>
                </div>
            </div>
        </div>
        
        <div class="top-performer">
            <h4>🎯 最佳精确率</h4>
            <p><strong>问题</strong>: {top_performers['best_precision']['question'][:100]}...</p>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-label">精确率</div>
                    <div class="stat-value">{top_performers['best_precision']['precision']:.4f}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">召回率</div>
                    <div class="stat-value">{top_performers['best_precision']['recall']:.4f}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">F1分数</div>
                    <div class="stat-value">{top_performers['best_precision']['f1_score']:.4f}</div>
                </div>
            </div>
        </div>
        
        <div class="insight">
            <h4>💡 性能洞察</h4>
            <p>最佳F1分数问题({top_performers['best_f1']['f1_score']:.2%})在精确率和召回率之间取得了良好平衡。</p>
            <p>最佳精确率问题({top_performers['best_precision']['precision']:.2%})虽然精确率很高，但召回率可能相对较低，需要进一步分析。</p>
        </div>
    </div>
    
    <div class="section">
        <h2>📋 问题性能排名 (Top 10)</h2>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>排名</th>
                        <th>问题</th>
                        <th>F1分数</th>
                        <th>精确率</th>
                        <th>召回率</th>
                        <th>AP</th>
                        <th>NDCG</th>
                        <th>状态</th>
                    </tr>
                </thead>
                <tbody>
"""

    # 添加表格行
    for i, item in enumerate(performance_ranking[:10], 1):
        f1_score = item['f1_score']
        if f1_score > 0.8:
            status_class = "badge-excellent"
            status_text = "优秀"
        elif f1_score > 0.6:
            status_class = "badge-good"
            status_text = "良好"
        elif f1_score > 0.4:
            status_class = "badge-fair"
            status_text = "一般"
        else:
            status_class = "badge-poor"
            status_text = "需改进"

        question_short = item['question'][:60] + "..." if len(item['question']) > 60 else item['question']

        html_content += f"""
                    <tr>
                        <td>{i}</td>
                        <td title="{item['question']}">{question_short}</td>
                        <td>{item['f1_score']:.4f}</td>
                        <td>{item['precision']:.4f}</td>
                        <td>{item['recall']:.4f}</td>
                        <td>{item['average_precision']:.4f}</td>
                        <td>{item['ndcg']:.4f}</td>
                        <td><span class="metric-badge {status_class}">{status_text}</span></td>
                    </tr>
        """

    html_content += """
                </tbody>
            </table>
        </div>
        
        <div class="insight">
            <h4>📊 排名分析</h4>
            <p>Top 10问题的平均F1分数为 {sum(item['f1_score'] for item in performance_ranking[:10])/10:.2%}，显著高于总体平均值({summary['avg_f1_score']:.2%})。</p>
            <p>排名靠前的问题通常具有更明确的查询意图和更标准化的答案格式。</p>
        </div>
    </div>
    
    <div class="section">
        <h2>📈 Top K指标分析</h2>
"""

    # 添加Top K分析
    if 'precision' in top_k_analysis:
        html_content += """
        <h3>Top K精确率</h3>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>K值</th>
                        <th>平均值</th>
                        <th>标准差</th>
                        <th>最小值</th>
                        <th>最大值</th>
                        <th>趋势</th>
                    </tr>
                </thead>
                <tbody>
        """

        for k, stats in sorted(top_k_analysis['precision'].items(), key=lambda x: int(x[0])):
            trend = "↗️ 上升" if k == '1' or stats['mean'] > \
                                 top_k_analysis['precision'].get(str(int(k) - 1), {'mean': 0})['mean'] else "↘️ 下降"
            html_content += f"""
                    <tr>
                        <td>{k}</td>
                        <td>{stats['mean']:.4f}</td>
                        <td>{stats['std']:.4f}</td>
                        <td>{stats['min']:.4f}</td>
                        <td>{stats['max']:.4f}</td>
                        <td>{trend}</td>
                    </tr>
            """

        html_content += """
                </tbody>
            </table>
        </div>
        """

    if 'recall' in top_k_analysis:
        html_content += """
        <h3>Top K召回率</h3>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>K值</th>
                        <th>平均值</th>
                        <th>标准差</th>
                        <th>最小值</th>
                        <th>最大值</th>
                        <th>趋势</th>
                    </tr>
                </thead>
                <tbody>
        """

        for k, stats in sorted(top_k_analysis['recall'].items(), key=lambda x: int(x[0])):
            trend = "↗️ 上升" if k == '1' or stats['mean'] > top_k_analysis['recall'].get(str(int(k) - 1), {'mean': 0})[
                'mean'] else "↘️ 下降"
            html_content += f"""
                    <tr>
                        <td>{k}</td>
                        <td>{stats['mean']:.4f}</td>
                        <td>{stats['std']:.4f}</td>
                        <td>{stats['min']:.4f}</td>
                        <td>{stats['max']:.4f}</td>
                        <td>{trend}</td>
                    </tr>
            """

        html_content += """
                </tbody>
            </table>
        </div>
        """

    html_content += """
        <div class="insight">
            <h4>📊 Top K分析洞察</h4>
            <p>Top K指标反映了系统在不同检索深度下的性能表现。通常，随着K值增加，精确率会下降而召回率会上升。</p>
            <p>理想情况下，系统应该在较小的K值下保持较高的精确率，同时在较大的K值下实现较高的召回率。</p>
        </div>
    </div>
    
    <div class="section">
        <h2>🔗 指标相关性分析</h2>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>指标</th>
    """

    # 添加相关性表头
    if correlation_matrix:
        metrics = list(correlation_matrix.keys())
        cn_names = [METRIC_NAMES_CN.get(m, m) for m in metrics]

        html_content += """
                        <th>""" + "</th><th>".join(cn_names) + """</th>
                    </tr>
                </thead>
                <tbody>
        """

        # 添加相关性数据行
        for i, metric in enumerate(metrics):
            cn_name = METRIC_NAMES_CN.get(metric, metric)
            html_content += f"""
                    <tr>
                        <td><strong>{cn_name}</strong></td>
            """

            for j, metric2 in enumerate(metrics):
                corr_value = correlation_matrix[metric][metric2]
                color_class = ""
                if corr_value > 0.7:
                    color_class = "badge-excellent"
                elif corr_value > 0.3:
                    color_class = "badge-good"
                elif corr_value > -0.3:
                    color_class = "badge-fair"
                else:
                    color_class = "badge-poor"

                html_content += f"""
                        <td><span class="metric-badge {color_class}">{corr_value:.3f}</span></td>
                """

            html_content += """
                    </tr>
            """

    html_content += """
                </tbody>
            </table>
        </div>
        
        <div class="insight">
            <h4>🔍 相关性洞察</h4>
            <p>指标相关性分析有助于理解不同评估指标之间的关系：</p>
            <ul>
                <li><strong>高正相关</strong>（>0.7）：指标变化趋势一致，可以相互印证</li>
                <li><strong>中等相关</strong>（0.3-0.7）：指标有一定关联，但各有侧重</li>
                <li><strong>低相关</strong>（<0.3）：指标相对独立，反映不同方面的性能</li>
                <li><strong>负相关</strong>：指标存在权衡关系，需要平衡考虑</li>
            </ul>
        </div>
    </div>
    
    <div class="section">
        <h2>💡 改进建议</h2>
        <div class="insight">
            <h4>🎯 基于分析结果的建议</h4>
            <p>根据本次评估结果，建议采取以下改进措施：</p>
            <ul>
                <li><strong>优化检索算法</strong>: 针对精确率较低的问题，优化查询理解和文档匹配策略</li>
                <li><strong>扩充知识库</strong>: 针对召回率较低的问题，补充相关文档和知识片段</li>
                <li><strong>改进排序模型</strong>: 针对NDCG较低的问题，优化结果排序算法</li>
                <li><strong>问题分类处理</strong>: 针对不同类型的问题采用不同的检索策略</li>
                <li><strong>持续监控</strong>: 建立定期评估机制，跟踪系统性能变化</li>
            </ul>
        </div>
    </div>
    
    <div class="footer">
        <p>📊 报告生成工具: 问答系统评估工具 | 版本: 1.0.0</p>
        <p>📅 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>⚠️ 注: 本报告基于自动化评估结果生成，建议结合人工分析进行决策</p>
    </div>
</body>
</html>
    """

    return html_content


# 使用示例
def main():
    """使用示例"""
    # 示例数据（模拟metric_all）
    example_metric_all = {
        "OSPF中Router ID的长度是多少位？": {
            "precision": 0.85,
            "recall": 0.90,
            "f1_score": 0.874,
            "precision_at_k": {1: 1.0, 3: 0.833, 5: 0.8, 10: 0.7},
            "recall_at_k": {1: 0.333, 3: 0.667, 5: 0.833, 10: 1.0},
            "average_precision": 0.912,
            "ndcg": 0.934,
            "mrr": 1.0,
            "hit_rate": 1.0,
            "coverage": 0.9,
            "redundancy": 0.1,
            "true_positives": 9,
            "false_positives": 1,
            "false_negatives": 1,
            "total_relevant": 10,
            "total_retrieved": 10
        },
        "OSPF报文头部长度是多少字节？": {
            "precision": 0.75,
            "recall": 0.80,
            "f1_score": 0.774,
            "precision_at_k": {1: 0.8, 3: 0.7, 5: 0.72, 10: 0.68},
            "recall_at_k": {1: 0.2, 3: 0.5, 5: 0.7, 10: 0.8},
            "average_precision": 0.782,
            "ndcg": 0.812,
            "mrr": 0.85,
            "hit_rate": 0.9,
            "coverage": 0.8,
            "redundancy": 0.15,
            "true_positives": 8,
            "false_positives": 2,
            "false_negatives": 2,
            "total_relevant": 10,
            "total_retrieved": 10
        }
    }

    # 测试analyze_metrics函数
    print("测试analyze_metrics函数...")
    analysis_results = analyze_metrics(example_metric_all)
    print(f"分析完成，共分析 {analysis_results['summary']['total_questions']} 个问题")
    print(f"平均F1分数: {analysis_results['summary']['avg_f1_score']:.4f}")

    # 测试generate_html_report函数
    print("\n测试generate_html_report函数...")
    html_content = generate_html_report(analysis_results)
    print(f"HTML报告生成完成，内容长度: {len(html_content)} 字符")

    # 保存测试报告
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_report_file = f"test_report_{timestamp}.html"

    with open(test_report_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"测试报告已保存到: {test_report_file}")

    # 测试MetricsVisualizer类
    print("\n测试MetricsVisualizer类...")
    visualizer = MetricsVisualizer(example_metric_all)
    visualizer.show_summary_statistics()

    print("\n✅ 所有测试完成！")


if __name__ == "__main__":
    main()
