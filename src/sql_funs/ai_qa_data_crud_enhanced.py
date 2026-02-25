# -*- coding: utf-8 -*-
"""
增强的AI问答对数据管理CRUD操作模块

此模块提供了增强的AI问答对数据管理功能，包括：
1. HuggingFace数据集预览功能
2. 智能字段映射功能
3. 改进的导入流程
"""
from typing import Optional, List,  Dict, Any, Callable
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
import json
import logging
import os
import shutil

from src.sql_funs.sql_base import PostgreSQLManager
from src.sql_funs.ai_qa_data_group_crud import AIQADataGroupManager
from src.sql_funs.ai_qa_data_crud import ImportStats

logger = logging.getLogger(__name__)


@dataclass
class DatasetPreview:
    """数据集预览信息"""
    file_path: str
    total_records: int = 0
    preview_rows: List[Dict] = None
    columns: List[str] = None
    error: str = None
    
    def __post_init__(self):
        if self.preview_rows is None:
            self.preview_rows = []
        if self.columns is None:
            self.columns = []


@dataclass
class FieldMapping:
    """字段映射配置"""
    ai_qa_field: str  # ai_qa_data表字段
    hf_field: str     # HuggingFace数据集字段
    is_required: bool = False
    transform_func: Callable = None  # 字段转换函数


@dataclass
class ImportConfig:
    """导入配置"""
    file_path: str
    group_id: int
    mapping: Dict[str, str]  # ai_qa_field -> hf_field 映射
    options: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.options is None:
            self.options = {
                'batch_size': 1000,
                'skip_rows': 0,
                'unmapped_fields': 'ignore'  # ignore|metadata
            }


class EnhancedAIQADataManager(PostgreSQLManager):
    """
    增强的AI问答对数据管理器
    
    继承自PostgreSQLManager，提供增强的问答对数据管理功能，
    包括数据集预览、智能字段映射、改进的导入流程等。
    """
    
    TABLE_NAME = "ai_qa_data"
    
    # ai_qa_data表字段定义
    AI_QA_FIELDS = [
        {'name': 'id', 'type': 'VARCHAR', 'required': False, 'description': '主键，唯一标识'},
        {'name': 'question', 'type': 'TEXT', 'required': True, 'description': '问题内容'},
        {'name': 'answers', 'type': 'JSONB', 'required': True, 'description': '答案内容'},
        {'name': 'context', 'type': 'TEXT', 'required': False, 'description': '上下文信息'},
        {'name': 'question_type', 'type': 'VARCHAR', 'required': False, 'description': '问题类型'},
        {'name': 'source_dataset', 'type': 'VARCHAR', 'required': False, 'description': '数据来源'},
        {'name': 'hf_dataset_id', 'type': 'VARCHAR', 'required': False, 'description': 'HuggingFace原始ID'},
        {'name': 'language', 'type': 'VARCHAR', 'required': False, 'description': '语言'},
        {'name': 'difficulty_level', 'type': 'INTEGER', 'required': False, 'description': '难度等级'},
        {'name': 'category', 'type': 'VARCHAR', 'required': False, 'description': '分类标签'},
        {'name': 'sub_category', 'type': 'VARCHAR', 'required': False, 'description': '子分类'},
        {'name': 'tags', 'type': 'JSONB', 'required': False, 'description': '标签列表'},
        {'name': 'fixed_metadata', 'type': 'JSONB', 'required': False, 'description': '固定元数据'},
        {'name': 'dynamic_metadata', 'type': 'JSONB', 'required': False, 'description': '动态元数据'},
        {'name': 'question_length', 'type': 'INTEGER', 'required': False, 'description': '问题长度'},
        {'name': 'answer_length', 'type': 'INTEGER', 'required': False, 'description': '答案长度'},
        {'name': 'context_length', 'type': 'INTEGER', 'required': False, 'description': '上下文长度'},
        {'name': 'created_month', 'type': 'DATE', 'required': False, 'description': '创建月份（分区键）'}
    ]
    
    # 智能映射建议：常见HuggingFace字段到ai_qa_data字段的映射
    SMART_MAPPING_SUGGESTIONS = {
        'question': ['question', 'query', 'input', 'text', 'prompt'],
        'answers': ['answers', 'answer', 'response', 'output', 'target', 'label'],
        'context': ['context', 'passage', 'background', 'article', 'document'],
        'hf_dataset_id': ['id', 'idx', 'index', 'uuid'],
        'source_dataset': ['dataset', 'source', 'origin'],
        'language': ['language', 'lang'],
        'difficulty_level': ['difficulty', 'difficulty_level', 'level'],
        'category': ['category', 'class', 'type'],
        'tags': ['tags', 'labels', 'keywords']
    }
    
    def __init__(self):
        super().__init__()
        self.group_manager = AIQADataGroupManager()
    
    # ==================== 数据集预览功能 ====================
    
    def preview_huggingface_dataset(self, file_path: str, preview_rows: int = 5) -> DatasetPreview:
        """
        预览数据集（支持HuggingFace数据集目录、JSON文件、JSONL文件）
        
        Args:
            file_path: 数据集路径（可以是HuggingFace数据集目录、JSON文件或JSONL文件）
            preview_rows: 预览行数
            
        Returns:
            DatasetPreview: 数据集预览信息
        """
        preview = DatasetPreview(file_path=file_path)
        
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                preview.error = f"文件不存在: {file_path}"
                return preview
            
            # 判断文件类型并相应处理
            if os.path.isfile(file_path):
                # 单个文件（JSON或JSONL）
                return self._preview_json_file(file_path, preview_rows)
            elif os.path.isdir(file_path):
                # 目录：检查内容类型
                json_files = self._find_json_files_in_dir(file_path)
                if json_files:
                    # 目录中包含JSON文件，使用第一个JSON文件
                    logger.info(f"目录中发现JSON文件，使用第一个: {json_files[0]}")
                    return self._preview_json_file(json_files[0], preview_rows)
                else:
                    # 尝试作为HuggingFace数据集加载
                    return self._preview_hf_dataset(file_path, preview_rows)
            else:
                preview.error = f"无效的文件路径: {file_path}"
                return preview
            
        except Exception as e:
            preview.error = f"预览数据集失败: {str(e)}"
            logger.error(f"预览数据集失败: {e}")
            raise e
        
        return preview
    
    def _find_json_files_in_dir(self, dir_path: str) -> List[str]:
        """
        在目录中查找JSON/JSONL文件
        
        Args:
            dir_path: 目录路径
            
        Returns:
            List[str]: JSON/JSONL文件路径列表
        """
        json_files = []
        try:
            for item in os.listdir(dir_path):
                item_path = os.path.join(dir_path, item)
                if os.path.isfile(item_path):
                    ext = os.path.splitext(item)[1].lower()
                    if ext in ['.json', '.jsonl']:
                        json_files.append(item_path)
        except Exception as e:
            logger.warning(f"查找JSON文件失败: {e}")
        return json_files
    
    def _preview_json_file(self, file_path: str, preview_rows: int = 5) -> DatasetPreview:
        """
        预览JSON或JSONL文件
        
        Args:
            file_path: JSON或JSONL文件路径
            preview_rows: 预览行数
            
        Returns:
            DatasetPreview: 数据集预览信息
        """
        preview = DatasetPreview(file_path=file_path)
        
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.jsonl':
                # JSONL文件：每行一个JSON对象
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                preview.total_records = len(lines)
                
                for i, line in enumerate(lines[:preview_rows]):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        preview.preview_rows.append(record)
                    except json.JSONDecodeError as e:
                        logger.warning(f"解析JSONL第{i+1}行失败: {e}")
                        
            elif file_ext == '.json':
                # JSON文件：可能是对象列表或单个对象
                # 先尝试作为普通JSON解析
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if isinstance(data, list):
                        # JSON数组
                        preview.total_records = len(data)
                        preview.preview_rows = data[:preview_rows]
                    elif isinstance(data, dict):
                        # 单个JSON对象或包含数据键的对象
                        # 尝试查找常见的数据键
                        data_keys = ['data', 'items', 'rows', 'records', 'examples', 'qa_pairs', 'questions']
                        found_data = None
                        for key in data_keys:
                            if key in data and isinstance(data[key], list):
                                found_data = data[key]
                                break
                        
                        if found_data:
                            preview.total_records = len(found_data)
                            preview.preview_rows = found_data[:preview_rows]
                        else:
                            # 如果没有找到数据键，将整个对象作为单条记录
                            preview.total_records = 1
                            preview.preview_rows = [data]
                    else:
                        preview.error = f"不支持的JSON格式: {type(data)}"
                        return preview
                        
                except json.JSONDecodeError as e:
                    # 如果JSON解析失败，尝试作为JSONL格式读取
                    logger.info(f"JSON解析失败，尝试作为JSONL格式: {e}")
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    preview.total_records = len(lines)
                    
                    for i, line in enumerate(lines[:preview_rows]):
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            record = json.loads(line)
                            preview.preview_rows.append(record)
                        except json.JSONDecodeError as e:
                            logger.warning(f"解析JSONL第{i+1}行失败: {e}")
            else:
                # 尝试按JSONL格式读取
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    preview.total_records = len(lines)
                    
                    for i, line in enumerate(lines[:preview_rows]):
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            record = json.loads(line)
                            preview.preview_rows.append(record)
                        except json.JSONDecodeError as e:
                            logger.warning(f"解析第{i+1}行失败: {e}")
                except Exception as e:
                    preview.error = f"不支持的文件格式: {file_ext}"
                    return preview
            
            # 提取所有列名
            if preview.preview_rows:
                all_keys = set()
                for row in preview.preview_rows:
                    if isinstance(row, dict):
                        all_keys.update(row.keys())
                preview.columns = sorted(list(all_keys))
            
            logger.info(f"JSON文件预览成功: {file_path}, 总记录数: {preview.total_records}")
            
        except Exception as e:
            preview.error = f"预览JSON文件失败: {str(e)}"
            logger.error(f"预览JSON文件失败: {e}")
        
        return preview
    
    def _preview_hf_dataset(self, file_path: str, preview_rows: int = 5) -> DatasetPreview:
        """
        预览HuggingFace数据集目录
        
        Args:
            file_path: HuggingFace数据集目录路径
            preview_rows: 预览行数
            
        Returns:
            DatasetPreview: 数据集预览信息
        """
        preview = DatasetPreview(file_path=file_path)
        
        try:
            # 尝试加载数据集
            try:
                from datasets import load_from_disk
                
                # 尝试直接加载
                try:
                    dataset = load_from_disk(file_path)
                except Exception as e:
                    # 如果失败，尝试查找子目录中的数据集
                    logger.info(f"直接加载失败，尝试查找子目录: {e}")
                    dataset = self._find_and_load_dataset(file_path)
                    if dataset is None:
                        raise e
                    
            except ImportError:
                preview.error = "未安装datasets库，请运行: pip install datasets"
                return preview
            except Exception as e:
                preview.error = f"加载数据集失败: {str(e)}"
                return preview
            
            # 获取数据集信息
            preview.total_records = sum(len(dataset[split]) for split in dataset.keys())
            
            # 获取第一分割的前几行数据
            first_split = list(dataset.keys())[0] if dataset.keys() else None
            if first_split:
                split_data = dataset[first_split]
                
                # 获取预览数据
                for i in range(min(preview_rows, len(split_data))):
                    record = split_data[i]
                    
                    # 转换为字典格式
                    record_dict = self._hf_record_to_dict(record)
                    if record_dict:
                        record_dict = self._convert_hf_objects(record_dict)
                        preview.preview_rows.append(record_dict)
                
                # 提取所有列名
                if preview.preview_rows:
                    all_keys = set()
                    for row in preview.preview_rows:
                        all_keys.update(row.keys())
                    preview.columns = sorted(list(all_keys))
            
            logger.info(f"数据集预览成功: {file_path}, 总记录数: {preview.total_records}")
            
        except Exception as e:
            preview.error = f"预览数据集失败: {str(e)}"
            logger.error(f"预览数据集失败: {e}")
        
        return preview
    
    def _find_and_load_dataset(self, dir_path: str):
        """
        在目录中查找并加载HuggingFace数据集
        
        会递归查找子目录，找到第一个可以被load_from_disk加载的数据集
        
        Args:
            dir_path: 目录路径
            
        Returns:
            Dataset/DatasetDict 或 None
        """
        from datasets import load_from_disk
        
        # 首先检查当前目录下的子目录
        for item in os.listdir(dir_path):
            item_path = os.path.join(dir_path, item)
            if os.path.isdir(item_path):
                # 检查是否是数据集目录（包含dataset_info.json或dataset_dict.json）
                if self._is_dataset_dir(item_path):
                    try:
                        logger.info(f"尝试加载数据集: {item_path}")
                        dataset = load_from_disk(item_path)
                        logger.info(f"成功加载数据集: {item_path}")
                        return dataset
                    except Exception as e:
                        logger.warning(f"加载失败 {item_path}: {e}")
                        continue
        
        # 如果没有找到，递归检查子目录
        for item in os.listdir(dir_path):
            item_path = os.path.join(dir_path, item)
            if os.path.isdir(item_path):
                dataset = self._find_and_load_dataset(item_path)
                if dataset is not None:
                    return dataset
        
        return None
    
    def _is_dataset_dir(self, dir_path: str) -> bool:
        """
        检查目录是否是HuggingFace数据集目录
        
        Args:
            dir_path: 目录路径
            
        Returns:
            bool: 是否是数据集目录
        """
        # 检查是否有dataset_dict.json（DatasetDict）
        if os.path.exists(os.path.join(dir_path, "dataset_dict.json")):
            return True
        
        # 检查是否有dataset_info.json（Dataset）
        if os.path.exists(os.path.join(dir_path, "dataset_info.json")):
            return True
        
        # 检查是否有子目录包含dataset_info.json（多分割数据集）
        for item in os.listdir(dir_path):
            item_path = os.path.join(dir_path, item)
            if os.path.isdir(item_path):
                if os.path.exists(os.path.join(item_path, "dataset_info.json")):
                    return True
        
        return False
    
    def get_smart_mapping_suggestions(self, hf_columns: List[str]) -> Dict[str, str]:
        """
        获取智能字段映射建议
        
        Args:
            hf_columns: HuggingFace数据集的列名列表
            
        Returns:
            Dict[str, str]: ai_qa_field -> hf_field 映射建议
        """
        suggestions = {}
        
        # 为每个ai_qa_data字段寻找最佳匹配
        for ai_field in self.AI_QA_FIELDS:
            ai_field_name = ai_field['name']
            
            # 跳过自动生成的字段
            if ai_field_name in ['question_length', 'answer_length', 'context_length', 'created_month']:
                continue
            
            # 查找最佳匹配
            best_match = None
            best_score = 0
            
            for hf_column in hf_columns:
                score = self._calculate_field_match_score(ai_field_name, hf_column)
                if score > best_score:
                    best_score = score
                    best_match = hf_column
            
            # 如果找到匹配，添加到建议中
            if best_match and best_score > 0.3:  # 阈值
                suggestions[ai_field_name] = best_match
        
        return suggestions
    
    def _calculate_field_match_score(self, ai_field: str, hf_field: str) -> float:
        """
        计算字段匹配分数
        
        Args:
            ai_field: ai_qa_data表字段名
            hf_field: HuggingFace数据集字段名
            
        Returns:
            float: 匹配分数 (0-1)
        """
        # 转换为小写进行比较
        ai_lower = ai_field.lower()
        hf_lower = hf_field.lower()
        
        # 完全匹配
        if ai_lower == hf_lower:
            return 1.0
        
        # 包含关系
        if ai_lower in hf_lower or hf_lower in ai_lower:
            return 0.8
        
        # 智能映射建议
        if ai_field in self.SMART_MAPPING_SUGGESTIONS:
            if hf_lower in [s.lower() for s in self.SMART_MAPPING_SUGGESTIONS[ai_field]]:
                return 0.7
        
        # 相似度计算（简单的字符串相似度）
        # 这里可以使用更复杂的算法，如Levenshtein距离
        common_chars = set(ai_lower) & set(hf_lower)
        similarity = len(common_chars) / max(len(ai_lower), len(hf_lower))
        
        return similarity * 0.5
    
    # ==================== 增强的导入功能 ====================
    
    def import_with_mapping(self, config: ImportConfig, progress_callback: Callable = None) -> ImportStats:
        """
        使用字段映射导入数据（支持HuggingFace数据集、JSON、JSONL文件）
        
        Args:
            config: 导入配置
            progress_callback: 进度回调函数
            
        Returns:
            ImportStats: 导入统计信息
        """
        from src.sql_funs.ai_qa_data_crud import ImportStats
        
        stats = ImportStats()
        start_time = datetime.now()
        
        try:
            # 验证必要字段映射
            required_fields = ['question', 'answers']
            missing_fields = []
            for field in required_fields:
                if field not in config.mapping or not config.mapping[field]:
                    missing_fields.append(field)
            
            if missing_fields:
                stats.errors.append(f"缺少必要字段映射: {', '.join(missing_fields)}")
                return stats
            
            # 检查分组是否存在
            with AIQADataGroupManager() as group_manager:
                if not group_manager.group_exists(config.group_id):
                    stats.errors.append(f"分组不存在: ID={config.group_id}")
                    return stats
            
            # 获取数据集名称
            dataset_name = Path(config.file_path).name
            
            # 根据文件类型选择导入方式
            if os.path.isfile(config.file_path):
                # JSON/JSONL文件
                return self._import_json_file(config, dataset_name, progress_callback, stats, start_time)
            elif os.path.isdir(config.file_path):
                # 目录：检查内容类型
                json_files = self._find_json_files_in_dir(config.file_path)
                if json_files:
                    # 目录中包含JSON文件，使用第一个JSON文件
                    logger.info(f"目录中发现JSON文件，使用第一个: {json_files[0]}")
                    # 临时修改config的file_path
                    original_path = config.file_path
                    config.file_path = json_files[0]
                    result = self._import_json_file(config, dataset_name, progress_callback, stats, start_time)
                    config.file_path = original_path
                    return result
                else:
                    # 尝试作为HuggingFace数据集加载
                    return self._import_hf_dataset(config, dataset_name, progress_callback, stats, start_time)
            else:
                stats.errors.append(f"无效的文件路径: {config.file_path}")
                stats.duration = (datetime.now() - start_time).total_seconds()
                return stats
                
        except Exception as e:
            stats.errors.append(f"导入错误: {str(e)}")
        
        stats.duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"导入完成: 成功={stats.success}, 失败={stats.failed}, 跳过={stats.skipped}")
        
        return stats
    
    def _import_json_file(self, config: ImportConfig, dataset_name: str, 
                          progress_callback: Callable, stats: ImportStats, 
                          start_time: datetime) -> ImportStats:
        """
        导入JSON或JSONL文件
        """
        try:
            file_path = config.file_path
            batch_size = config.options.get('batch_size', 1000)
            skip_rows = config.options.get('skip_rows', 0)
            unmapped_fields = config.options.get('unmapped_fields', 'ignore')
            
            # 读取所有记录
            records = []
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.jsonl':
                # JSONL文件
                with open(file_path, 'r', encoding='utf-8') as f:
                    for i, line in enumerate(f):
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            record = json.loads(line)
                            records.append(record)
                        except json.JSONDecodeError as e:
                            logger.warning(f"解析JSONL第{i+1}行失败: {e}")
                            
            elif file_ext == '.json':
                # JSON文件：先尝试作为普通JSON解析
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if isinstance(data, list):
                        records = data
                    elif isinstance(data, dict):
                        # 尝试查找常见的数据键
                        data_keys = ['data', 'items', 'rows', 'records', 'examples', 'qa_pairs', 'questions']
                        for key in data_keys:
                            if key in data and isinstance(data[key], list):
                                records = data[key]
                                break
                        if not records:
                            records = [data]
                    else:
                        stats.errors.append(f"不支持的JSON格式: {type(data)}")
                        stats.duration = (datetime.now() - start_time).total_seconds()
                        return stats
                        
                except json.JSONDecodeError as e:
                    # 如果JSON解析失败，尝试作为JSONL格式读取
                    logger.info(f"JSON解析失败，尝试作为JSONL格式: {e}")
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for i, line in enumerate(f):
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                record = json.loads(line)
                                records.append(record)
                            except json.JSONDecodeError as e:
                                logger.warning(f"解析JSONL第{i+1}行失败: {e}")
            else:
                # 尝试按JSONL格式读取
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for i, line in enumerate(f):
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                record = json.loads(line)
                                records.append(record)
                            except json.JSONDecodeError as e:
                                logger.warning(f"解析第{i+1}行失败: {e}")
                except Exception as e:
                    stats.errors.append(f"不支持的文件格式: {file_ext}")
                    stats.duration = (datetime.now() - start_time).total_seconds()
                    return stats
            
            # 应用跳过行数
            if skip_rows > 0:
                records = records[skip_rows:]
            
            stats.total = len(records)
            
            # 批量导入
            for i, record in enumerate(records):
                try:
                    # 转换数据格式
                    qa_data = self._convert_with_mapping(
                        record, config.group_id, dataset_name, config.mapping, unmapped_fields
                    )
                    
                    if qa_data:
                        # 使用现有的create_qa_data方法
                        from src.sql_funs.ai_qa_data_crud import AIQADataManager
                        with AIQADataManager() as manager:
                            qa_id = manager.create_qa_data(**qa_data)
                            if qa_id:
                                stats.success += 1
                            else:
                                stats.failed += 1
                    else:
                        stats.skipped += 1
                        
                except Exception as e:
                    stats.failed += 1
                    stats.errors.append(f"记录导入错误: {str(e)[:100]}")
                
                # 进度回调
                if progress_callback and (i + 1) % 100 == 0:
                    progress_callback(i + 1, stats.total)
                
                if (i + 1) % 1000 == 0:
                    logger.info(f"导入进度: {i + 1}/{stats.total}")
            
            # 更新分组统计
            self._update_group_qa_count(config.group_id)
            
        except Exception as e:
            stats.errors.append(f"导入JSON文件失败: {str(e)}")
        
        stats.duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"导入完成: 成功={stats.success}, 失败={stats.failed}, 跳过={stats.skipped}")
        
        return stats
    
    def _import_hf_dataset(self, config: ImportConfig, dataset_name: str,
                           progress_callback: Callable, stats: ImportStats,
                           start_time: datetime) -> ImportStats:
        """
        导入HuggingFace数据集
        """
        try:
            # 加载数据集
            from datasets import load_from_disk
            
            try:
                dataset = load_from_disk(config.file_path)
            except Exception as e:
                # 如果直接加载失败，尝试查找子目录
                logger.info(f"直接加载失败，尝试查找子目录: {e}")
                dataset = self._find_and_load_dataset(config.file_path)
                if dataset is None:
                    raise e
            
            batch_size = config.options.get('batch_size', 1000)
            skip_rows = config.options.get('skip_rows', 0)
            unmapped_fields = config.options.get('unmapped_fields', 'ignore')
            
            # 处理所有分割
            total_records = 0
            for split_name in dataset.keys():
                split_data = dataset[split_name]
                total_records += len(split_data)
            
            stats.total = total_records
            
            # 导入数据
            imported_count = 0
            
            for split_name in dataset.keys():
                split_data = dataset[split_name]
                split_len = len(split_data)
                
                # 处理跳过行数
                current_skip = skip_rows
                skip_rows = 0  # 重置，只在第一个split使用
                
                for i in range(0, split_len, batch_size):
                    end_idx = min(i + batch_size, split_len)
                    
                    # 使用select获取记录
                    batch_indices = list(range(i, end_idx))
                    if current_skip > 0:
                        skip_in_batch = min(current_skip, len(batch_indices))
                        batch_indices = batch_indices[skip_in_batch:]
                        current_skip -= skip_in_batch
                    
                    if not batch_indices:
                        continue
                    
                    batch_dataset = split_data.select(batch_indices)
                    
                    for record in batch_dataset:
                        try:
                            # 转换数据格式
                            qa_data = self._convert_with_mapping(
                                record, config.group_id, dataset_name, config.mapping, unmapped_fields
                            )
                            
                            if qa_data:
                                # 使用现有的create_qa_data方法
                                from src.sql_funs.ai_qa_data_crud import AIQADataManager
                                with AIQADataManager() as manager:
                                    qa_id = manager.create_qa_data(**qa_data)
                                    if qa_id:
                                        stats.success += 1
                                    else:
                                        stats.failed += 1
                            else:
                                stats.skipped += 1
                                
                        except Exception as e:
                            stats.failed += 1
                            stats.errors.append(f"记录导入错误: {str(e)[:100]}")
                    
                    imported_count += len(batch_indices)
                    
                    # 进度回调
                    if progress_callback:
                        progress_callback(imported_count, total_records)
                    
                    logger.info(f"导入进度: {imported_count}/{total_records}")
            
            # 更新分组统计
            self._update_group_qa_count(config.group_id)
            
        except Exception as e:
            stats.errors.append(f"导入数据集失败: {str(e)}")
        
            stats.duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"导入完成: 成功={stats.success}, 失败={stats.failed}, 跳过={stats.skipped}")
            # 更新分组统计
            self._update_group_qa_count(config.group_id)
            return stats
        except ImportError:
            stats.errors.append("未安装datasets库，请运行: pip install datasets")
        except Exception as e:
            stats.errors.append(f"导入错误: {str(e)}")
        
        stats.duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"导入完成: 成功={stats.success}, 失败={stats.failed}, 跳过={stats.skipped}")
        
        return stats
    
    def _convert_with_mapping(self, record, group_id: int, dataset_name: str, 
                              mapping: Dict[str, str], unmapped_fields: str = 'ignore') -> Optional[Dict]:
        """
        使用字段映射转换记录
        
        Args:
            record: 原始记录（可能是HuggingFace数据集的特殊对象）
            group_id: 分组ID
            dataset_name: 数据集名称
            mapping: 字段映射配置
            unmapped_fields: 未映射字段处理方式
            
        Returns:
            Optional[Dict]: 转换后的数据
        """
        try:
            # 将HuggingFace数据集记录转换为字典
            record_dict = self._hf_record_to_dict(record)
            
            if not record_dict:
                logger.warning(f"无法将记录转换为字典: {type(record)}")
                return None
            
            # 将HuggingFace数据集的特殊对象转换为普通Python对象
            record_dict = self._convert_hf_objects(record_dict)
            
            # 构建转换后的数据
            qa_data = {
                'group_id': group_id,
                'source_dataset': dataset_name,
                'fixed_metadata': {
                    'original_format': 'huggingface',
                    'imported_at': datetime.now().isoformat(),
                    'field_mapping': mapping
                },
                'dynamic_metadata': {}
            }
            
            # 应用字段映射
            for ai_field, hf_field in mapping.items():
                # 跳过特殊值
                if not hf_field or hf_field == '不导入' or hf_field == '自动生成':
                    continue
                
                # 检查字段是否存在于记录中
                if hf_field in record_dict:
                    value = record_dict[hf_field]
                    
                    # 特殊字段处理
                    if ai_field == 'answers':
                        value = self._process_answers(value)
                    elif ai_field == 'tags' and isinstance(value, str):
                        value = [value]
                    elif ai_field == 'question_type' and (not value or value == '自动生成'):
                        # 自动生成问题类型
                        value = self._auto_detect_question_type(record_dict.get('question', ''))
                    elif ai_field in ['fixed_metadata', 'dynamic_metadata'] and isinstance(value, str):
                        try:
                            value = json.loads(value)
                        except:
                            value = {'raw': value}
                    
                    qa_data[ai_field] = value
            
            # 处理未映射的字段
            if unmapped_fields == 'metadata':
                unmapped_data = {}
                for hf_field, value in record_dict.items():
                    # 跳过已映射的字段
                    if hf_field in mapping.values():
                        continue
                    
                    # 添加到动态元数据
                    unmapped_data[hf_field] = value
                
                if unmapped_data:
                    qa_data['dynamic_metadata'].update(unmapped_data)
            
            # 验证必要字段
            if 'question' not in qa_data or not qa_data['question']:
                logger.debug(f"记录缺少question字段，可用字段: {list(record_dict.keys())[:10]}")
                return None
            
            if 'answers' not in qa_data:
                logger.debug(f"记录缺少answers字段")
                return None
            
            return qa_data
            
        except Exception as e:
            logger.warning(f"转换记录失败: {e}", exc_info=True)
            return None
    
    def _hf_record_to_dict(self, record) -> Optional[Dict]:
        """
        将HuggingFace数据集记录转换为字典
        
        HuggingFace数据集返回的记录可能是多种类型：
        - dict: 已经是字典
        - BatchEncoding: transformers的编码结果
        - 其他可迭代对象
        
        Args:
            record: HuggingFace数据集记录
            
        Returns:
            Optional[Dict]: 字典形式的记录
        """
        try:
            # 如果已经是字典，直接返回
            if isinstance(record, dict):
                return record
            
            # 尝试使用 keys() 和 __getitem__ 方法（适用于 BatchEncoding 等）
            if hasattr(record, 'keys') and callable(getattr(record, 'keys')):
                try:
                    result = {}
                    for key in record.keys():
                        result[key] = record[key]
                    return result
                except Exception as e:
                    logger.debug(f"使用 keys() 方法转换失败: {e}")
            
            # 尝试使用 __dict__ 属性
            if hasattr(record, '__dict__'):
                try:
                    return record.__dict__
                except Exception as e:
                    logger.debug(f"使用 __dict__ 转换失败: {e}")
            
            # 尝试迭代转换
            try:
                result = {}
                for key in record:
                    result[key] = record[key]
                return result
            except Exception as e:
                logger.debug(f"使用迭代转换失败: {e}")
            
            # 最后尝试 dict() 构造函数
            try:
                return dict(record)
            except Exception as e:
                logger.debug(f"使用 dict() 转换失败: {e}")
            
            # 所有方法都失败
            logger.warning(f"无法将记录转换为字典，类型: {type(record)}")
            return None
            
        except Exception as e:
            logger.warning(f"转换记录为字典时出错: {e}")
            return None
    
    def _convert_hf_objects(self, obj):
        """
        递归将HuggingFace数据集对象转换为普通Python对象
        
        Args:
            obj: 任意对象
            
        Returns:
            转换后的对象
        """
        if isinstance(obj, dict):
            return {k: self._convert_hf_objects(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_hf_objects(item) for item in obj]
        elif hasattr(obj, 'tolist'):  # numpy数组等
            return obj.tolist()
        elif hasattr(obj, 'item'):  # numpy标量
            return obj.item()
        else:
            return obj
    
    def _process_answers(self, answers):
        """处理answers字段"""
        if isinstance(answers, str):
            return {'text': [answers], 'answer_start': []}
        elif isinstance(answers, list):
            return {'text': answers, 'answer_start': []}
        elif isinstance(answers, dict):
            return answers
        else:
            return {'text': [str(answers)], 'answer_start': []}
    
    def _auto_detect_question_type(self, question: str) -> str:
        """
        自动检测问题类型
        
        Args:
            question: 问题文本
            
        Returns:
            str: 问题类型
        """
        question_lower = question.lower()
        
        # 检测特定关键词
        if any(word in question_lower for word in ['what', '什么', '是什么', '为什么', 'why']):
            return 'factual'
        elif any(word in question_lower for word in ['how', '如何', '怎么', '怎样']):
            return 'reasoning'
        elif any(word in question_lower for word in ['which', '哪个', '哪些']):
            return 'contextual'
        elif any(word in question_lower for word in ['explain', '解释', '说明']):
            return 'conceptual'
        else:
            return 'factual'
    
    def _update_group_qa_count(self, group_id: int):
        """更新分组的问答对数量"""
        try:
            if not self.connection or self.connection.closed:
                self.connect()
            
            # 计算分组中的问答对数量
            query = f"SELECT COUNT(*) FROM {self.TABLE_NAME} WHERE group_id = %s"
            result = self.execute_query(query, (group_id,))
            count = result[0][0] if result else 0
            
            # 更新分组
            if not self.group_manager.connection or self.group_manager.connection.closed:
                self.group_manager.connect()
            
            self.group_manager.update_group(group_id, qa_count=count)
            
        except Exception as e:
            logger.warning(f"更新分组统计失败: {e}")
    
    # ==================== 文件上传功能 ====================
    
    def save_uploaded_file(self, uploaded_file, temp_dir: str = None) -> str:
        """
        保存上传的文件
        
        Args:
            uploaded_file: 上传的文件对象
            temp_dir: 临时目录路径
            
        Returns:
            str: 保存的文件路径
        """
        try:
            if temp_dir is None:
                # 使用项目内的临时目录，避免权限问题
                project_root = Path(__file__).parent.parent.parent
                temp_base = project_root / "temp_uploads"
                temp_base.mkdir(exist_ok=True)
                
                # 创建带时间戳的子目录
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                temp_dir = str(temp_base / f"hf_upload_{timestamp}")
            
            # 确保目录存在
            os.makedirs(temp_dir, exist_ok=True)
            
            # 处理文件名：提取基本文件名，去掉路径部分
            original_filename = uploaded_file.filename
            
            # 如果文件名包含路径分隔符，只取最后一部分
            if '/' in original_filename:
                original_filename = original_filename.split('/')[-1]
            elif '\\' in original_filename:
                original_filename = original_filename.split('\\')[-1]
            
            # 生成安全文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_filename = f"{timestamp}_{original_filename.replace(' ', '_').replace('/', '_').replace('\\', '_')}"
            file_path = os.path.join(temp_dir, safe_filename)
            
            # 确保父目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 保存文件
            uploaded_file.save(file_path)
            
            logger.info(f"文件保存成功: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"保存上传文件失败: {e}")
            raise
    
    def cleanup_temp_files(self, file_path: str):
        """
        清理临时文件
        
        Args:
            file_path: 文件路径
        """
        try:
            if os.path.exists(file_path):
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                else:
                    os.remove(file_path)
                logger.info(f"清理临时文件: {file_path}")
        except Exception as e:
            logger.warning(f"清理临时文件失败: {e}")
