from typing import Dict, Any
import json
from jsonpath import jsonpath


def load_json_file(file_path: str) -> Dict[str, Any]:
    """从文件加载JSON数据"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_xml_file(xml_content: str, file_path: str):
    """保存XML到文件"""
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(xml_content)
