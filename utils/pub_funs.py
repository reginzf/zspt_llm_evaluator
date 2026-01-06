from typing import Dict, Any, Optional
from pathlib import Path
import json
from env_config_init import  REPORT_PATH

def load_json_file(file_path: str) -> Dict[str, Any]:
    """从文件加载JSON数据"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json_file(data: Dict[str, Any], file_path: str):
    """保存JSON数据到文件"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def save_xml_file(xml_content: str, file_path: str):
    """保存XML到文件"""
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(xml_content)


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
