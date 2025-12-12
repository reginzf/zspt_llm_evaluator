# 问答系统召回质量评估可视化工具

## 概述

本工具用于分析和可视化问答系统的向量检索召回质量。通过分析`metric_all`数据，生成美观、交互式的HTML报告，帮助您直观地了解系统性能。

## 文件结构

```
reports_funs/
├── visualize_metrics.py       # 核心分析模块
├── generate_report.py         # 报告生成主程序
├── metrics_report_template.html  # HTML报告模板
├── report_config.json         # 配置文件
└── README_metrics_visualization.md  # 本文件
```

## 快速开始

### 方法1：使用示例数据快速生成报告

```bash
cd D:\pyworkplace\git_place\ai-ken
python generate_report.py --quick
```

### 方法2：运行完整流程

1. **首先运行main.py获取metric_all数据**：
   ```bash
   python main.py
   ```
   *注意：需要确保main.py正确运行并生成metric_all数据*

2. **生成可视化报告**：
   ```bash
   python generate_report.py
   ```

## metric_all数据结构

`metric_all`是一个字典，结构如下：
```python
{
    "问题文本1": {
        "precision": 0.75,           # 准确率
        "recall": 0.60,             # 召回率
        "f1_score": 0.6667,         # F1分数
        "precision_at_k": {         # Top K准确率
            1: 0.8,
            3: 0.7,
            5: 0.72,
            10: 0.75
        },
        "recall_at_k": {            # Top K召回率
            1: 0.2,
            3: 0.5,
            5: 0.6,
            10: 0.6
        },
        "average_precision": 0.68,  # 平均准确率
        "ndcg": 0.72,               # 归一化折损累计增益
        "mrr": 0.65,                # 平均倒数排名
        "hit_rate": 0.85,           # 命中率
        "coverage": 0.60,           # 覆盖率
        "redundancy": 0.10,         # 冗余度
        "true_positives": 3,        # 真正例
        "false_positives": 1,       # 假正例
        "false_negatives": 2,       # 假负例
        "total_relevant": 5,        # 总相关文档数
        "total_retrieved": 4        # 总检索文档数
    },
    "问题文本2": { ... },
    ...
}
```

## 报告内容

生成的HTML报告包含以下部分：

### 1. 摘要卡片
- 平均准确率、召回率、F1分数、NDCG
- 进度条直观显示性能水平

### 2. Top K指标分析
- **准确率@K折线图**：显示不同K值下的准确率变化
- **召回率@K折线图**：显示不同K值下的召回率变化

### 3. 问题性能分布
- **F1分数分布条形图**：按性能等级（优秀/中等/需改进）分组
- **排序质量指标雷达图**：显示AP、NDCG、MRR、命中率、覆盖率

### 4. 详细问题分析表
- 每个问题的详细指标
- 性能状态标签（优秀/中等/需改进）
- 支持展开/收起详细视图

### 5. 相关性分析
- **准确率 vs 召回率散点图**：显示问题分布
- **性能热力图**：显示指标间相关性

## 自定义配置

修改`report_config.json`文件可以自定义报告：

```json
{
  "report_settings": {
    "title": "自定义报告标题",
    "chart_colors": {
      "primary": "#你的主色",
      "secondary": "#你的辅色"
    },
    "metrics_thresholds": {
      "excellent": 0.8,  # 优秀阈值
      "good": 0.6,       # 良好阈值
      "fair": 0.4        # 中等阈值
    }
  }
}
```

## 高级用法

### 1. 修改main.py以返回metric_all

在`main.py`的`main()`函数末尾添加：
```python
def main():
    # ... 现有代码 ...
    
    # 在循环结束后返回metric_all
    return metric_all

if __name__ == '__main__':
    metric_all = main()
    # 可以在这里保存metric_all到文件
    import json
    with open('metric_all.json', 'w', encoding='utf-8') as f:
        json.dump(metric_all, f, ensure_ascii=False, indent=2)
```

### 2. 从文件加载metric_all

如果已经将metric_all保存为JSON文件：
```python
import json
with open('metric_all.json', 'r', encoding='utf-8') as f:
    metric_all = json.load(f)
```

### 3. 自定义可视化

修改`visualize_metrics.py`中的函数：
- `analyze_metrics()`: 添加自定义分析逻辑
- `generate_html_report()`: 修改报告结构

## 故障排除

### 问题1: 无法导入模块
**错误**: `ModuleNotFoundError: No module named 'src'`
**解决**: 确保在项目根目录运行，或添加项目路径：

```python
import sys

sys.path.insert(0, '/')
```

### 问题2: metric_all为空
**错误**: `metric_all`字典为空
**解决**: 
1. 检查main.py是否正确运行
2. 确保`calculate_chunk_recall_metrics`函数被调用
3. 使用`--quick`参数生成示例报告测试

### 问题3: 图表不显示
**解决**:
1. 检查网络连接（图表使用CDN）
2. 确保浏览器支持JavaScript
3. 查看浏览器控制台错误信息

## 性能指标说明

| 指标 | 说明 | 理想值 |
|------|------|--------|
| **准确率** | 检索结果中相关文档的比例 | >0.7 |
| **召回率** | 检索到的相关文档占所有相关文档的比例 | >0.6 |
| **F1分数** | 准确率和召回率的调和平均 | >0.65 |
| **NDCG** | 考虑排序位置的归一化指标 | >0.7 |
| **MRR** | 第一个相关结果排名的倒数 | >0.6 |
| **命中率** | 至少命中一个相关文档的概率 | >0.8 |

## 扩展功能建议

1. **导出功能**: 添加PDF/Excel导出
2. **比较功能**: 比较不同参数配置的结果
3. **趋势分析**: 分析性能随时间的变化
4. **预警系统**: 当指标低于阈值时发送警报
5. **API接口**: 提供REST API获取报告数据

## 技术支持

如有问题，请检查：
1. Python版本 >= 3.7
2. 必要的依赖包已安装
3. 文件路径权限正确
4. 网络连接正常（用于加载Chart.js）

## 更新日志

### v1.0.0 (2025-12-12)
- 初始版本发布
- 支持metric_all数据分析
- 生成交互式HTML报告
- 包含6种可视化图表
- 支持示例数据快速测试