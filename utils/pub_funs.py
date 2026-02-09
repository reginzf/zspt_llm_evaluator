from env_config_init import REPORT_PATH
import json

from pathlib import Path
from typing import Union, Dict, List, Any, Optional


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


def safe_json_load(json_string: str, default: Any = None) -> Any:
    """
    安全解析JSON字符串

    Args:
        json_string: JSON字符串
        default: 解析失败时的默认值

    Returns:
        解析结果或默认值
    """
    try:
        if not json_string or not isinstance(json_string, str):
            return default
        return json.loads(json_string)
    except json.JSONDecodeError:
        return default


def safe_json_dump(data: Any,
                   ensure_ascii: bool = False,
                   indent: int = 2) -> Optional[str]:
    """
    安全序列化为JSON字符串

    Args:
        data: 要序列化的数据
        ensure_ascii: 是否转义非ASCII字符
        indent: 缩进空格数

    Returns:
        JSON字符串或None
    """
    try:
        return json.dumps(data, ensure_ascii=ensure_ascii, indent=indent)
    except Exception:
        return None


def read_json_file(file_path: Union[str, Path],
                   encoding: str = 'utf-8',
                   default: Any = None) -> Any:
    """
    安全读取JSON文件

    Args:
        file_path: JSON文件路径
        encoding: 文件编码
        default: 文件不存在或读取失败时的默认值

    Returns:
        解析后的JSON数据或默认值
    """
    try:
        path = Path(file_path)
        if not path.exists():
            if default is not None:
                return default
            raise FileNotFoundError(f"文件不存在: {file_path}")

        with open(path, 'r', encoding=encoding) as f:
            return json.load(f)

    except json.JSONDecodeError as e:
        print(f"✗ JSON解析错误 ({file_path}): {e}")
        if default is not None:
            return default
        raise
    except Exception as e:
        print(f"✗ 读取JSON文件失败 ({file_path}): {e}")
        if default is not None:
            return default
        raise


def write_json_file(file_path: Union[str, Path],
                    data: Any,
                    encoding: str = 'utf-8',
                    ensure_ascii: bool = False,
                    indent: int = 2,
                    create_dirs: bool = True) -> bool:
    """
    安全写入JSON文件

    Args:
        file_path: JSON文件路径
        data: 要写入的数据
        encoding: 文件编码
        ensure_ascii: 是否转义非ASCII字符
        indent: 缩进空格数
        create_dirs: 是否自动创建目录

    Returns:
        bool: 写入是否成功
    """
    try:
        path = Path(file_path)

        # 自动创建目录
        if create_dirs:
            ensure_directory_exists(path)

        with open(path, 'w', encoding=encoding) as f:
            json.dump(data, f, ensure_ascii=ensure_ascii, indent=indent)

        print(f"✓ JSON文件已保存: {file_path}")
        return True

    except Exception as e:
        print(f"✗ 写入JSON文件失败 ({file_path}): {e}")
        return False


def validate_json_file(file_path: Union[str, Path],
                       encoding: str = 'utf-8') -> tuple[bool, Optional[str]]:
    """
    验证JSON文件格式是否正确

    Args:
        file_path: JSON文件路径
        encoding: 文件编码

    Returns:
        tuple[bool, Optional[str]]: (是否有效, 错误信息)
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return False, f"文件不存在: {file_path}"

        with open(path, 'r', encoding=encoding) as f:
            json.load(f)
        return True, None

    except json.JSONDecodeError as e:
        return False, f"JSON格式错误: {e}"
    except Exception as e:
        return False, f"文件读取错误: {e}"


def merge_json_files(file_paths: List[Union[str, Path]],
                     output_path: Union[str, Path],
                     merge_strategy: str = 'merge_dicts') -> bool:
    """
    合并多个JSON文件

    Args:
        file_paths: 要合并的JSON文件路径列表
        output_path: 输出文件路径
        merge_strategy: 合并策略 ('merge_dicts', 'concat_lists', 'overwrite')

    Returns:
        bool: 合并是否成功
    """
    try:
        merged_data = None

        for file_path in file_paths:
            data = read_json_file(file_path, default={})

            if merged_data is None:
                merged_data = data
            else:
                if merge_strategy == 'merge_dicts':
                    if isinstance(merged_data, dict) and isinstance(data, dict):
                        merged_data.update(data)
                    else:
                        print(f"警告: 类型不匹配，跳过文件: {file_path}")
                elif merge_strategy == 'concat_lists':
                    if isinstance(merged_data, list) and isinstance(data, list):
                        merged_data.extend(data)
                    else:
                        print(f"警告: 类型不匹配，跳过文件: {file_path}")
                elif merge_strategy == 'overwrite':
                    merged_data = data

        if merged_data is not None:
            return write_json_file(output_path, merged_data)
        return False

    except Exception as e:
        print(f"✗ 合并JSON文件失败: {e}")
        return False


def extract_nested_value(data: Dict,
                         key_path: Union[str, List[str]],
                         default: Any = None) -> Any:
    """
    从嵌套字典中提取值

    Args:
        data: 源数据字典
        key_path: 键路径（可以用'.'分隔或列表形式）
        default: 默认值

    Returns:
        提取的值或默认值
    """
    try:
        if isinstance(key_path, str):
            keys = key_path.split('.')
        else:
            keys = key_path

        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current

    except Exception:
        return default


def flatten_json(data: Dict,
                 separator: str = '.',
                 parent_key: str = '') -> Dict:
    """
    将嵌套JSON展平为一层字典

    Args:
        data: 嵌套字典
        separator: 分隔符
        parent_key: 父级键名

    Returns:
        展平后的字典
    """
    items = []

    for key, value in data.items():
        new_key = f"{parent_key}{separator}{key}" if parent_key else key

        if isinstance(value, dict):
            items.extend(flatten_json(value, separator, new_key).items())
        else:
            items.append((new_key, value))

    return dict(items)


def ensure_directory_exists(file_path: Union[str, Path]) -> bool:
    """
    确保文件所在目录存在，如果不存在则创建

    Args:
        file_path: 文件路径

    Returns:
        bool: 目录创建是否成功
    """
    try:
        path = Path(file_path)
        directory = path.parent

        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"✓ 创建目录: {directory}")
            return True
        return True

    except Exception as e:
        print(f"✗ 创建目录失败: {e}")
        return False


def get_file_size(file_path: Union[str, Path]) -> Optional[int]:
    """
    获取文件大小（字节）

    Args:
        file_path: 文件路径

    Returns:
        Optional[int]: 文件大小，如果文件不存在返回None
    """
    try:
        path = Path(file_path)
        if path.exists():
            return path.stat().st_size
        return None
    except Exception:
        return None


def is_file_empty(file_path: Union[str, Path]) -> bool:
    """
    检查文件是否为空

    Args:
        file_path: 文件路径

    Returns:
        bool: 文件是否为空
    """
    size = get_file_size(file_path)
    return size is None or size == 0


def backup_file(file_path: Union[str, Path], backup_suffix: str = '.backup') -> Optional[str]:
    """
    创建文件备份

    Args:
        file_path: 原文件路径
        backup_suffix: 备份后缀

    Returns:
        Optional[str]: 备份文件路径，失败返回None
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return None

        backup_path = path.with_suffix(path.suffix + backup_suffix)
        import shutil
        shutil.copy2(path, backup_path)
        print(f"✓ 创建备份: {backup_path}")
        return str(backup_path)

    except Exception as e:
        print(f"✗ 创建备份失败: {e}")
        return None


def clear_directory(directory_path: Union[str, Path]) -> bool:
    """
    清空目录中的所有文件

    Args:
        directory_path: 目录路径

    Returns:
        bool: 清空是否成功
    """
    try:
        path = Path(directory_path)
        if not path.exists():
            return True

        for item in path.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                import shutil
                shutil.rmtree(item)

        print(f"✓ 清空目录: {directory_path}")
        return True

    except Exception as e:
        print(f"✗ 清空目录失败: {e}")
        return False


def get_files_in_directory(directory_path: Union[str, Path],
                           pattern: str = "*",
                           recursive: bool = False) -> list:
    """
    获取目录中的文件列表

    Args:
        directory_path: 目录路径
        pattern: 文件匹配模式
        recursive: 是否递归搜索

    Returns:
        list: 文件路径列表
    """
    try:
        path = Path(directory_path)
        if not path.exists():
            return []

        if recursive:
            files = list(path.rglob(pattern))
        else:
            files = list(path.glob(pattern))

        return [str(f) for f in files if f.is_file()]

    except Exception:
        return []


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小显示

    Args:
        size_bytes: 字节数

    Returns:
        str: 格式化的大小字符串
    """
    if size_bytes == 0:
        return "0B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"
