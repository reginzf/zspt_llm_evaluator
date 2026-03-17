#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XLSX 导入功能测试脚本

用法:
    python test_xlsx_import.py

此脚本会:
1. 创建一个测试用的 xlsx 文件
2. 测试预览功能
3. 测试导入功能
"""

import os
import sys
import tempfile
import json

# 添加项目路径
sys.path.insert(0, '/root/.openclaw/workspace/zspt_llm_evaluator')

def create_test_xlsx():
    """创建测试用的 xlsx 文件"""
    try:
        import pandas as pd
    except ImportError:
        print("❌ 错误: 未安装 pandas，请运行: pip install pandas openpyxl")
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


def test_preview_xlsx(file_path):
    """测试 xlsx 预览功能"""
    print("\n=== 测试预览功能 ===")
    
    try:
        from src.sql_funs.ai_qa_data_crud_enhanced import EnhancedAIQADataManager
        
        manager = EnhancedAIQADataManager()
        preview = manager._preview_xlsx_file(file_path, preview_rows=5)
        
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


def test_smart_mapping(file_path):
    """测试智能字段映射建议"""
    print("\n=== 测试智能字段映射 ===")
    
    try:
        from src.sql_funs.ai_qa_data_crud_enhanced import EnhancedAIQADataManager
        
        manager = EnhancedAIQADataManager()
        preview = manager._preview_xlsx_file(file_path, preview_rows=5)
        
        if preview.error:
            print(f"❌ 获取列失败: {preview.error}")
            return False
        
        suggestions = manager.get_smart_mapping_suggestions(preview.columns)
        
        print(f"✅ 智能映射建议:")
        for ai_field, source_field in suggestions.items():
            print(f"   {ai_field} -> {source_field}")
        
        return True
        
    except Exception as e:
        print(f"❌ 智能映射测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def cleanup(file_path):
    """清理临时文件"""
    if file_path and os.path.exists(file_path):
        os.unlink(file_path)
        print(f"\n✅ 清理临时文件: {file_path}")


def main():
    print("=" * 60)
    print("XLSX 导入功能测试")
    print("=" * 60)
    
    # 检查依赖
    try:
        import pandas as pd
        import openpyxl
        print("✅ pandas 和 openpyxl 已安装")
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: pip install pandas openpyxl")
        return 1
    
    # 创建测试文件
    test_file = create_test_xlsx()
    if not test_file:
        return 1
    
    try:
        # 运行测试
        results = []
        
        results.append(("预览功能", test_preview_xlsx(test_file)))
        results.append(("智能映射", test_smart_mapping(test_file)))
        
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
