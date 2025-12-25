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


def get_test_paths(relative_path) -> Dict[str, str]:
    """
    获取OSPF测试相关目录和文件的绝对路径

    Args:
        relative_path: 相对于项目根目录的路径，默认为"tests\\ospf"

    Returns:
        包含以下键的字典：
        - "project_root": 项目根目录绝对路径
        - "target_dir": OSPF测试目录绝对路径
        - "docs_dir": docs目录绝对路径
        - "questions_json": questions.json文件绝对路径
        - "ls_labeled_chunks_dir": ls_labeled_chunks目录绝对路径
        - "lzpt_chunks_dir": lzpt_chunks目录绝对路径
    """
    # 获取当前文件的绝对路径
    current_file_path = Path(__file__).resolve()
    project_root = None
    for parent in current_file_path.parents:
        if (parent / "main.py").exists():
            project_root = parent
            break

    # 构建完整路径
    target_dir = project_root / 'tests' /relative_path    # 固定放在tests目录下
    # 验证路径是否存在
    if not target_dir.exists():
        raise FileNotFoundError(f"测试目录不存在: {target_dir}")
    # 构建各个子路径
    paths = {
        "project_root": str(project_root),
        "target_dir": str(target_dir),
        "docs_dir": str(target_dir / "docs"),
        "questions": str(target_dir / "questions"),
        "ls_labeled_chunks_dir": str(target_dir / "ls_labeled_chunks"),
        "lzpt_chunks_dir": str(target_dir / "lzpt_chunks"),
    }

    # 验证各个子路径是否存在
    for key, path_str in paths.items():
        path = Path(path_str)
        if key not in ["project_root"] and not path.exists():
            print(f"警告: {key} 路径不存在: {path_str}")
            path.mkdir()

    return paths



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
