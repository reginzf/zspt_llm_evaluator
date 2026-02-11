# -*- coding: utf-8 -*-
"""
AI问答对分组管理CRUD操作模块

此模块提供了AI问答对分组的完整CRUD操作接口，
包括分组的增删改查、统计等功能。
"""
from typing import Optional, List, Tuple, Dict, Any
from src.sql_funs.sql_base import PostgreSQLManager
import logging
import json

logger = logging.getLogger(__name__)


class AIQADataGroupManager(PostgreSQLManager):
    """
    AI问答对分组管理器
    
    继承自PostgreSQLManager，提供针对ai_qa_data_group表的完整CRUD操作，
    包括分组的创建、更新、删除、查询等操作。
    """
    
    TABLE_NAME = "ai_qa_data_group"
    
    def __init__(self):
        super().__init__()
    
    # ==================== 创建操作 ====================
    
    def create_group(self, name: str, purpose: str = None, test_type: str = 'custom',
                     language: str = 'zh', difficulty_range: str = None,
                     tags: List[str] = None, metadata: Dict = None) -> Optional[int]:
        """
        创建新的问答对分组
        
        Args:
            name: 分组名称（必填）
            purpose: 用途描述
            test_type: 测试类型 ('accuracy', 'performance', 'robustness', 'comprehensive', 'custom')
            language: 语言，默认'zh'
            difficulty_range: 难度范围，如 "1-5"
            tags: 标签列表
            metadata: 额外配置信息字典
            
        Returns:
            Optional[int]: 新创建分组的ID，失败返回None
        """
        try:
            data = {
                "name": name,
                "purpose": purpose,
                "test_type": test_type,
                "language": language,
                "difficulty_range": difficulty_range,
                "tags": tags or [],
                "metadata": metadata or {}
            }
            
            # 移除None值
            data = {k: v for k, v in data.items() if v is not None}
            
            success = self.insert(self.TABLE_NAME, data)
            
            if success:
                # 获取刚创建的记录ID
                query = f"""
                SELECT id FROM {self.TABLE_NAME} 
                WHERE name = %s AND created_at > NOW() - INTERVAL '5 seconds'
                ORDER BY created_at DESC LIMIT 1
                """
                result = self.execute_query(query, (name,))
                if result:
                    group_id = result[0][0]
                    logger.info(f"分组创建成功: ID={group_id}, name={name}")
                    return group_id
            
            return None
            
        except Exception as e:
            logger.error(f"创建分组失败: {e}")
            return None
    
    def create_group_with_uuid(self, group_uuid: str, name: str, **kwargs) -> bool:
        """
        使用指定UUID创建分组（用于数据导入时保持UUID一致）
        
        Args:
            group_uuid: 指定的UUID
            name: 分组名称
            **kwargs: 其他字段
            
        Returns:
            bool: 创建成功返回True
        """
        try:
            data = {
                "group_uuid": group_uuid,
                "name": name,
                **kwargs
            }
            
            # 处理列表和字典类型
            for key, value in data.items():
                if isinstance(value, (list, dict)):
                    data[key] = json.dumps(value, ensure_ascii=False)
            
            columns = list(data.keys())
            values = list(data.values())
            placeholders = ", ".join(["%s"] * len(values))
            
            query = f"INSERT INTO {self.TABLE_NAME} ({', '.join(columns)}) VALUES ({placeholders})"
            
            self.cursor.execute(query, values)
            self.connection.commit()
            logger.info(f"分组创建成功: UUID={group_uuid}, name={name}")
            return True
            
        except Exception as e:
            self.connection.rollback()
            logger.error(f"创建分组失败: {e}")
            return False
    
    # ==================== 读取操作 ====================
    
    def get_group_by_id(self, group_id: int) -> Optional[Dict[str, Any]]:
        """
        根据ID获取分组信息
        
        Args:
            group_id: 分组ID
            
        Returns:
            Optional[Dict]: 分组信息字典，不存在返回None
        """
        query = f"SELECT * FROM {self.TABLE_NAME} WHERE id = %s"
        result = self.execute_query(query, (group_id,))
        
        if result:
            return self._row_to_dict(result[0])
        return None
    
    def get_group_by_uuid(self, group_uuid: str) -> Optional[Dict[str, Any]]:
        """
        根据UUID获取分组信息
        
        Args:
            group_uuid: 分组UUID
            
        Returns:
            Optional[Dict]: 分组信息字典，不存在返回None
        """
        query = f"SELECT * FROM {self.TABLE_NAME} WHERE group_uuid = %s"
        result = self.execute_query(query, (group_uuid,))
        
        if result:
            return self._row_to_dict(result[0])
        return None
    
    def list_groups(self, name: str = None, test_type: str = None, 
                    is_active: bool = None, language: str = None,
                    order_by: str = 'created_at DESC', limit: int = None,
                    offset: int = None) -> List[Dict[str, Any]]:
        """
        获取分组列表
        
        Args:
            name: 按名称模糊匹配
            test_type: 按测试类型筛选
            is_active: 按激活状态筛选
            language: 按语言筛选
            order_by: 排序字段
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            List[Dict]: 分组信息字典列表
        """
        # 使用gen_select_query方法生成查询
        exact_match_fields = {'test_type', 'is_active', 'language'}
        partial_match_fields = {'name'}
        allowed_fields = exact_match_fields | partial_match_fields
        
        # 构建查询参数
        query_params = {}
        if name is not None:
            query_params['name'] = name
        if test_type is not None:
            query_params['test_type'] = test_type
        if is_active is not None:
            query_params['is_active'] = is_active
        if language is not None:
            query_params['language'] = language
        
        if query_params:
            query, params = self.gen_select_query(
                self.TABLE_NAME,
                order_by=order_by,
                limit=limit,
                exact_match_fields=list(exact_match_fields),
                partial_match_fields=list(partial_match_fields),
                allowed_fileds=list(allowed_fields),
                **query_params
            )
            result = self.execute_query(query, params)
        else:
            # 无筛选条件时查询所有记录
            base_query = f"SELECT * FROM {self.TABLE_NAME}"
            if order_by:
                base_query += f" ORDER BY {order_by}"
            if limit:
                base_query += f" LIMIT {limit}"
            if offset:
                base_query += f" OFFSET {offset}"
            result = self.execute_query(base_query)
        
        if result:
            return [self._row_to_dict(row) for row in result]
        return []
    
    def count_groups(self, **filters) -> int:
        """
        统计分组数量
        
        Args:
            **filters: 筛选条件
            
        Returns:
            int: 分组数量
        """
        conditions = []
        params = []
        
        if 'name' in filters and filters['name']:
            conditions.append("name LIKE %s")
            params.append(f"%{filters['name']}%")
        
        if 'test_type' in filters and filters['test_type']:
            conditions.append("test_type = %s")
            params.append(filters['test_type'])
        
        if 'is_active' in filters and filters['is_active'] is not None:
            conditions.append("is_active = %s")
            params.append(filters['is_active'])
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        query = f"SELECT COUNT(*) FROM {self.TABLE_NAME} {where_clause}"
        result = self.execute_query(query, tuple(params) if params else None)
        
        return result[0][0] if result else 0
    
    # ==================== 更新操作 ====================
    
    def update_group(self, group_id: int, **kwargs) -> bool:
        """
        更新分组信息
        
        Args:
            group_id: 分组ID
            **kwargs: 要更新的字段
            
        Returns:
            bool: 更新成功返回True
        """
        # 不允许更新的字段
        forbidden_fields = {'id', 'group_uuid', 'created_at'}
        
        data = {k: v for k, v in kwargs.items() if k not in forbidden_fields and v is not None}
        
        if not data:
            logger.warning("没有可更新的字段")
            return False
        
        try:
            result = self.update(self.TABLE_NAME, data, id=group_id)
            if result:
                logger.info(f"分组更新成功: ID={group_id}")
            return result
        except Exception as e:
            logger.error(f"更新分组失败: {e}")
            return False
    
    def update_qa_count(self, group_id: int, count: int = None) -> bool:
        """
        更新分组的问答对数量
        
        Args:
            group_id: 分组ID
            count: 指定数量，为None则自动统计
            
        Returns:
            bool: 更新成功返回True
        """
        try:
            if count is None:
                # 自动统计
                query = "SELECT COUNT(*) FROM ai_qa_data WHERE group_id = %s"
                result = self.execute_query(query, (group_id,))
                count = result[0][0] if result else 0
            
            return self.update_group(group_id, qa_count=count)
            
        except Exception as e:
            logger.error(f"更新问答对数量失败: {e}")
            return False
    
    def activate_group(self, group_id: int) -> bool:
        """激活分组"""
        return self.update_group(group_id, is_active=True)
    
    def deactivate_group(self, group_id: int) -> bool:
        """停用分组"""
        return self.update_group(group_id, is_active=False)
    
    def add_tags(self, group_id: int, tags: List[str]) -> bool:
        """
        为分组添加标签
        
        Args:
            group_id: 分组ID
            tags: 要添加的标签列表
            
        Returns:
            bool: 添加成功返回True
        """
        try:
            group = self.get_group_by_id(group_id)
            if not group:
                logger.warning(f"分组不存在: ID={group_id}")
                return False
            
            current_tags = group.get('tags', [])
            new_tags = list(set(current_tags + tags))  # 去重
            
            return self.update_group(group_id, tags=new_tags)
            
        except Exception as e:
            logger.error(f"添加标签失败: {e}")
            return False
    
    def remove_tags(self, group_id: int, tags: List[str]) -> bool:
        """
        从分组移除标签
        
        Args:
            group_id: 分组ID
            tags: 要移除的标签列表
            
        Returns:
            bool: 移除成功返回True
        """
        try:
            group = self.get_group_by_id(group_id)
            if not group:
                logger.warning(f"分组不存在: ID={group_id}")
                return False
            
            current_tags = group.get('tags', [])
            new_tags = [t for t in current_tags if t not in tags]
            
            return self.update_group(group_id, tags=new_tags)
            
        except Exception as e:
            logger.error(f"移除标签失败: {e}")
            return False
    
    # ==================== 删除操作 ====================
    
    def delete_group(self, group_id: int, force: bool = False) -> bool:
        """
        删除分组
        
        Args:
            group_id: 分组ID
            force: 是否强制删除（有关联数据时也删除）
            
        Returns:
            bool: 删除成功返回True
        """
        try:
            if not force:
                # 检查是否有关联的问答对数据
                query = "SELECT COUNT(*) FROM ai_qa_data WHERE group_id = %s"
                result = self.execute_query(query, (group_id,))
                count = result[0][0] if result else 0
                
                if count > 0:
                    logger.warning(f"分组下还有 {count} 条问答对数据，无法删除")
                    return False
            
            success = self.delete(self.TABLE_NAME, id=group_id)
            if success:
                logger.info(f"分组删除成功: ID={group_id}")
            return success
            
        except Exception as e:
            logger.error(f"删除分组失败: {e}")
            return False
    
    def delete_group_by_uuid(self, group_uuid: str, force: bool = False) -> bool:
        """
        根据UUID删除分组
        
        Args:
            group_uuid: 分组UUID
            force: 是否强制删除
            
        Returns:
            bool: 删除成功返回True
        """
        group = self.get_group_by_uuid(group_uuid)
        if group:
            return self.delete_group(group['id'], force)
        return False
    
    # ==================== 统计操作 ====================
    
    def get_group_statistics(self, group_id: int) -> Dict[str, Any]:
        """
        获取分组统计信息
        
        Args:
            group_id: 分组ID
            
        Returns:
            Dict: 统计信息字典
        """
        try:
            # 基础统计
            query = """
            SELECT 
                COUNT(*) as total_qa,
                COUNT(DISTINCT source_dataset) as source_count,
                AVG(difficulty_level) as avg_difficulty,
                MIN(difficulty_level) as min_difficulty,
                MAX(difficulty_level) as max_difficulty,
                COUNT(DISTINCT category) as category_count,
                COUNT(DISTINCT language) as language_count
            FROM ai_qa_data 
            WHERE group_id = %s
            """
            result = self.execute_query(query, (group_id,))
            
            stats = {}
            if result and result[0]:
                row = result[0]
                stats = {
                    'total_qa': row[0] or 0,
                    'source_count': row[1] or 0,
                    'avg_difficulty': round(row[2], 2) if row[2] else 0,
                    'min_difficulty': row[3] or 0,
                    'max_difficulty': row[4] or 0,
                    'category_count': row[5] or 0,
                    'language_count': row[6] or 0
                }
            
            # 按分类统计
            category_query = """
            SELECT category, COUNT(*) as count
            FROM ai_qa_data 
            WHERE group_id = %s AND category IS NOT NULL
            GROUP BY category
            ORDER BY count DESC
            """
            category_result = self.execute_query(category_query, (group_id,))
            stats['category_distribution'] = {
                row[0]: row[1] for row in category_result
            } if category_result else {}
            
            # 按难度统计
            difficulty_query = """
            SELECT difficulty_level, COUNT(*) as count
            FROM ai_qa_data 
            WHERE group_id = %s AND difficulty_level IS NOT NULL
            GROUP BY difficulty_level
            ORDER BY difficulty_level
            """
            difficulty_result = self.execute_query(difficulty_query, (group_id,))
            stats['difficulty_distribution'] = {
                row[0]: row[1] for row in difficulty_result
            } if difficulty_result else {}
            
            return stats
            
        except Exception as e:
            logger.error(f"获取分组统计信息失败: {e}")
            return {}
    
    # ==================== 辅助方法 ====================
    
    def _row_to_dict(self, row: Tuple) -> Dict[str, Any]:
        """
        将数据库行转换为字典
        
        Args:
            row: 数据库行元组
            
        Returns:
            Dict: 转换后的字典
        """
        columns = [
            'id', 'group_uuid', 'name', 'purpose', 'test_type', 'language',
            'difficulty_range', 'tags', 'source_count', 'qa_count', 'is_active',
            'created_at', 'updated_at', 'metadata'
        ]
        
        result = {}
        for i, col in enumerate(columns):
            if i < len(row):
                value = row[i]
                # 处理JSONB字段
                if col in ['tags', 'metadata'] and isinstance(value, str):
                    try:
                        value = json.loads(value)
                    except:
                        pass
                # 处理时间戳
                elif col in ['created_at', 'updated_at'] and hasattr(value, 'isoformat'):
                    value = value.isoformat()
                result[col] = value
        
        return result
    
    def group_exists(self, group_id: int) -> bool:
        """检查分组是否存在"""
        return self.get_group_by_id(group_id) is not None
    
    def group_exists_by_uuid(self, group_uuid: str) -> bool:
        """根据UUID检查分组是否存在"""
        return self.get_group_by_uuid(group_uuid) is not None
