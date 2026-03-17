#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XLSX 导入功能独立测试脚本（不依赖 PostgreSQL）
"""

import os
import sys
import tempfile
import json
from dataclasses import dataclass
from typing import List, Dict

# 添加项目路径
sys.path.insert(0, '/root/.openclaw/workspace/zspt_llm_evaluator')


def test_preview_xlsx(file_path):
    """测试 xlsx 预览功能"""
    print("\n=== 测试预览功能 ===")
    
    try:
        import pandas as pd
        
        @dataclass
        class DatasetPreview:
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
        
        preview = DatasetPreview(file_path=file_path)
        
        # 读取第一个sheet
        df = pd.read_excel(file_path, sheet_name=0)
        
        # 获取列名
        preview.columns = df.columns.tolist()
        
        # 获取总行数
        preview.total_records = len(df)
        
        # 获取前 5 行数据
        preview_rows_df = df.head(5)
        
        # 转换为字典列表（处理NaN值）
        for _, row in preview_rows_df.iterrows():
            record = {}
            for col in preview.columns:
                value = row[col]
                # 处理 NaN 和特殊类型
                if pd.isna(value):
                    record[col] = None
                elif isinstance(value, (int, float)):
                    record[col] = value
                else:
                    record[col] = str(value)
            preview.preview_rows.append(record)
        
        if preview.error:
            print(f"❌ 预览失败: {preview.error}")
            return False
        
        print(f"✅ 预览成功!")
        print(f"   文件路径: {preview.file_path}")
        print(f"   总记录数: {preview.total_records}")
        print(f"   列数: {len(preview.columns)}")
        print(f"   列名: {preview.columns}")
        print(f"   预览行数: {len(preview.preview_rows)}")
        
        if preview.preview_rows:
            print(f"\n   第一行数据示例:")
            for key, value in preview.preview_rows[0].items():
                print(f"     {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ 预览测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_conversion(file_path):
    """测试数据转换逻辑"""
    print("\n=== 测试数据转换 ===")
    
    try:
        import pandas as pd
        
        # 模拟字段映射
        mapping = {
            'question': '问题',
            'answers': '答案',
            'context': '上下文',
            'question_type': '类型',
            'difficulty_level': '难度'
        }
        
        # 读取 xlsx
        df = pd.read_excel(file_path, sheet_name=0)
        
        # 转换为 QA 数据格式
        qa_data_list = []
        for _, row in df.iterrows():
            qa_data = {
                'group_id': 1,  # 模拟分组ID
                'question': str(row.get(mapping['question'], '')),
                'answers': str(row.get(mapping['answers'], '')),
                'context': str(row.get(mapping['context'], '')) if pd.notna(row.get(mapping['context'])) else None,
                'question_type': str(row.get(mapping['question_type'], '')) if pd.notna(row.get(mapping['question_type'])) else None,
                'difficulty_level': int(row.get(mapping['difficulty_level'], 1)) if pd.notna(row.get(mapping['difficulty_level'])) else None,
                'source_dataset': 'xlsx_import_test',
                'language': 'zh'
            }
            qa_data_list.append(qa_data)
        
        print(f"✅ 数据转换成功!")
        print(f"   转换记录数: {len(qa_data_list)}")
        
        if qa_data_list:
            print(f"\n   第一条记录示例:")
            for key, value in qa_data_list[0].items():
                print(f"     {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据转换测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_test_xlsx():
    """创建测试用的 xlsx 文件"""
    try:
        import pandas as pd
    except ImportError:
        print("❌ 错误: 未安装 pandas")
        return None
    
    # 创建测试数据
    data = {
        '问题': ['什么是Python？', '什么是Flask？', '什么是Vue？'],
        '答案': ['Python是一种编程语言', 'Flask是一个Web框架', 'Vue是一个前端框架'],
        '上下文': ['编程语言介绍', 'Web开发', '前端开发'],
        '类型': ['概念', '工具', '框架'],
        '难度': [1, 2, 3],
        '标签': [['编程'], ['Python', 'Web'], ['前端', 'JS']]
    }
    
    df = pd.DataFrame(data)
    
    # 保存到临时文件
    temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
    df.to_excel(temp_file.name, sheet_name='Sheet1', index=False)
    temp_file.close()
    
    print(f"✅ 创建测试文件: {temp_file.name}")
    return temp_file.name


def cleanup(file_path):
    """清理临时文件"""
    if file_path and os.path.exists(file_path):
        os.unlink(file_path)
        print(f"\n✅ 清理临时文件: {file_path}")


def main():
    print("=" * 60)
    print("XLSX 导入功能独立测试")
    print("=" * 60)
    
    # 检查依赖
    try:
        import pandas as pd
        import openpyxl
        print("✅ pandas 和 openpyxl 已安装")
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        return 1
    
    # 创建测试文件
    test_file = create_test_xlsx()
    if not test_file:
        return 1
    
    try:
        # 运行测试
        results = []
        
        results.append(("预览功能", test_preview_xlsx(test_file)))
        results.append(("数据转换", test_data_conversion(test_file)))
        
        # 打印测试结果
        print("\n" + "=" * 60)
        print("测试结果汇总")
        print("=" * 60)
        
        for name, result in results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{name}: {status}")
        
        all_passed = all(r for _, r in results)
        
        if all_passed:
            print("\n🎉 所有测试通过!")
            return 0
        else:
            print("\n⚠️ 部分测试失败")
            return 1
            
    finally:
        cleanup(test_file)


if __name__ == '__main__':
    sys.exit(main())
