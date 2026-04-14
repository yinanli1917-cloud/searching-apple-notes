#!/usr/bin/env python3
"""
Apple Notes MCP 服务器 (云端部署版本)
支持 API Key 认证和远程访问

环境变量配置:
    API_KEY: API 密钥（必需，用于 Poke AI 认证）
    PORT: 服务器端口（默认 8000）
    HOST: 绑定地址（默认 0.0.0.0，接受所有连接）
"""

import sys
import os
import sqlite3
import subprocess
from pathlib import Path
from typing import List, Optional

import chromadb
from chromadb.api.types import EmbeddingFunction, Documents
from fastmcp import FastMCP

# 导入 BGE-M3 模型
from FlagEmbedding import FlagModel

# ============ 配置 ============
# 从环境变量读取配置
API_KEY = os.environ.get("API_KEY")  # 必需
PORT = int(os.environ.get("PORT", "8000"))
HOST = os.environ.get("HOST", "0.0.0.0")  # 0.0.0.0 接受所有连接

# 云端路径配置
BASE_DIR = Path("/app") if Path("/app").exists() else Path.home() / "Documents/apple-notes-mcp"
NOTES_DB = BASE_DIR / "notes.db"
CHROMA_DB = BASE_DIR / "chroma_db"
INDEXER_SCRIPT = BASE_DIR / "scripts/indexer.py"

# 验证 API Key
if not API_KEY:
    print("❌ 错误: 未设置 API_KEY 环境变量", file=sys.stderr)
    print("请在 Railway 中设置环境变量: API_KEY=your-secret-key", file=sys.stderr)
    sys.exit(1)

print(f"✅ API Key 已配置: {API_KEY[:8]}...", file=sys.stderr)

# ============ BGE-M3 嵌入函数 ============
class BGEEmbeddingFunction(EmbeddingFunction):
    """
    BGE-M3 嵌入函数
    使用 BAAI/bge-m3 模型生成 1024 维向量
    """
    def __init__(self):
        print("🚀 加载 BGE-M3 模型...", file=sys.stderr)
        self.model = FlagModel(
            'BAAI/bge-m3',
            query_instruction_for_retrieval="为这个句子生成表示以用于检索相关文章：",
            use_fp16=True
        )
        print("✅ BGE-M3 模型加载完成", file=sys.stderr)

    def __call__(self, input: Documents) -> List[List[float]]:
        embeddings = self.model.encode(input)
        return embeddings.tolist()

# ============ 初始化 MCP ============
mcp = FastMCP(name="apple-notes-search")

# 延迟初始化 ChromaDB
_chroma_client = None
_collection = None
_bge_ef = None

def get_collection():
    """获取 ChromaDB collection（懒加载）"""
    global _chroma_client, _collection, _bge_ef
    if _collection is None:
        if not CHROMA_DB.exists():
            raise FileNotFoundError(
                f"向量数据库不存在: {CHROMA_DB}\n"
                "请先运行索引脚本: python3 scripts/build_index_cloud.py"
            )

        _chroma_client = chromadb.PersistentClient(path=str(CHROMA_DB))

        if _bge_ef is None:
            _bge_ef = BGEEmbeddingFunction()

        _collection = _chroma_client.get_or_create_collection(
            "apple_notes",
            embedding_function=_bge_ef
        )
        print(f"✅ 向量数据库已加载，笔记数: {_collection.count()}", file=sys.stderr)

    return _collection

# ============ API Key 验证中间件 ============
# 注意: FastMCP 2.x 可能没有内置的中间件支持
# 我们需要在工具层面进行验证

def verify_api_key(provided_key: Optional[str]) -> bool:
    """验证 API Key"""
    if not provided_key:
        return False
    return provided_key == API_KEY

# ============ 工具定义 ============

@mcp.tool()
async def search_notes(query: str, api_key: str, limit: int = 5) -> str:
    """
    在 Apple Notes 中进行语义搜索

    Args:
        query: 搜索关键词或问题（支持模糊匹配和语义理解）
        api_key: API 密钥（必需）
        limit: 返回结果数量（默认5条，最多20条）

    Returns:
        匹配的备忘录列表，包含标题、内容和更新时间
    """
    # 验证 API Key
    if not verify_api_key(api_key):
        return "❌ 认证失败: API Key 无效"

    try:
        limit = min(limit, 20)
        collection = get_collection()
        results = collection.query(
            query_texts=[query],
            n_results=limit
        )

        if not results['documents'][0]:
            return "❌ 没有找到相关备忘录"

        # 格式化输出
        output = [f"# 搜索结果：{query}\n"]
        output.append(f"找到 {len(results['documents'][0])} 个相关结果\n")

        for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
            title = metadata.get('title', '(无标题)')
            updated = metadata.get('updated', '')

            output.append(f"## {i+1}. {title}")
            output.append(f"**更新时间**: {updated[:10] if updated else '未知'}")
            output.append(f"\n{doc[:400]}...")
            output.append("\n---\n")

        return "\n".join(output)

    except Exception as e:
        return f"❌ 搜索失败: {str(e)}"

@mcp.tool()
async def refine_search(
    query: str,
    api_key: str,
    date_after: str = "",
    date_before: str = "",
    limit: int = 5
) -> str:
    """
    使用过滤条件进行更精确的搜索

    Args:
        query: 搜索查询
        api_key: API 密钥（必需）
        date_after: 只搜索此日期之后的笔记（格式：YYYY-MM-DD）
        date_before: 只搜索此日期之前的笔记（格式：YYYY-MM-DD）
        limit: 返回结果数量

    Returns:
        筛选后的备忘录列表
    """
    if not verify_api_key(api_key):
        return "❌ 认证失败: API Key 无效"

    try:
        limit = min(limit, 20)

        where = {}
        if date_after:
            where["updated"] = {"$gte": date_after}
        if date_before:
            if "updated" in where:
                where["updated"]["$lte"] = date_before
            else:
                where["updated"] = {"$lte": date_before}

        collection = get_collection()
        results = collection.query(
            query_texts=[query],
            n_results=limit,
            where=where if where else None
        )

        if not results['documents'][0]:
            return "❌ 没有找到符合条件的备忘录"

        output = [f"# 精细搜索结果：{query}\n"]
        if date_after or date_before:
            output.append(f"**时间范围**: {date_after or '不限'} ~ {date_before or '不限'}\n")
        output.append(f"找到 {len(results['documents'][0])} 个结果\n")

        for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
            title = metadata.get('title', '(无标题)')
            updated = metadata.get('updated', '')

            output.append(f"## {i+1}. {title}")
            output.append(f"**更新时间**: {updated[:10] if updated else '未知'}")
            output.append(f"\n{doc[:400]}...")
            output.append("\n---\n")

        return "\n".join(output)

    except Exception as e:
        return f"❌ 搜索失败: {str(e)}"

@mcp.tool()
async def get_stats(api_key: str) -> str:
    """
    查看备忘录数量和索引状态

    Args:
        api_key: API 密钥（必需）

    Returns:
        统计信息，包括总笔记数、已索引数、覆盖率等
    """
    if not verify_api_key(api_key):
        return "❌ 认证失败: API Key 无效"

    try:
        if not NOTES_DB.exists():
            return "❌ 备忘录数据库不存在"

        conn = sqlite3.connect(str(NOTES_DB))
        cursor = conn.execute("SELECT COUNT(*) FROM notes")
        total_notes = cursor.fetchone()[0]
        conn.close()

        collection = get_collection()
        indexed_count = collection.count()

        coverage = (indexed_count / total_notes * 100) if total_notes > 0 else 0

        return f"""# 备忘录统计

📊 **总体情况**
- 总笔记数: {total_notes}
- 已索引数: {indexed_count}
- 索引覆盖率: {coverage:.1f}%

💡 **提示**
这是你的私有 Apple Notes 语义搜索实例。
"""

    except Exception as e:
        return f"❌ 获取统计失败: {str(e)}"

# ============ 健康检查端点 ============
@mcp.tool()
async def health_check() -> str:
    """
    健康检查（无需 API Key）

    Returns:
        服务器状态信息
    """
    try:
        chroma_status = "✅ 可用" if CHROMA_DB.exists() else "❌ 未初始化"
        notes_status = "✅ 可用" if NOTES_DB.exists() else "❌ 不存在"

        return f"""# 服务器状态

🟢 服务器运行中

**数据库状态**:
- 向量数据库: {chroma_status}
- 笔记数据库: {notes_status}

**配置**:
- API Key: 已配置 ✅
- 模型: BGE-M3 (1024维)
"""
    except Exception as e:
        return f"❌ 健康检查失败: {str(e)}"

# ============ 启动服务器 ============
if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Apple Notes MCP 服务器 (云端版本)")
    print("=" * 60)
    print(f"📂 基础目录: {BASE_DIR}")
    print(f"📂 笔记数据库: {NOTES_DB}")
    print(f"🗂️  向量数据库: {CHROMA_DB}")
    print(f"🔐 API 认证: 已启用")
    print()
    print(f"🌐 服务器地址: http://{HOST}:{PORT}/sse")
    print(f"   (HTTPS 由 Railway 自动提供)")
    print()
    print("✅ 可用工具:")
    print("  - search_notes: 语义搜索备忘录 (需要 api_key)")
    print("  - refine_search: 精细化搜索 (需要 api_key)")
    print("  - get_stats: 查看统计信息 (需要 api_key)")
    print("  - health_check: 健康检查 (无需 api_key)")
    print()
    print("⏳ 等待客户端连接...")
    print("=" * 60)
    print()

    # 运行 MCP 服务器
    mcp.run(transport="sse", host=HOST, port=PORT)
