"""
metric_all数据可视化展示模块
提供多种美观直观的方式展示切片召回质量评估结果
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
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

    def _create_pr_scatter_plot(self) -> None:
        """创建精确率-召回率散点图"""
        self.fig.add_trace(
            go.Scatter(
                x=self.df['recall'],
                y=self.df['precision'],
                mode='markers',
                marker=dict(
                    size=10,
                    color=self.df['f1_score'],
                    colorscale='Viridis',
                    showscale=False
                ),
                text=self.df['question'].str[:50],
                hoverinfo='text+x+y',
                name='问题'
            ),
            row=1, col=1
        )
        self.fig.update_xaxes(title_text="召回率", row=1, col=1)
        self.fig.update_yaxes(title_text="精确率", row=1, col=1)

    def _create_f1_histogram(self) -> None:
        """创建F1分数分布直方图"""
        self.fig.add_trace(
            go.Histogram(
                x=self.df['f1_score'],
                nbinsx=20,
                marker_color='skyblue',
                name='F1分布'
            ),
            row=1, col=2
        )
        self.fig.update_xaxes(title_text="F1分数", row=1, col=2)
        self.fig.update_yaxes(title_text="数量", row=1, col=2)

    def _create_precision_at_k_plot(self) -> None:
        """创建Top K精确率折线图"""
        k_values, avg_precision_at_k = self._get_top_k_columns('precision@')
        if k_values:
            self.fig.add_trace(
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
            self.fig.update_xaxes(title_text="K值", row=1, col=3)
            self.fig.update_yaxes(title_text="精确率", row=1, col=3)

    def _create_recall_at_k_plot(self) -> None:
        """创建Top K召回率折线图"""
        k_values, avg_recall_at_k = self._get_top_k_columns('recall@')
        if k_values:
            self.fig.add_trace(
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
            self.fig.update_xaxes(title_text="K值", row=2, col=1)
            self.fig.update_yaxes(title_text="召回率", row=2, col=1)

    def _create_ranking_metrics_bar(self) -> None:
        """创建排序指标对比柱状图"""
        ranking_metrics = ['average_precision', 'ndcg', 'mrr']
        available_metrics = [m for m in ranking_metrics if m in self.df.columns]

        if available_metrics:
            avg_values = [self.df[m].mean() for m in available_metrics]
            cn_names = [METRIC_NAMES_CN.get(m, m) for m in available_metrics]

            self.fig.add_trace(
                go.Bar(
                    x=cn_names,
                    y=avg_values,
                    marker_color=['#FF6B6B', '#4ECDC4', '#45B7D1'],
                    name='排序指标'
                ),
                row=2, col=2
            )
            self.fig.update_xaxes(title_text="指标", row=2, col=2)
            self.fig.update_yaxes(title_text="平均值", row=2, col=2)

    def _create_hit_coverage_scatter(self) -> None:
        """创建命中率与recall_at_k的散点图"""
        # 首先检查是否有hit_rate和recall_at_k相关列
        if 'hit_rate' not in self.df.columns:
            return  # 如果没有命中率数据，则跳过此图
        
        # 查找可用的recall@k列
        recall_at_k_columns = [col for col in self.df.columns if col.startswith('recall@')]
        
        if not recall_at_k_columns:
            # 如果没有找到recall@k列，可以尝试使用总的recall
            if 'recall' in self.df.columns:
                self.fig.add_trace(
                    go.Scatter(
                        x=self.df['recall'],
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
                        name='命中率 vs 召回率'
                    ),
                    row=2, col=3
                )
                self.fig.update_xaxes(title_text="召回率", row=2, col=3)
                self.fig.update_yaxes(title_text="命中率", row=2, col=3)
        else:
            # 如果找到recall@k列，使用最大k值的列
            recall_at_k_columns.sort(key=lambda x: int(x.split('@')[1]))  # 按k值排序
            max_k_column = recall_at_k_columns[-1]  # 选择最大k值的列
            
            if max_k_column in self.df.columns:
                self.fig.add_trace(
                    go.Scatter(
                        x=self.df[max_k_column],
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
                        name=f'命中率 vs {max_k_column}'
                    ),
                    row=2, col=3
                )
                self.fig.update_xaxes(title_text=f"{max_k_column} (召回率@k)", row=2, col=3)
                self.fig.update_yaxes(title_text="命中率", row=2, col=3)

    def _create_performance_heatmap(self) -> None:
        """创建问题性能热图"""
        top_questions = self.df.nlargest(10, 'f1_score')
        metrics_for_heatmap = ['precision', 'recall', 'f1_score', 'average_precision', 'ndcg']
        available_for_heatmap = [m for m in metrics_for_heatmap if m in top_questions.columns]
        # 计算位置
        location = self.get_subplot_relative_position(3, 1)
        x_right = location['x_domain'][1]
        y_bottom = location['y_domain'][0] - 0.01
        y_height = (location['y_domain'][1] - location['y_domain'][0]) * 1.1
        if len(available_for_heatmap) > 0:
            heatmap_data = top_questions[available_for_heatmap].values.T
            cn_labels = [METRIC_NAMES_CN.get(m, m) for m in available_for_heatmap]

            # 准备hover文本数据
            questions_text = top_questions['question'].str[:50].tolist()
            x_labels = [f"Q{i + 1}" for i in range(len(top_questions))]

            # 构建hover文本矩阵
            hover_text = []
            for i, metric in enumerate(cn_labels):
                row_text = []
                for j, question_text in enumerate(questions_text):
                    row_text.append(f"问题: {question_text}<br>指标: {metric}<br>值: {heatmap_data[i][j]:.3f}")
                hover_text.append(row_text)

            self.fig.add_trace(
                go.Heatmap(
                    z=heatmap_data,
                    x=x_labels,
                    y=cn_labels,
                    text=hover_text,
                    hoverinfo='text',
                    colorscale='YlOrRd',
                    showscale=True,
                    colorbar=dict(
                        x=x_right,  # 靠近子图右侧
                        xanchor="left",  # 左侧对齐
                        y=y_bottom,  # 靠近子图底部
                        yanchor="bottom",  # 底部对齐
                        len=y_height,  # 长度等于子图高度
                        orientation='v',  # 垂直方向
                        tickmode="array",
                        tickvals=[-1, -0.5, 0, 0.5, 1],
                        ticktext=["-1", "-0.5", "0", "0.5", "1"]
                    )
                ),
                row=3, col=1
            )

    def _create_correlation_heatmap(self) -> None:
        """创建指标相关性热图"""
        correlation_metrics = ['precision', 'recall', 'f1_score', 'average_precision', 'ndcg', 'mrr']
        available_corr = [m for m in correlation_metrics if m in self.df.columns]
        location = self.get_subplot_relative_position(3, 2)
        x_right = location['x_domain'][1]
        y_bottom = location['y_domain'][0] - 0.01
        y_height = (location['y_domain'][1] - location['y_domain'][0]) * 1.1
        if len(available_corr) > 1:
            corr_matrix = self.df[available_corr].corr()
            cn_labels_corr = [METRIC_NAMES_CN.get(m, m) for m in available_corr]

            self.fig.add_trace(
                go.Heatmap(
                    z=corr_matrix.values,
                    x=cn_labels_corr,
                    y=cn_labels_corr,
                    colorscale='RdBu',
                    zmid=0,
                    showscale=True,
                    colorbar=dict(
                        x=x_right,  # 靠近子图右侧
                        xanchor="left",  # 左侧对齐
                        y=y_bottom,  # 靠近子图底部
                        yanchor="bottom",  # 底部对齐
                        len=y_height,  # 长度等于子图高度
                        orientation='v',  # 垂直方向
                        tickmode="array",
                        tickvals=[-1, -0.5, 0, 0.5, 1],
                        ticktext=["-1", "-0.5", "0", "0.5", "1"]
                    )
                ),
                row=3, col=2
            )

    def _create_performance_ranking_bar(self) -> None:
        """创建性能排名条形图"""
        top_n = min(15, len(self.df))
        top_questions = self.df.nlargest(top_n, 'f1_score')

        self.fig.add_trace(
            go.Bar(
                y=[f"Q{i + 1}" for i in range(len(top_questions))],
                x=top_questions['f1_score'],
                orientation='h',
                marker_color='lightgreen',
                text=[f"{score:.3f}" for score in top_questions['f1_score']],
                textposition='auto',
                name='F1分数排名',
                customdata=top_questions['question'].str[:50],  # 添加自定义数据
                hovertemplate='<b>%{y}</b><br>F1分数: %{x:.3f}<br>问题: %{customdata}<extra></extra>'  # 自定义悬停模板
            ),
            row=3, col=3
        )
        self.fig.update_xaxes(title_text="F1分数", row=3, col=3)

    def create_interactive_dashboard(self, output_file: str = "metrics_dashboard.html", save_to_html=True):
        """创建交互式仪表板"""
        # 创建子图
        self.fig: go.Figure = make_subplots(
            rows=3, cols=3,
            subplot_titles=('精确率 vs 召回率', 'F1分数分布', 'Top K精确率',
                            'Top K召回率', '排序指标对比', '命中率与覆盖率',
                            '问题性能热图', '指标相关性', '性能排名'),
            specs=[[{'type': 'scatter'}, {'type': 'histogram'}, {'type': 'scatter'}],
                   [{'type': 'scatter'}, {'type': 'bar'}, {'type': 'scatter'}],
                   [{'type': 'heatmap'}, {'type': 'heatmap'}, {'type': 'bar'}]]
        )
        # 添加各个子图
        self._create_pr_scatter_plot()
        self._create_f1_histogram()
        self._create_precision_at_k_plot()
        self._create_recall_at_k_plot()
        self._create_ranking_metrics_bar()
        self._create_hit_coverage_scatter()
        self._create_performance_heatmap()
        self._create_correlation_heatmap()
        self._create_performance_ranking_bar()

        # 更新布局
        self.fig.update_layout(
            height=1200,
            width=1400,
            title_text="切片召回质量评估仪表板",
            showlegend=False,
            template="plotly_white"
        )

        # 保存为HTML文件
        if save_to_html:
            self.fig.write_html(output_file)
        else:  # 返回html，用于插入HTMLRenderer中，进行渲染
            return self.fig.to_html(include_plotlyjs=True)
        print(f"✅ 交互式仪表板已保存到: {output_file}")

        return self.fig

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

    def get_subplot_relative_position(self, row: int, col: int) -> Optional[Dict[str, float]]:
        """
        只获取子图的相对位置信息（0-1比例）
        这是最稳定的方法，不依赖像素计算
        """
        if self.fig is None:
            return None

        try:
            # 方法1：尝试使用轴域
            subplot_index = (row - 1) * 3 + col

            # 获取轴对象
            if subplot_index == 1:
                xaxis = self.fig.layout.xaxis
                yaxis = self.fig.layout.yaxis
            else:
                xaxis = getattr(self.fig.layout, f'xaxis{subplot_index}', None)
                yaxis = getattr(self.fig.layout, f'yaxis{subplot_index}', None)

            if xaxis is None or yaxis is None:
                print(f"无法找到子图 (row={row}, col={col}) 的轴配置")
                return None

            # 获取域
            x_domain = getattr(xaxis, 'domain', [0.0, 1.0])
            y_domain = getattr(yaxis, 'domain', [0.0, 1.0])

            # 标准化域值
            if x_domain is None:
                x_domain = [0.0, 1.0]
            if y_domain is None:
                y_domain = [0.0, 1.0]

            # 转换为列表并获取数值
            x_start = float(list(x_domain)[0])
            x_end = float(list(x_domain)[1])
            y_start = float(list(y_domain)[0])
            y_end = float(list(y_domain)[1])

            return {
                'row': row,
                'col': col,
                'x': x_start,
                'y': y_start,
                'width': x_end - x_start,
                'height': y_end - y_start,
                'x_domain': [x_start, x_end],
                'y_domain': [y_start, y_end]
            }

        except Exception as e:
            print(f"获取子图位置时出错: {e}")
            return None

    def export_to_excel(self, output_file: str = "metrics_report.xlsx"):
        """导出为Excel文件"""
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # 创建各个工作表
            self._create_detailed_sheet(writer)
            self._create_summary_sheet(writer)
            self._create_top_k_sheet(writer)
            self._create_ranking_sheet(writer)

        print(f"✅ Excel报告已保存到: {output_file}")


if __name__ == '__main__':
    from reports.reports_funcs.generate_report import load_metric_data
    from pathlib import Path

    data = load_metric_data(
        r'D:\pyworkplace\git_place\ai-ken\reports\report_data\ospf\metric_chunk_id_augmentedSearch_400_0.json',
        Path(r'D:\pyworkplace\git_place\ai-ken\reports\report_data\ospf'))
    mev = MetricsVisualizer(data)
    mev.create_interactive_dashboard("ospf_dashboard.html")
