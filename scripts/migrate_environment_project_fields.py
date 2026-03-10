#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境表项目字段数据迁移脚本

此脚本用于向现有的ai_environment_info表中添加project_name和project_id字段，
并对现有数据进行适当的默认值填充。
"""

import sys
import os
import logging
from typing import List, Dict, Any

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.sql_funs.sql_base import PostgreSQLManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class EnvironmentMigration:
    """环境表迁移类"""
    
    def __init__(self):
        self.db_manager = PostgreSQLManager()
    
    def check_migration_needed(self) -> bool:
        """检查是否需要进行迁移"""
        try:
            # 检查project_name字段是否存在
            query = """
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'ai_environment_info' 
                AND column_name = 'project_name'
            """
            result = self.db_manager.execute_query(query)
            return len(result) == 0
        except Exception as e:
            logger.error(f"检查迁移需求时发生错误: {e}")
            return False
    
    def add_project_fields(self) -> bool:
        """向表中添加项目相关字段"""
        try:
            # 添加project_name字段
            alter_sql_1 = """
                ALTER TABLE ai_environment_info 
                ADD COLUMN IF NOT EXISTS project_name VARCHAR(200)
            """
            
            # 添加project_id字段
            alter_sql_2 = """
                ALTER TABLE ai_environment_info 
                ADD COLUMN IF NOT EXISTS project_id VARCHAR(100)
            """
            
            # 执行SQL语句
            self.db_manager.cursor.execute(alter_sql_1)
            self.db_manager.cursor.execute(alter_sql_2)
            self.db_manager.connection.commit()
            
            logger.info("成功添加project_name和project_id字段")
            return True
            
        except Exception as e:
            self.db_manager.connection.rollback()
            logger.error(f"添加字段时发生错误: {e}")
            return False
    
    def migrate_existing_data(self) -> bool:
        """迁移现有数据，为项目字段设置默认值"""
        try:
            # 为现有记录设置默认项目名称（基于环境名称）
            update_sql = """
                UPDATE ai_environment_info 
                SET project_name = CASE 
                    WHEN zlpt_name ILIKE '%生产%' OR zlpt_name ILIKE '%prod%' THEN '生产项目'
                    WHEN zlpt_name ILIKE '%测试%' OR zlpt_name ILIKE '%test%' THEN '测试项目'
                    WHEN zlpt_name ILIKE '%开发%' OR zlpt_name ILIKE '%dev%' THEN '开发项目'
                    ELSE CONCAT('项目_', zlpt_name)
                END,
                project_id = CONCAT('proj_', REPLACE(zlpt_base_id, 'env_', ''))
                WHERE project_name IS NULL OR project_name = ''
            """
            
            self.db_manager.cursor.execute(update_sql)
            affected_rows = self.db_manager.cursor.rowcount
            self.db_manager.connection.commit()
            
            logger.info(f"成功更新 {affected_rows} 条记录的项目字段")
            return True
            
        except Exception as e:
            self.db_manager.connection.rollback()
            logger.error(f"迁移现有数据时发生错误: {e}")
            return False
    
    def create_indexes(self) -> bool:
        """为新字段创建索引"""
        try:
            # 为project_name创建索引
            index_sql_1 = """
                CREATE INDEX IF NOT EXISTS idx_environment_project_name 
                ON ai_environment_info(project_name)
            """
            
            # 为project_id创建索引
            index_sql_2 = """
                CREATE INDEX IF NOT EXISTS idx_environment_project_id 
                ON ai_environment_info(project_id)
            """
            
            self.db_manager.cursor.execute(index_sql_1)
            self.db_manager.cursor.execute(index_sql_2)
            self.db_manager.connection.commit()
            
            logger.info("成功创建项目字段索引")
            return True
            
        except Exception as e:
            self.db_manager.connection.rollback()
            logger.error(f"创建索引时发生错误: {e}")
            return False
    
    def validate_migration(self) -> bool:
        """验证迁移结果"""
        try:
            # 检查字段是否存在
            check_columns_sql = """
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'ai_environment_info' 
                AND column_name IN ('project_name', 'project_id')
            """
            columns_result = self.db_manager.execute_query(check_columns_sql)
            
            if len(columns_result) != 2:
                logger.error("字段验证失败：project_name或project_id字段缺失")
                return False
            
            # 检查数据完整性
            check_data_sql = """
                SELECT COUNT(*) as total_count,
                       COUNT(project_name) as project_name_count,
                       COUNT(project_id) as project_id_count
                FROM ai_environment_info
            """
            data_result = self.db_manager.execute_query(check_data_sql)
            
            if data_result:
                stats = data_result[0]
                logger.info(f"数据统计 - 总记录数: {stats[0]}, "
                           f"有项目名称: {stats[1]}, 有项目ID: {stats[2]}")
                
                # 检查是否有空值
                if stats[1] < stats[0] or stats[2] < stats[0]:
                    logger.warning("发现部分记录的项目字段为空")
                    
            return True
            
        except Exception as e:
            logger.error(f"验证迁移结果时发生错误: {e}")
            return False
    
    def rollback_migration(self) -> bool:
        """回滚迁移（谨慎使用）"""
        try:
            # 删除添加的字段
            drop_sql_1 = "ALTER TABLE ai_environment_info DROP COLUMN IF EXISTS project_name"
            drop_sql_2 = "ALTER TABLE ai_environment_info DROP COLUMN IF EXISTS project_id"
            
            self.db_manager.cursor.execute(drop_sql_1)
            self.db_manager.cursor.execute(drop_sql_2)
            self.db_manager.connection.commit()
            
            logger.info("成功回滚迁移")
            return True
            
        except Exception as e:
            self.db_manager.connection.rollback()
            logger.error(f"回滚迁移时发生错误: {e}")
            return False
    
    def run_migration(self) -> bool:
        """执行完整的迁移流程"""
        logger.info("开始环境表项目字段迁移...")
        
        # 检查是否需要迁移
        if not self.check_migration_needed():
            logger.info("表结构已经是最新版本，无需迁移")
            return True
        
        # 执行迁移步骤
        steps = [
            ("添加项目字段", self.add_project_fields),
            ("迁移现有数据", self.migrate_existing_data),
            ("创建索引", self.create_indexes),
            ("验证迁移结果", self.validate_migration)
        ]
        
        for step_name, step_func in steps:
            logger.info(f"执行步骤: {step_name}")
            if not step_func():
                logger.error(f"步骤 '{step_name}' 执行失败")
                return False
            logger.info(f"步骤 '{step_name}' 执行成功")
        
        logger.info("环境表项目字段迁移完成！")
        return True


def main():
    """主函数"""
    migration = EnvironmentMigration()
    
    try:
        success = migration.run_migration()
        if success:
            print("✅ 迁移成功完成！")
            sys.exit(0)
        else:
            print("❌ 迁移失败！")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  用户中断迁移过程")
        sys.exit(1)
    except Exception as e:
        logger.error(f"迁移过程中发生未预期的错误: {e}")
        print(f"❌ 迁移失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()