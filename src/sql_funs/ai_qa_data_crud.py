# -*- coding: utf-8 -*-
"""
AI问答对数据管理CRUD操作模块

此模块提供了AI问答对数据的完整CRUD操作接口，
包括数据的增删改查、批量导入、HuggingFace数据集导入等功能。
"""
from typing import Optional, List, Tuple, Dict, Any, Callable, Union
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
import json
import logging
import io

from src.sql_funs.sql_base import PostgreSQLManager
from src.sql_funs.ai_qa_data_group_crud import AIQADataGroupManager

logger = logging.getLogger(__name__)


@dataclass
class ImportStats:
    """导入统计信息"""
    total: int = 0
    success: int = 0
    failed: int = 0
    skipped: int = 0
    errors: List[str] = None
    duration: float = 0.0
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class AIQADataManager(PostgreSQLManager):
    """
    AI问答对数据管理器
    
    继承自PostgreSQLManager，提供针对ai_qa_data表的完整CRUD操作，
    包括数据的创建、更新、删除、查询，以及HuggingFace数据导入等功能。
    """
    
    TABLE_NAME = "ai_qa_data"
    
    def __init__(self):
        super().__init__()
        self.group_manager = AIQADataGroupManager()
    
    # ==================== 创建操作 ====================
    
    def create_qa_data(self, group_id: int, question: str, answers: Union[str, List[str], Dict],
                       context: str = None, question_type: str = None,
                       source_dataset: str = None, hf_dataset_id: str = None,
                       language: str = 'zh', difficulty_level: int = None,
                       category: str = None, sub_category: str = None,
                       tags: List[str] = None, fixed_metadata: Dict = None,
                       dynamic_metadata: Dict = None, **kwargs) -> Optional[int]:
        """
        创建新的问答对数据
        
        Args:
            group_id: 所属分组ID（必填）
            question: 问题文本（必填）
            answers: 答案，支持字符串、字符串列表或字典格式
            context: 上下文/背景信息
            question_type: 问题类型
            source_dataset: 源数据集名称
            hf_dataset_id: HuggingFace原始ID
            language: 语言
            difficulty_level: 难度等级（1-10）
            category: 分类标签
            sub_category: 子分类
            tags: 标签列表
            fixed_metadata: 固定元数据
            dynamic_metadata: 动态元数据
            **kwargs: 其他字段
            
        Returns:
            Optional[int]: 新创建记录的ID，失败返回None
        """
        try:
            # 处理answers字段，统一存储为JSONB
            processed_answers = self._process_answers(answers)
            
            # 计算文本长度
            question_length = len(question) if question else 0
            answer_length = self._calculate_answer_length(processed_answers)
            context_length = len(context) if context else 0
            
            data = {
                "group_id": group_id,
                "question": question,
                "answers": processed_answers,
                "context": context,
                "question_type": question_type,
                "source_dataset": source_dataset,
                "hf_dataset_id": hf_dataset_id,
                "language": language,
                "difficulty_level": difficulty_level,
                "category": category,
                "sub_category": sub_category,
                "tags": tags or [],
                "fixed_metadata": fixed_metadata or {},
                "dynamic_metadata": dynamic_metadata or {},
                "question_length": question_length,
                "answer_length": answer_length,
                "context_length": context_length,
                "created_month": datetime.now().strftime('%Y-%m-%d'),  # 分区键
                **kwargs
            }
            
            # 移除None值
            data = {k: v for k, v in data.items() if v is not None}
            
            # 使用PostgreSQLManager的insert方法
            success = self.insert(self.TABLE_NAME, data)
            
            if success:
                # 获取刚创建的记录ID
                query = f"""
                SELECT id FROM {self.TABLE_NAME} 
                WHERE group_id = %s AND question = %s 
                AND created_at > NOW() - INTERVAL '5 seconds'
                ORDER BY created_at DESC LIMIT 1
                """
                result = self.execute_query(query, (group_id, question))
                if result:
                    qa_id = result[0][0]
                    logger.info(f"问答对创建成功: ID={qa_id}")
                    
                    # 更新分组的问答对数量
                    self._update_group_qa_count(group_id)
                    
                    return qa_id
            
            return None
            
        except Exception as e:
            logger.error(f"创建问答对失败: {e}")
            return None
    
    def batch_create_qa_data(self, qa_data_list: List[Dict[str, Any]], 
                             batch_size: int = 1000,
                             progress_callback: Callable[[int, int], None] = None) -> ImportStats:
        """
        批量创建问答对数据
        
        Args:
            qa_data_list: 问答对数据列表
            batch_size: 批次大小
            progress_callback: 进度回调函数，参数为(当前数量, 总数)
            
        Returns:
            ImportStats: 导入统计信息
        """
        stats = ImportStats(total=len(qa_data_list))
        start_time = datetime.now()
        
        try:
            for i in range(0, len(qa_data_list), batch_size):
                batch = qa_data_list[i:i+batch_size]
                
                for data in batch:
                    try:
                        qa_id = self.create_qa_data(**data)
                        if qa_id:
                            stats.success += 1
                        else:
                            stats.failed += 1
                            stats.errors.append(f"Failed to create QA data: {data.get('question', 'unknown')[:50]}")
                    except Exception as e:
                        stats.failed += 1
                        stats.errors.append(str(e))
                
                # 进度回调
                if progress_callback:
                    progress_callback(min(i + batch_size, stats.total), stats.total)
                
                logger.info(f"批量导入进度: {min(i + batch_size, stats.total)}/{stats.total}")
            
            # 更新各分组的问答对数量
            group_ids = set(d.get('group_id') for d in qa_data_list if d.get('group_id'))
            for group_id in group_ids:
                self._update_group_qa_count(group_id)
            
        except Exception as e:
            logger.error(f"批量创建问答对失败: {e}")
            stats.errors.append(str(e))
        
        stats.duration = (datetime.now() - start_time).total_seconds()
        return stats
    
    def bulk_insert_qa_data(self, qa_data_list: List[Dict[str, Any]]) -> int:
        """
        使用COPY命令进行高效批量插入
        
        Args:
            qa_data_list: 问答对数据列表
            
        Returns:
            int: 成功插入的记录数
        """
        if not qa_data_list:
            return 0
        
        try:
            # 准备数据
            buffer = io.StringIO()
            
            for data in qa_data_list:
                # 处理数据格式
                processed = self._prepare_copy_data(data)
                line = '\t'.join(str(v) for v in processed) + '\n'
                buffer.write(line)
            
            buffer.seek(0)
            
            # 使用COPY命令
            self.cursor.copy_from(
                buffer,
                self.TABLE_NAME,
                columns=['group_id', 'question', 'answers', 'context', 'question_type',
                        'source_dataset', 'hf_dataset_id', 'language', 'difficulty_level',
                        'category', 'sub_category', 'tags', 'fixed_metadata', 'dynamic_metadata',
                        'question_length', 'answer_length', 'context_length', 'created_month']
            )
            self.connection.commit()
            
            inserted_count = len(qa_data_list)
            logger.info(f"批量插入成功: {inserted_count} 条记录")
            
            # 更新分组数量
            group_ids = set(d.get('group_id') for d in qa_data_list if d.get('group_id'))
            for group_id in group_ids:
                self._update_group_qa_count(group_id)
            
            return inserted_count
            
        except Exception as e:
            self.connection.rollback()
            logger.error(f"批量插入失败: {e}")
            return 0
    
    # ==================== HuggingFace数据集导入 ====================
    
    def import_from_huggingface(self, dataset_path: str, group_id: int = None,
                                group_name: str = None,
                                batch_size: int = 1000,
                                transform_func: Callable[[Dict], Dict] = None,
                                progress_callback: Callable[[int, int], None] = None) -> ImportStats:
        """
        从HuggingFace数据集导入问答对数据
        
        Args:
            dataset_path: HuggingFace数据集路径或本地路径
            group_id: 目标分组ID（与group_name二选一）
            group_name: 目标分组名称（如果不存在则创建）
            batch_size: 批次大小
            transform_func: 数据转换函数，接收原始数据字典，返回处理后的字典
            progress_callback: 进度回调函数
            
        Returns:
            ImportStats: 导入统计信息
        """
        stats = ImportStats()
        start_time = datetime.now()
        
        try:
            # 检查或创建分组
            if group_id is None:
                if group_name:
                    # 尝试查找现有分组
                    groups = self.group_manager.list_groups(name=group_name)
                    if groups:
                        group_id = groups[0]['id']
                        logger.info(f"使用现有分组: {group_name} (ID={group_id})")
                    else:
                        # 创建新分组
                        group_id = self.group_manager.create_group(
                            name=group_name,
                            purpose=f"Imported from {dataset_path}",
                            test_type='comprehensive'
                        )
                        if group_id:
                            logger.info(f"创建新分组: {group_name} (ID={group_id})")
                        else:
                            stats.errors.append(f"无法创建分组: {group_name}")
                            return stats
                else:
                    stats.errors.append("必须提供 group_id 或 group_name")
                    return stats
            
            # 加载数据集
            from datasets import load_from_disk
            dataset = load_from_disk(dataset_path)
            
            # 获取数据集名称
            dataset_name = Path(dataset_path).name
            
            # 处理所有分割
            total_records = 0
            for split_name in dataset.keys():
                split_data = dataset[split_name]
                total_records += len(split_data)
            
            stats.total = total_records
            logger.info(f"数据集加载成功: {total_records} 条记录")
            
            # 导入数据
            imported_count = 0
            for split_name in dataset.keys():
                split_data = dataset[split_name]
                
                for i in range(0, len(split_data), batch_size):
                    batch = split_data[i:i+batch_size]
                    
                    for record in batch:
                        try:
                            # 转换数据格式
                            qa_data = self._convert_hf_record(
                                record, group_id, dataset_name, transform_func
                            )
                            
                            if qa_data:
                                qa_id = self.create_qa_data(**qa_data)
                                if qa_id:
                                    stats.success += 1
                                else:
                                    stats.failed += 1
                            else:
                                stats.skipped += 1
                                
                        except Exception as e:
                            stats.failed += 1
                            stats.errors.append(f"Record import error: {str(e)[:100]}")
                    
                    imported_count += len(batch)
                    
                    # 进度回调
                    if progress_callback:
                        progress_callback(imported_count, total_records)
                    
                    logger.info(f"导入进度: {imported_count}/{total_records}")
            
            # 更新分组统计
            self._update_group_qa_count(group_id)
            self.group_manager.update_group(
                group_id, 
                source_count=len(dataset.keys())
            )
            
        except ImportError:
            stats.errors.append("未安装datasets库，请运行: pip install datasets")
        except Exception as e:
            stats.errors.append(f"Import error: {str(e)}")
        
        stats.duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"导入完成: 成功={stats.success}, 失败={stats.failed}, 跳过={stats.skipped}")
        
        return stats
    
    def _convert_hf_record(self, record: Dict, group_id: int, dataset_name: str,
                           transform_func: Callable = None) -> Optional[Dict]:
        """
        将HuggingFace记录转换为数据库格式
        
        Args:
            record: HuggingFace数据集记录
            group_id: 分组ID
            dataset_name: 数据集名称
            transform_func: 自定义转换函数
            
        Returns:
            Optional[Dict]: 转换后的数据字典，转换失败返回None
        """
        try:
            # 应用自定义转换
            if transform_func:
                record = transform_func(record)
                if record is None:
                    return None
            
            # 提取问题
            question = record.get('question') or record.get('query') or record.get('input')
            if not question:
                return None
            
            # 提取答案（支持多种格式）
            answers = record.get('answers')
            if answers is None:
                answers = record.get('answer') or record.get('output') or record.get('target')
            
            # 提取上下文
            context = record.get('context') or record.get('passage') or record.get('background')
            
            # 构建数据字典
            qa_data = {
                'group_id': group_id,
                'question': question,
                'answers': answers,
                'context': context,
                'source_dataset': dataset_name,
                'hf_dataset_id': str(record.get('id', '')),
                'language': record.get('language', 'zh'),
                'difficulty_level': record.get('difficulty_level'),
                'category': record.get('category'),
                'sub_category': record.get('sub_category'),
                'tags': record.get('tags', []),
                'fixed_metadata': {
                    'original_format': 'huggingface',
                    'imported_at': datetime.now().isoformat()
                },
                'dynamic_metadata': {k: v for k, v in record.items() 
                                    if k not in ['question', 'answers', 'answer', 'context', 
                                                'query', 'input', 'output', 'target', 'id']}
            }
            
            return qa_data
            
        except Exception as e:
            logger.warning(f"转换记录失败: {e}")
            return None
    
    # ==================== 读取操作 ====================
    
    def get_qa_data_by_id(self, qa_id: int, created_month: str = None) -> Optional[Dict[str, Any]]:
        """
        根据ID获取问答对数据
        
        Args:
            qa_id: 问答对ID
            created_month: 创建月份（分区键，提高查询效率）
            
        Returns:
            Optional[Dict]: 问答对数据字典
        """
        if created_month:
            query = f"SELECT * FROM {self.TABLE_NAME} WHERE id = %s AND created_month = %s"
            result = self.execute_query(query, (qa_id, created_month))
        else:
            query = f"SELECT * FROM {self.TABLE_NAME} WHERE id = %s"
            result = self.execute_query(query, (qa_id,))
        
        if result:
            return self._row_to_dict(result[0])
        return None
    
    def get_qa_data_by_uuid(self, qa_uuid: str) -> Optional[Dict[str, Any]]:
        """
        根据UUID获取问答对数据
        
        Args:
            qa_uuid: 问答对UUID
            
        Returns:
            Optional[Dict]: 问答对数据字典
        """
        query = f"SELECT * FROM {self.TABLE_NAME} WHERE qa_uuid = %s"
        result = self.execute_query(query, (qa_uuid,))
        
        if result:
            return self._row_to_dict(result[0])
        return None
    
    def list_qa_data(self, group_id: int = None, question_type: str = None,
                     difficulty_level: int = None, category: str = None,
                     language: str = None, tags: List[str] = None,
                     question_keyword: str = None, context_keyword: str = None,
                     order_by: str = 'created_at DESC', limit: int = None,
                     offset: int = None) -> List[Dict[str, Any]]:
        """
        获取问答对列表（支持多种筛选条件）
        
        Args:
            group_id: 按分组筛选
            question_type: 按问题类型筛选
            difficulty_level: 按难度等级筛选
            category: 按分类筛选
            language: 按语言筛选
            tags: 按标签筛选（包含任一标签）
            question_keyword: 问题关键词（全文搜索）
            context_keyword: 上下文关键词（全文搜索）
            order_by: 排序字段
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            List[Dict]: 问答对数据字典列表
        """
        conditions = []
        params = []
        
        if group_id:
            conditions.append("group_id = %s")
            params.append(group_id)
        
        if question_type:
            conditions.append("question_type = %s")
            params.append(question_type)
        
        if difficulty_level:
            conditions.append("difficulty_level = %s")
            params.append(difficulty_level)
        
        if category:
            conditions.append("category = %s")
            params.append(category)
        
        if language:
            conditions.append("language = %s")
            params.append(language)
        
        if tags:
            # 使用JSONB包含查询
            conditions.append("tags @> %s")
            params.append(json.dumps(tags))
        
        if question_keyword:
            conditions.append("question ILIKE %s")
            params.append(f"%{question_keyword}%")
        
        if context_keyword:
            conditions.append("context ILIKE %s")
            params.append(f"%{context_keyword}%")
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        query = f"SELECT * FROM {self.TABLE_NAME} {where_clause}"
        
        if order_by:
            query += f" ORDER BY {order_by}"
        
        if limit:
            query += f" LIMIT {limit}"
        
        if offset:
            query += f" OFFSET {offset}"
        
        result = self.execute_query(query, tuple(params) if params else None)
        
        if result:
            return [self._row_to_dict(row) for row in result]
        return []
    
    def search_similar_questions(self, question: str, group_id: int = None,
                                  limit: int = 10) -> List[Dict[str, Any]]:
        """
        搜索相似问题（使用全文搜索）
        
        Args:
            question: 搜索关键词
            group_id: 限制在特定分组内搜索
            limit: 返回结果数量
            
        Returns:
            List[Dict]: 相似问题列表
        """
        conditions = []
        params = []
        
        if group_id:
            conditions.append("group_id = %s")
            params.append(group_id)
        
        # 使用相似度搜索
        conditions.append("question %% %s")  # pg_trgm的相似度操作符
        params.append(question)
        
        where_clause = "WHERE " + " AND ".join(conditions)
        
        query = f"""
        SELECT *, similarity(question, %s) as sim_score
        FROM {self.TABLE_NAME}
        {where_clause}
        ORDER BY sim_score DESC, question <-> %s
        LIMIT %s
        """
        params.extend([question, question, limit])
        
        result = self.execute_query(query, tuple(params))
        
        if result:
            return [self._row_to_dict(row[:-1], similarity=row[-1]) for row in result]
        return []
    
    def count_qa_data(self, **filters) -> int:
        """
        统计问答对数量
        
        Args:
            **filters: 筛选条件
            
        Returns:
            int: 问答对数量
        """
        # 使用gen_select_query方法生成COUNT查询
        exact_match_fields = {'group_id', 'question_type', 'category', 'language', 'difficulty_level'}
        partial_match_fields = {'question', 'context'}
        allowed_fields = exact_match_fields | partial_match_fields
        
        # 构建COUNT查询
        base_query = f"SELECT COUNT(*) FROM {self.TABLE_NAME}"
        
        if filters:
            # 移除None值的过滤条件
            clean_filters = {k: v for k, v in filters.items() if v is not None}
            if clean_filters:
                where_query, params = self.gen_select_query(
                    self.TABLE_NAME,
                    exact_match_fields=list(exact_match_fields),
                    partial_match_fields=list(partial_match_fields),
                    allowed_fileds=list(allowed_fields),
                    **clean_filters
                )
                # 提取WHERE子句部分
                where_clause = where_query.split('WHERE ', 1)[1] if 'WHERE ' in where_query else ''
                query = f"{base_query} WHERE {where_clause}"
                result = self.execute_query(query, params)
            else:
                result = self.execute_query(base_query)
        else:
            result = self.execute_query(base_query)
        
        return result[0][0] if result else 0
    
    # ==================== 更新操作 ====================
    
    def update_qa_data(self, qa_id: int, **kwargs) -> bool:
        """
        更新问答对数据
        
        Args:
            qa_id: 问答对ID
            **kwargs: 要更新的字段
            
        Returns:
            bool: 更新成功返回True
        """
        # 不允许更新的字段
        forbidden_fields = {'id', 'qa_uuid', 'group_id', 'created_at', 'created_month'}
        
        data = {k: v for k, v in kwargs.items() if k not in forbidden_fields and v is not None}
        
        # 特殊处理answers字段
        if 'answers' in data:
            data['answers'] = self._process_answers(data['answers'])
            data['answer_length'] = self._calculate_answer_length(data['answers'])
        
        # 更新文本长度
        if 'question' in data:
            data['question_length'] = len(data['question'])
        if 'context' in data:
            data['context_length'] = len(data['context']) if data['context'] else 0
        
        if not data:
            logger.warning("没有可更新的字段")
            return False
        
        try:
            result = self.update(self.TABLE_NAME, data, id=qa_id)
            if result:
                logger.info(f"问答对更新成功: ID={qa_id}")
            return result
        except Exception as e:
            logger.error(f"更新问答对失败: {e}")
            return False
    
    # ==================== 删除操作 ====================
    
    def delete_qa_data(self, qa_id: int) -> bool:
        """
        删除问答对数据
        
        Args:
            qa_id: 问答对ID
            
        Returns:
            bool: 删除成功返回True
        """
        try:
            # 获取分组ID用于后续更新统计
            qa_data = self.get_qa_data_by_id(qa_id)
            group_id = qa_data.get('group_id') if qa_data else None
            
            success = self.delete(self.TABLE_NAME, id=qa_id)
            
            if success and group_id:
                logger.info(f"问答对删除成功: ID={qa_id}")
                # 更新分组统计
                self._update_group_qa_count(group_id)
            
            return success
            
        except Exception as e:
            logger.error(f"删除问答对失败: {e}")
            return False
    
    def delete_qa_data_by_group(self, group_id: int) -> int:
        """
        删除分组下的所有问答对数据
        
        Args:
            group_id: 分组ID
            
        Returns:
            int: 删除的记录数
        """
        try:
            # 使用PostgreSQLManager的execute_query方法执行批量删除
            query = f"DELETE FROM {self.TABLE_NAME} WHERE group_id = %s"
            result = self.execute_query(query, (group_id,))
            
            if result is True:
                # 查询删除的记录数（需要重新查询，因为execute_query不返回rowcount）
                count_query = f"SELECT COUNT(*) FROM {self.TABLE_NAME} WHERE group_id = %s"
                # 由于我们刚删除了这些记录，所以应该返回0，但我们可以通过之前的统计来估算
                deleted_count = self.cursor.rowcount if hasattr(self.cursor, 'rowcount') else 0
                logger.info(f"分组 {group_id} 下的问答对删除成功")
                
                # 更新分组统计
                self._update_group_qa_count(group_id)
                
                return deleted_count
            else:
                logger.warning(f"分组 {group_id} 下的问答对删除操作未成功执行")
                return 0
                
        except Exception as e:
            logger.error(f"批量删除问答对失败: {e}")
            return 0
    
    # ==================== 辅助方法 ====================
    
    def _process_answers(self, answers: Union[str, List[str], Dict]) -> Dict:
        """
        统一处理answers字段，转换为标准JSONB格式
        
        Args:
            answers: 原始答案数据
            
        Returns:
            Dict: 标准化后的答案字典
        """
        if isinstance(answers, str):
            return {'text': [answers], 'answer_start': []}
        elif isinstance(answers, list):
            return {'text': answers, 'answer_start': []}
        elif isinstance(answers, dict):
            # 已经是字典格式，确保有text字段
            if 'text' not in answers:
                # 尝试查找其他可能的答案字段
                for key in ['answer', 'answers', 'output', 'target']:
                    if key in answers:
                        value = answers[key]
                        if isinstance(value, str):
                            return {'text': [value], 'answer_start': []}
                        elif isinstance(value, list):
                            return {'text': value, 'answer_start': []}
            return answers
        else:
            return {'text': [str(answers)], 'answer_start': []}
    
    def _calculate_answer_length(self, answers: Dict) -> int:
        """
        计算答案长度
        
        Args:
            answers: 答案字典
            
        Returns:
            int: 答案总长度
        """
        total_length = 0
        if isinstance(answers, dict):
            texts = answers.get('text', [])
            if isinstance(texts, list):
                total_length = sum(len(str(t)) for t in texts)
            else:
                total_length = len(str(texts))
        return total_length
    
    def _update_group_qa_count(self, group_id: int):
        """更新分组的问答对数量统计"""
        try:
            count = self.count_qa_data(group_id=group_id)
            self.group_manager.update_group(group_id, qa_count=count)
        except Exception as e:
            logger.warning(f"更新分组统计失败: {e}")
    
    def _prepare_copy_data(self, data: Dict) -> List:
        """
        准备COPY命令所需的数据格式
        
        Args:
            data: 原始数据字典
            
        Returns:
            List: 处理后的数据列表
        """
        # 确保created_month字段
        if 'created_month' not in data:
            data['created_month'] = datetime.now().strftime('%Y-%m-%d')
        
        # 处理answers字段
        answers = self._process_answers(data.get('answers', ''))
        
        # 计算长度
        question_length = len(data.get('question', ''))
        answer_length = self._calculate_answer_length(answers)
        context_length = len(data.get('context', '')) if data.get('context') else 0
        
        return [
            data.get('group_id'),
            data.get('question', ''),
            json.dumps(answers, ensure_ascii=False),
            data.get('context', ''),
            data.get('question_type', ''),
            data.get('source_dataset', ''),
            data.get('hf_dataset_id', ''),
            data.get('language', 'zh'),
            data.get('difficulty_level'),
            data.get('category', ''),
            data.get('sub_category', ''),
            json.dumps(data.get('tags', []), ensure_ascii=False),
            json.dumps(data.get('fixed_metadata', {}), ensure_ascii=False),
            json.dumps(data.get('dynamic_metadata', {}), ensure_ascii=False),
            question_length,
            answer_length,
            context_length,
            data['created_month']
        ]
    
    def _row_to_dict(self, row: Tuple, similarity: float = None) -> Dict[str, Any]:
        """
        将数据库行转换为字典
        
        Args:
            row: 数据库行元组
            similarity: 相似度分数（可选）
            
        Returns:
            Dict: 转换后的字典
        """
        columns = [
            'id', 'qa_uuid', 'group_id', 'question', 'answers', 'context',
            'question_type', 'source_dataset', 'hf_dataset_id', 'language',
            'difficulty_level', 'category', 'sub_category', 'tags',
            'fixed_metadata', 'dynamic_metadata', 'vector_embedding',
            'question_length', 'answer_length', 'context_length',
            'created_at', 'updated_at', 'created_month'
        ]
        
        result = {}
        for i, col in enumerate(columns):
            if i < len(row):
                value = row[i]
                # 处理JSONB字段
                if col in ['answers', 'tags', 'fixed_metadata', 'dynamic_metadata'] and isinstance(value, str):
                    try:
                        value = json.loads(value)
                    except:
                        pass
                # 处理时间戳
                elif col in ['created_at', 'updated_at'] and hasattr(value, 'isoformat'):
                    value = value.isoformat()
                result[col] = value
        
        if similarity is not None:
            result['similarity'] = similarity
        
        return result
    
    def qa_data_exists(self, qa_id: int) -> bool:
        """检查问答对是否存在"""
        return self.get_qa_data_by_id(qa_id) is not None
