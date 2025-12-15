from typing import Dict, Any
from pathlib import Path
import json


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


if __name__ == "__main__":
    from env_config_init import settings

    try:
        # 使用默认路径
        paths = get_test_paths(settings.TEST_PATH)
        print("项目根目录:", paths["project_root"])
        print("测试目录:", paths["target_dir"])
        print("docs目录:", paths["docs_dir"])
        print("questions:", paths["questions"])
        print("ls_labeled_chunks目录:", paths["ls_labeled_chunks_dir"])
        print("lzpt_chunks目录:", paths["lzpt_chunks_dir"])

        # 或者指定其他相对路径
        # paths = get_ospf_test_paths("tests\\bgp")  # 用于其他协议测试

    except FileNotFoundError as e:
        print(f"错误: {e}")
