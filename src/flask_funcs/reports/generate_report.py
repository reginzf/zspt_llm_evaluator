"""
问答系统召回质量评估报告生成器
使用Jinja2模板引擎生成美观的可视化报告
load_metric_data-->加载报告,返回json
generate_reports_from_metric-->加载load_metric_data的数据，生成html渲染器，分析数据并保存到本地
"""

import json
import os
import sys
from typing import Dict, List, Any, Optional
from pathlib import Path
from env_config_init import REPORT_PATH
try:
    from .metrics_analyzer import analyze_metrics
    from .html_renderer import HTMLRenderer
except ImportError:
    from src.flask_funcs.reports.metrics_analyzer import analyze_metrics
    from src.flask_funcs.reports.html_renderer import HTMLRenderer

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def load_metric_data(filepath: str, report_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """
    加载metric数据

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


def generate_reports_from_metric_files(report_path: Optional[Path] = None) -> List[Path]:
    """
    从REPORT_PATH读取所有metric开头的JSON文件，为每个文件生成对应的报告

    功能实现：
    1. 读取REPORT_PATH，过滤以"metric"开头".json"结尾的文件，作为数据的输入文件
    2. 分析数据，生成analysis_results并生成报告，报告名称和输入文件名称一一对应
    3. 完成之后保存报告文件到REPORT_PATH下面

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

    # 创建HTML渲染器
    renderer = HTMLRenderer()

    for file_name, metric_data in name_file_map.items():
        # 提取文件名（不含扩展名）
        base_name = Path(file_name).stem

        # 分析数据
        analysis_results = analyze_metrics(metric_data)

        # 生成html报告
        html_content = renderer.render_metrics_dashboard(analysis_results,metric_data)

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


if __name__ == "__main__":
    main()