#!/usr/bin/env python3
"""
OSPF问答系统召回质量评估报告生成器
用于分析metric_all数据并生成美观的可视化报告
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Tuple
import numpy as np
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from visualize_metrics import analyze_metrics, generate_html_report


def load_metric_data() -> Dict[str, Any]:
    """
    加载metric_all数据
    这里假设metric_all已经通过main.py运行并保存到文件
    或者可以直接从内存中获取
    """
    # 方法1: 如果metric_all已经保存到文件
    metric_file = project_root.parent / "report_data" / "metric_all.json"
    if metric_file.exists():
        print(f"从文件加载metric数据: {metric_file}")
        with open(metric_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    # 方法2: 运行main.py获取metric_all
    # print("运行main.py获取metric数据...")
    # try:
    #     # 导入main模块并运行
    #     import main
    #     from main import main as run_main
    #
    #     # 这里需要修改main.py，使其返回metric_all
    #     # 或者通过其他方式获取metric_all
    #     print("注意: 需要修改main.py使其返回metric_all")
    #     print("或者手动提供metric_all数据")
    #
    #     # 临时示例数据
    #     return generate_sample_data()
    #
    # except Exception as e:
    #     print(f"运行main.py时出错: {e}")
    #     print("使用示例数据生成报告...")
    #     return generate_sample_data()


def generate_sample_data() -> Dict[str, Any]:
    """生成示例metric_all数据用于测试"""
    sample_metrics = {
        "precision": 0.75,
        "recall": 0.60,
        "f1_score": 0.6667,
        "precision_at_k": {1: 0.8, 3: 0.7, 5: 0.72, 10: 0.75},
        "recall_at_k": {1: 0.2, 3: 0.5, 5: 0.6, 10: 0.6},
        "average_precision": 0.68,
        "mean_average_precision": 0.68,
        "ndcg": 0.72,
        "mrr": 0.65,
        "hit_rate": 0.85,
        "coverage": 0.60,
        "redundancy": 0.10,
        "true_positives": 3,
        "false_positives": 1,
        "false_negatives": 2,
        "total_relevant": 5,
        "total_retrieved": 4
    }

    # 生成10个示例问题
    questions = [
        "OSPF中Router ID的长度是多少位？",
        "OSPF报文头部长度是多少字节？",
        "在广播网络中，OSPF路由器如何发现邻居？",
        "在点到点网络中，OSPF路由器如何建立邻接关系？",
        "解释OSPF中链路状态通告（LSA）的概念和结构",
        "解释OSPF中链路状态数据库（LSDB）的组织方式",
        "在一个复杂的OSPF网络中，如果出现路由环路，如何诊断和解决？",
        "如何配置ospf邻居?",
        "OSPF支持的最大度量值是多少？",
        "OSPF中，DR和BDR的作用是什么？"
    ]

    metric_all = {}
    for i, question in enumerate(questions):
        # 为每个问题生成略有不同的指标
        metrics = sample_metrics.copy()
        # 添加一些随机变化
        variation = 0.1 * (i / len(questions))
        for key in ['precision', 'recall', 'f1_score', 'ndcg', 'mrr']:
            if key in metrics:
                metrics[key] = max(0, min(1, metrics[key] + (np.random.random() - 0.5) * variation))

        metric_all[question] = metrics

    return metric_all


def save_metric_data(metric_all: Dict[str, Any], output_file: str = "metric_all.json"):
    """保存metric_all数据到文件"""
    output_path = project_root.parent / "report_data" / output_file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metric_all, f, ensure_ascii=False, indent=2)
    print(f"metric数据已保存到: {output_path}")


def main():
    """主函数：生成评估报告"""
    print("=" * 60)
    print("问答系统召回质量评估报告生成器")
    print("=" * 60)

    # 1. 加载metric_all数据
    print("\n1. 加载metric数据...")
    metric_all = load_metric_data()

    if not metric_all:
        print("错误: 无法加载metric数据")
        return

    print(f"加载了 {len(metric_all)} 个问题的metric数据")

    # 2. 分析数据
    print("\n2. 分析metric数据...")
    analysis_results = analyze_metrics(metric_all)

    # 3. 生成HTML报告
    print("\n3. 生成HTML报告...")
    html_content = generate_html_report(analysis_results)

    # 4. 保存报告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = project_root.parent / "report_data" / f"metrics_report_{timestamp}.html"

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"\n报告已生成: {report_file}")
    print(f"文件大小: {os.path.getsize(report_file) / 1024:.1f} KB")

    # 5. 在浏览器中打开报告（可选）
    try:
        import webbrowser
        webbrowser.open(f"file://{report_file}")
        print("已在浏览器中打开报告")
    except:
        print("请手动打开报告文件查看")

    # 6. 保存原始数据（可选）
    save_option = input("\n是否保存metric_all数据到文件？(y/n): ")
    if save_option.lower() == 'y':
        save_metric_data(metric_all)

    print("\n" + "=" * 60)
    print("报告生成完成！")
    print("=" * 60)


def quick_generate():
    """快速生成报告（不运行main.py）"""
    print("快速生成评估报告...")

    # 生成示例数据
    metric_all = generate_sample_data()

    # 分析数据
    analysis_results = analyze_metrics(metric_all)

    # 生成报告
    html_content = generate_html_report(analysis_results)

    # 保存报告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = project_root.parent / "report_data" / f"quick_report_{timestamp}.html"

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"快速报告已生成: {report_file}")

    # 在浏览器中打开
    try:
        import webbrowser
        webbrowser.open(f"file://{report_file}")
    except:
        pass


if __name__ == "__main__":
    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        quick_generate()
    else:
        main()
