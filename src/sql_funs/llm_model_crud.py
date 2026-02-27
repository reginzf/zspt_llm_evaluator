# -*- coding: utf-8 -*-
"""
LLM模型管理CRUD操作模块
"""
from typing import Optional, List, Dict, Any
from src.sql_funs.sql_base import PostgreSQLManager
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class LLMModelManager(PostgreSQLManager):
    """LLM模型管理器"""
    
    TABLE_NAME = "ai_llm_models"
    
    def __init__(self):
        super().__init__()
    
    def create_model(self, name, model_type, api_key, api_url,
                     model=None, temperature=0.7, max_tokens=2048,
                     timeout=30, version=None):
        """创建LLM模型配置"""
        try:
            data = {
                "name": name,
                "type": model_type,
                "api_key": api_key,
                "api_url": api_url,
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "timeout": timeout,
                "version": version
            }
            data = {k: v for k, v in data.items() if v is not None}
            
            # 插入数据
            success = self.insert(self.TABLE_NAME, data)
            if success:
                # 查询获取刚插入的记录的ID
                query = f"SELECT id FROM {self.TABLE_NAME} WHERE name = %s ORDER BY created_at DESC LIMIT 1"
                result = self.execute_query(query, (name,))
                if result:
                    model_id = result[0][0]
                    logger.info(f"LLM模型创建成功: ID={model_id}, name={name}")
                    return model_id
            return None
        except Exception as e:
            logger.error(f"创建LLM模型失败: {e}")
            return None
    
    def get_model_by_id(self, model_id):
        """根据ID获取模型配置"""
        try:
            query = f"SELECT * FROM {self.TABLE_NAME} WHERE id = %s"
            result = self.execute_query(query, (model_id,))
            if result:
                return self._row_to_dict(result[0])
            return None
        except Exception as e:
            logger.error(f"获取模型失败: {e}")
            return None
    
    def get_model_by_name(self, name):
        """根据名称获取模型配置"""
        try:
            query = f"SELECT * FROM {self.TABLE_NAME} WHERE name = %s AND is_active = TRUE"
            result = self.execute_query(query, (name,))
            if result:
                return self._row_to_dict(result[0])
            return None
        except Exception as e:
            logger.error(f"获取模型失败: {e}")
            return None
    
    def list_models(self, model_type=None, status=None, keyword=None, limit=None, offset=0):
        """获取模型列表"""
        try:
            conditions = ["is_active = TRUE"]
            params = []
            
            if model_type:
                conditions.append("type = %s")
                params.append(model_type)
            if status:
                conditions.append("status = %s")
                params.append(status)
            if keyword:
                conditions.append("name ILIKE %s")
                params.append(f"%{keyword}%")
            
            where_clause = " AND ".join(conditions)
            query = f"SELECT * FROM {self.TABLE_NAME} WHERE {where_clause} ORDER BY created_at DESC"
            
            if limit:
                query += f" LIMIT {limit}"
            if offset:
                query += f" OFFSET {offset}"
            
            result = self.execute_query(query, tuple(params) if params else None)
            if result:
                return [self._row_to_dict(row) for row in result]
            return []
        except Exception as e:
            logger.error(f"获取模型列表失败: {e}")
            return []
    
    def count_models(self, model_type=None, status=None, keyword=None):
        """统计模型数量"""
        try:
            conditions = ["is_active = TRUE"]
            params = []
            
            if model_type:
                conditions.append("type = %s")
                params.append(model_type)
            if status:
                conditions.append("status = %s")
                params.append(status)
            if keyword:
                conditions.append("name ILIKE %s")
                params.append(f"%{keyword}%")
            
            where_clause = " AND ".join(conditions)
            query = f"SELECT COUNT(*) FROM {self.TABLE_NAME} WHERE {where_clause}"
            
            result = self.execute_query(query, tuple(params) if params else None)
            return result[0][0] if result else 0
        except Exception as e:
            logger.error(f"统计模型数量失败: {e}")
            return 0
    
    def update_model(self, model_id, **kwargs):
        """更新模型配置"""
        try:
            forbidden_fields = {'id', 'created_at'}
            data = {k: v for k, v in kwargs.items() if k not in forbidden_fields}
            
            if not data:
                return False
            
            data['updated_at'] = datetime.now()
            return self.update(self.TABLE_NAME, data, id=model_id)
        except Exception as e:
            logger.error(f"更新模型失败: {e}")
            return False
    
    def delete_model(self, model_id):
        """删除模型（软删除）"""
        return self.update_model(model_id, is_active=False)
    
    def update_status(self, model_id, status):
        """更新模型状态"""
        return self.update_model(model_id, status=status, last_check=datetime.now())
    
    def model_exists(self, name):
        """检查模型名称是否已存在"""
        try:
            query = f"SELECT COUNT(*) FROM {self.TABLE_NAME} WHERE name = %s AND is_active = TRUE"
            result = self.execute_query(query, (name,))
            return result[0][0] > 0 if result else False
        except Exception as e:
            logger.error(f"检查模型存在失败: {e}")
            return False
    
    def _row_to_dict(self, row):
        """将数据库行转换为字典"""
        from decimal import Decimal
        
        columns = [
            'id', 'name', 'type', 'api_key', 'api_url', 'model',
            'temperature', 'max_tokens', 'timeout', 'version',
            'status', 'last_check', 'is_active', 'created_at', 'updated_at'
        ]
        
        result = {}
        for i, col in enumerate(columns):
            if i < len(row):
                value = row[i]
                # 处理时间戳
                if col in ['created_at', 'updated_at', 'last_check'] and hasattr(value, 'isoformat'):
                    value = value.isoformat()
                # 处理Decimal类型
                elif isinstance(value, Decimal):
                    value = float(value)
                result[col] = value
        return result
