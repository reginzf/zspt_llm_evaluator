#!/usr/bin/env python3
"""
Qdrant 语义搜索 - 简单实用版
直接在项目根目录运行，无需 MCP

使用方法:
  1. 索引代码: python qdrant_search.py index
  2. 搜索:     python qdrant_search.py search "你的问题"
  3. 交互模式: python qdrant_search.py interactive
"""

import os
import sys
from pathlib import Path

# 配置 - 自动检测项目根目录
SCRIPT_DIR = Path(__file__).parent.resolve()  # scripts/
SKILL_DIR = SCRIPT_DIR.parent  # qdrant-memory/
SKILLS_DIR = SKILL_DIR.parent  # skills/
AGENTS_DIR = SKILLS_DIR.parent  # .agents/
PROJECT_ROOT = AGENTS_DIR.parent  # 项目根目录

MODELS_DIR = PROJECT_ROOT / "models"
INDEX_FILE = SKILL_DIR / "qdrant_index.pkl"

# 确保能找到项目根目录（通过检查 .git 或 src 目录）
if not (PROJECT_ROOT / ".git").exists() and not (PROJECT_ROOT / "src").exists():
    print(f"[Warning] 可能未正确检测到项目根目录: {PROJECT_ROOT}")


def get_model():
    """加载本地模型"""
    from sentence_transformers import SentenceTransformer
    
    model_path = MODELS_DIR / "bge-base-zh-v1.5"
    if not model_path.exists():
        model_path = MODELS_DIR / "paraphrase-multilingual-MiniLM-L12-v2"
    
    print(f"[Load] 模型: {model_path.name}")
    return SentenceTransformer(str(model_path))


def index_code():
    """索引项目代码"""
    from sentence_transformers import SentenceTransformer
    import pickle
    
    print("-" * 60)
    print("Qdrant 代码索引")
    print("-" * 60)
    
    # 加载模型
    print("\n[1/3] 加载模型...")
    model = get_model()
    dim = model.get_sentence_embedding_dimension()
    print(f"      维度: {dim}")
    
    # 收集文件
    print("\n[2/3] 扫描文件...")
    src_dir = PROJECT_ROOT / "src"
    memory_dir = PROJECT_ROOT / ".agents" / "memory"
    
    files = list(src_dir.rglob("*.py"))
    files.extend(src_dir.rglob("*.js"))
    files.extend(src_dir.rglob("*.ts"))
    files.extend(src_dir.rglob("*.vue"))
    files.extend(src_dir.rglob("*.md"))
    
    # 添加 memory 目录下的配置文档
    if memory_dir.exists():
        files.extend(memory_dir.rglob("*.md"))
    
    files = [f for f in files if "__pycache__" not in str(f) and ".venv" not in str(f)]
    print(f"      找到 {len(files)} 个文件")
    
    # 索引
    print("\n[3/3] 编码并保存...")
    vectors_data = []
    point_id = 0
    
    for i, file_path in enumerate(files, 1):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            if len(content.strip()) < 50:
                continue
            
            # 分段
            chunks = []
            for j in range(0, min(len(content), 3000), 600):
                chunk = content[j:j+600].strip()
                if len(chunk) > 50:
                    chunks.append(chunk)
            
            for chunk in chunks[:3]:  # 每文件最多3段
                vec = model.encode(chunk[:800]).tolist()
                vectors_data.append({
                    "id": point_id,
                    "vector": vec,  # 直接保存向量
                    "payload": {
                        "text": chunk[:800],
                        "file": str(file_path.relative_to(PROJECT_ROOT)),
                        "ext": file_path.suffix
                    }
                })
                point_id += 1
                
            if i % 20 == 0:
                print(f"      进度: {i}/{len(files)} files, {point_id} vectors")
                
        except Exception as e:
            pass
    
    # 保存到文件
    data = {
        "collection": "ai-ken",
        "dim": dim,
        "vectors": vectors_data
    }
    
    with open(INDEX_FILE, 'wb') as f:
        pickle.dump(data, f)
    
    print(f"\n[OK] 完成! 共 {len(vectors_data)} 个向量")
    print(f"      保存到: {INDEX_FILE}")
    
    return data


def load_vectors():
    """加载向量数据"""
    import pickle
    
    if not INDEX_FILE.exists():
        return None
    
    with open(INDEX_FILE, 'rb') as f:
        return pickle.load(f)


def search(query: str, top_k: int = 5):
    """语义搜索"""
    from qdrant_client import QdrantClient
    from qdrant_client.models import VectorParams, Distance, PointStruct
    
    # 加载数据
    data = load_vectors()
    if not data:
        print("[WARN] 没有索引数据，请先运行: python qdrant_search.py index")
        return []
    
    print(f"\n[Search] \"{query}\"")
    print("-" * 60)
    
    # 加载模型
    model = get_model()
    
    # 创建内存 Qdrant
    client = QdrantClient(":memory:")
    client.create_collection(
        collection_name="ai-ken",
        vectors_config=VectorParams(size=data["dim"], distance=Distance.COSINE)
    )
    
    # 导入向量
    points = [PointStruct(id=v["id"], vector=v["vector"], payload=v["payload"]) 
              for v in data["vectors"]]
    client.upsert("ai-ken", points)
    
    # 搜索
    vec = model.encode(query).tolist()
    res = client.query_points(
        collection_name="ai-ken",
        query=vec,
        limit=top_k,
        with_payload=True
    )
    results = res.points
    
    if not results:
        print("未找到结果")
        return []
    
    for i, hit in enumerate(results, 1):
        bar = "#" * int(hit.score * 15) + "-" * (15 - int(hit.score * 15))
        print(f"\n{i}. [{bar}] {hit.score:.3f}")
        print(f"   文件: {hit.payload.get('file', 'N/A')}")
        text = hit.payload.get('text', '')[:200].replace('\n', ' ')
        print(f"   内容: {text}...")
    
    return results


def interactive():
    """交互模式"""
    print("-" * 60)
    print("Qdrant 语义搜索 - 交互模式")
    print("-" * 60)
    print("命令: /quit 退出, /index 重新索引\n")
    
    has_index = INDEX_FILE.exists()
    if not has_index:
        print("[提示] 尚未建立索引，输入 /index 创建")
    
    while True:
        try:
            query = input("\n> ").strip()
            
            if not query:
                continue
            
            if query in ['/quit', '/q', 'exit']:
                break
            
            if query == '/index':
                index_code()
                has_index = True
                continue
            
            if not has_index:
                print("[错误] 尚未建立索引，请先输入 /index")
                continue
            
            search(query)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[错误] {e}")
    
    print("\n再见!")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    cmd = sys.argv[1]
    
    if cmd == "index":
        index_code()
    elif cmd == "search":
        query = sys.argv[2] if len(sys.argv) > 2 else input("输入搜索词: ")
        search(query)
    elif cmd == "interactive":
        interactive()
    else:
        print(f"未知命令: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
