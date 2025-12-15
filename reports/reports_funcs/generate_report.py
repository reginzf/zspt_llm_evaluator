#!/usr/bin/env python3
"""
OSPF问答系统召回质量评估报告生成器
用于分析metric_all数据并生成美观的可视化报告
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
import numpy as np
from pathlib import Path
from env_config_init import REPORT_PATH

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from visualize_metrics import analyze_metrics, generate_html_report


def load_metric_data(filepath: str, report_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """
    加载metric_all数据
    
    Args:
        filepath: 文件名
        report_path: 报告路径，如果为None则使用默认的REPORT_PATH
    
    Returns:
        metric数据字典，如果加载失败则返回None
    """
    # 使用指定的report_path或默认的REPORT_PATH
    target_path = report_path if report_path else REPORT_PATH
    metric_file = target_path / filepath
    
    if metric_file.exists():
        print(f"从文件加载metric数据: {metric_file}")
        try:
            with open(metric_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载文件 {metric_file} 时出错: {e}")
            return None
    else:
        print(f"无法加载metric数据: {metric_file} 不存在")
        return None


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


def generate_reports_from_metric_files(report_path: Optional[Path] = None) -> List[Path]:
    """
    从REPORT_PATH读取所有metric开头的JSON文件，为每个文件生成对应的报告
    
    Args:
        report_path: 报告路径，如果为None则使用默认的REPORT_PATH
    
    Returns:
        list: 生成的报告文件路径列表
    """
    from datetime import datetime
    
    # 使用指定的report_path或默认的REPORT_PATH
    target_path = report_path if report_path else REPORT_PATH
    
    print("=" * 60)
    print("问答系统召回质量评估报告生成器")
    print("=" * 60)

    # 1、查看REPORT_PATH下有几个metric_all_xxx.json文件，并加载数据
    print("\n1. 加载metric数据...")
    metric_json_files = [f for f in os.listdir(target_path) if f.startswith("metric") and f.endswith(".json")]
    
    if not metric_json_files:
        print(f"错误: {target_path}不存在metric开头的json文件")
        return []
    
    name_file_map = {}
    for metric_json_file in metric_json_files:
        metric_data = load_metric_data(metric_json_file, target_path)
        if metric_data:
            name_file_map[metric_json_file] = metric_data
            print(f"已加载 {metric_json_file}, 问题{len(metric_data)}个")
        else:
            print(f"警告: 无法加载 {metric_json_file}")

    if not name_file_map:
        print("错误: 没有成功加载任何metric数据文件")
        return []

    # 2. 分析数据并生成报告
    print("\n2. 分析metric数据并生成报告...")
    report_files = []
    for file_name, metric_data in name_file_map.items():
        # 提取文件名（不含扩展名）
        base_name = Path(file_name).stem
        
        # 分析数据
        analysis_results = analyze_metrics(metric_data)
        
        # 生成html报告
        html_content = generate_html_report(analysis_results)
        
        # 保存html报告，使用输入文件名作为报告名称的一部分
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = target_path / f"report_{base_name}_{timestamp}.html"
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            file_size_kb = os.path.getsize(report_file) / 1024
            print(f"\n报告已生成: {report_file}")
            print(f"文件大小: {file_size_kb:.1f} KB")
            report_files.append(report_file)
        except Exception as e:
            print(f"保存报告文件 {report_file} 时出错: {e}")
    
    return report_files


def main():
    """主函数：生成评估报告"""
    # 使用新的函数生成报告
    report_files = generate_reports_from_metric_files()
    
    if not report_files:
        return
    
    # 尝试在浏览器中打开报告
    print("\n3. 尝试打开报告...")
    try:
        import webbrowser
        for file in report_files:
            webbrowser.open(f"file://{file}")
            print(f"已在浏览器中打开报告: {file.name}")
    except Exception as e:
        print(f"打开浏览器时出错: {e}")
        print("请手动打开报告文件查看")
    
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