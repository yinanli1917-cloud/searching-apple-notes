#!/usr/bin/env python3
"""
云端索引构建脚本

用于在 Railway 部署后首次构建向量索引。
需要先上传 notes.db 到 Railway。

使用方法:
    python3 scripts/build_index_cloud.py
"""

import sys
import sqlite3
from pathlib import Path
from typing import List

import chromadb
from chromadb.api.types import EmbeddingFunction, Documents
from FlagEmbedding import FlagModel

# ============ 配置 ============
# 云端路径配置
BASE_DIR = Path("/app") if Path("/app").exists() else Path.home() / "Documents/apple-notes-mcp"
NOTES_DB = BASE_DIR / "notes.db"
CHROMA_DB = BASE_DIR / "chroma_db"

print("=" * 60)
print("🚀 云端索引构建")
print("=" * 60)
print(f"📂 基础目录: {BASE_DIR}")
print(f"📂 笔记数据库: {NOTES_DB}")
print(f"🗂️  向量数据库: {CHROMA_DB}")
print()

# ============ BGE-M3 嵌入函数 ============
class BGEEmbeddingFunction(EmbeddingFunction):
    """BGE-M3 嵌入函数"""
    def __init__(self):
        print("🚀 加载 BGE-M3 模型...")
        self.model = FlagModel(
            'BAAI/bge-m3',
            query_instruction_for_retrieval="为这个句子生成表示以用于检索相关文章：",
            use_fp16=True
        )
        print("✅ BGE-M3 模型加载完成")

    def __call__(self, input: Documents) -> List[List[float]]:
        embeddings = self.model.encode(input)
        return embeddings.tolist()

# ============ 构建索引 ============
def build_index():
    """从 notes.db 构建向量索引"""

    # 检查 notes.db
    if not NOTES_DB.exists():
        print(f"❌ 错误: {NOTES_DB} 不存在")
        print("\n请先上传 notes.db 到 Railway:")
        print("1. 在本地运行: python3 scripts/export_notes_fixed.py")
        print("2. 将 ~/notes.db 上传到 Railway 的 /app/ 目录")
        sys.exit(1)

    # 读取笔记
    print("\n📖 读取笔记数据...")
    conn = sqlite3.connect(str(NOTES_DB))
    cursor = conn.execute("SELECT id, title, body, updated FROM notes")
    notes = cursor.fetchall()
    conn.close()

    print(f"✅ 读取到 {len(notes)} 条笔记")

    if len(notes) == 0:
        print("❌ 错误: notes.db 中没有数据")
        sys.exit(1)

    # 初始化 ChromaDB
    print("\n🗂️  初始化向量数据库...")
    CHROMA_DB.parent.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(CHROMA_DB))
    bge_ef = BGEEmbeddingFunction()

    # 创建或获取 collection
    collection = client.get_or_create_collection(
        name="apple_notes",
        embedding_function=bge_ef,
        metadata={"description": "Apple Notes 语义搜索 (BGE-M3, 1024维)"}
    )

    # 清空现有数据（如果有）
    existing_count = collection.count()
    if existing_count > 0:
        print(f"⚠️  检测到现有索引 ({existing_count} 条)，将清空后重建")
        collection.delete(where={})  # 清空

    # 批量索引
    print(f"\n🔨 开始构建索引（{len(notes)} 条笔记）...")
    batch_size = 50

    for i in range(0, len(notes), batch_size):
        batch = notes[i:i+batch_size]

        ids = [str(note[0]) for note in batch]
        documents = [note[2] or "" for note in batch]  # body
        metadatas = [
            {
                "title": note[1] or "(无标题)",
                "updated": note[3] or ""
            }
            for note in batch
        ]

        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

        progress = min(i + batch_size, len(notes))
        print(f"  进度: {progress}/{len(notes)} ({progress*100//len(notes)}%)")

    # 验证
    final_count = collection.count()
    print(f"\n✅ 索引构建完成！")
    print(f"📊 统计:")
    print(f"  - 笔记总数: {len(notes)}")
    print(f"  - 已索引: {final_count}")
    print(f"  - 覆盖率: {final_count*100//len(notes)}%")

    if final_count != len(notes):
        print(f"\n⚠️  警告: 索引数量与笔记数量不一致")

    return final_count

# ============ 主函数 ============
if __name__ == "__main__":
    try:
        count = build_index()
        print("\n" + "=" * 60)
        print(f"✅ 云端索引构建成功！已索引 {count} 条笔记")
        print("=" * 60)
        print("\n现在可以启动 MCP 服务器:")
        print("  python3 scripts/server_cloud.py")
        print()
    except Exception as e:
        print(f"\n❌ 索引构建失败: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
