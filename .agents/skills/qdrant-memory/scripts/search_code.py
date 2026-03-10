#!/usr/bin/env python3
"""
代码搜索工具 - Kimi 专用版
简化版接口，便于 Kimi 调用

用法:
    python search_code.py "搜索关键词"
"""

import sys
import subprocess
from pathlib import Path

# 检测路径
SCRIPT_DIR = Path(__file__).parent.resolve()

def search(query: str):
    """执行代码搜索"""
    if not query.strip():
        print("[Error] 搜索词不能为空")
        return 1
    
    # 构建命令 - 使用当前脚本所在目录的 qdrant_search.py
    qdrant_script = SCRIPT_DIR / "qdrant_search.py"
    cmd = [
        ".venv\\Scripts\\python",
        str(qdrant_script),
        "search",
        query
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, encoding='utf-8', errors='ignore')
        # 使用 stdout.buffer 直接输出，避免编码问题
        sys.stdout.buffer.write(result.stdout.encode('utf-8', errors='ignore'))
        if result.stderr:
            sys.stderr.buffer.write(result.stderr.encode('utf-8', errors='ignore'))
        return result.returncode
    except Exception as e:
        print(f"[Error] 搜索失败: {e}")
        return 1

def main():
    if len(sys.argv) < 2:
        print("用法: python search_code.py \"搜索关键词\"")
        print("示例: python search_code.py \"Flask蓝图注册\"")
        return 1
    
    query = sys.argv[1]
    return search(query)

if __name__ == "__main__":
    sys.exit(main())
