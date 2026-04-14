#!/usr/bin/env python3.12
"""
Apple Notes MCP 服务器 (HTTP/SSE 版本)
为 Poke AI 等远程 MCP 客户端提供 HTTP 接口

使用方法:
    python3 server_http.py

服务器将在 http://localhost:8000/sse 提供服务
"""

import sys
import os
import sqlite3
import subprocess
from pathlib import Path
from typing import List

import chromadb
from chromadb.api.types import EmbeddingFunction, Documents
from fastmcp import FastMCP

# 导入 BGE-M3 模型
from FlagEmbedding import FlagModel

# ============ 配置 ============
NOTES_DB = Path.home() / "notes.db"
CHROMA_DB = Path.home() / "Documents/apple-notes-mcp/chroma_db"
INDEXER_SCRIPT = Path.home() / "Documents/apple-notes-mcp/scripts/indexer.py"

# HTTP 服务器配置
HOST = "0.0.0.0"    # 监听所有网络接口（局域网可访问）
PORT = 8000         # 端口号

# ============ BGE-M3 嵌入函数 ============
class BGEEmbeddingFunction(EmbeddingFunction):
    """
    BGE-M3 嵌入函数
    使用 BAAI/bge-m3 模型生成 1024 维向量
    - 模型: BAAI/bge-m3
    - 维度: 1024
    - 特点: 优化中英文混合搜索，支持 100+ 语言
    """
    def __init__(self):
        print("🚀 加载 BGE-M3 模型...", file=sys.stderr)
        self.model = FlagModel(
            'BAAI/bge-m3',
            query_instruction_for_retrieval="为这个句子生成表示以用于检索相关文章：",
            use_fp16=True  # 使用半精度浮点数加速，M2 MAX 支持
        )
        print("✅ BGE-M3 模型加载完成", file=sys.stderr)

    def __call__(self, input: Documents) -> List[List[float]]:
        """
        将文本转换为向量
        Args:
            input: 文本列表
        Returns:
            向量列表（每个向量 1024 维）
        """
        embeddings = self.model.encode(input)
        return embeddings.tolist()

# ============ 初始化 MCP 和 ChromaDB ============
mcp = FastMCP(name="apple-notes-search")

# 延迟初始化 ChromaDB（在需要时才连接）
_chroma_client = None
_collection = None
_bge_ef = None

def get_collection():
    """获取 ChromaDB collection（懒加载）"""
    global _chroma_client, _collection, _bge_ef
    if _collection is None:
        _chroma_client = chromadb.PersistentClient(path=str(CHROMA_DB))

        # 初始化 BGE-M3 嵌入函数
        if _bge_ef is None:
            _bge_ef = BGEEmbeddingFunction()

        _collection = _chroma_client.get_or_create_collection(
            "apple_notes",
            embedding_function=_bge_ef
        )
    return _collection

# ============ 工具 1: 搜索备忘录 ============
@mcp.tool()
async def search_notes(query: str, limit: int = 5) -> str:
    """
    在 Apple Notes 中进行语义搜索

    Args:
        query: 搜索关键词或问题（支持模糊匹配和语义理解）
        limit: 返回结果数量（默认5条，最多20条）

    Returns:
        匹配的备忘录列表，包含标题、内容和更新时间
    """
    try:
        # 限制最大返回数量
        limit = min(limit, 20)

        collection = get_collection()
        results = collection.query(
            query_texts=[query],
            n_results=limit
        )

        if not results['documents'][0]:
            return "❌ 没有找到相关备忘录"

        # 格式化输出（Markdown格式）
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
        return f"❌ 搜索失败: {str(e)}\n\n请确保已经运行过索引脚本。"

# ============ 工具 2: 精细化搜索 ============
@mcp.tool()
async def refine_search(
    query: str,
    date_after: str = "",
    date_before: str = "",
    limit: int = 5
) -> str:
    """
    使用过滤条件进行更精确的搜索

    Args:
        query: 搜索查询
        date_after: 只搜索此日期之后的笔记（格式：YYYY-MM-DD）
        date_before: 只搜索此日期之前的笔记（格式：YYYY-MM-DD）
        limit: 返回结果数量

    Returns:
        筛选后的备忘录列表
    """
    try:
        limit = min(limit, 20)

        # 构建过滤条件
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

        # 格式化输出
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

# ============ 工具 3: 刷新索引 ============
@mcp.tool()
async def refresh_index() -> str:
    """
    手动触发备忘录导出和重新索引

    这个操作会：
    1. 重新导出 Apple Notes 到 SQLite
    2. 增量更新向量数据库（只索引新增/修改的笔记）

    Returns:
        操作结果和统计信息
    """
    try:
        output = ["# 刷新索引\n"]

        # 1. 导出备忘录（使用UTF-8修复版）
        output.append("## 步骤 1: 导出备忘录")
        result = subprocess.run(
            [
                "python3",
                str(Path.home() / "Documents/apple-notes-mcp/scripts/export_notes_fixed.py")
            ],
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode != 0:
            return f"❌ 导出失败:\n{result.stderr}"

        output.append("✅ 导出成功\n")

        # 2. 运行索引脚本
        output.append("## 步骤 2: 更新索引")
        result = subprocess.run(
            ["python3", str(INDEXER_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode != 0:
            return f"❌ 索引失败:\n{result.stderr}"

        # 提取关键信息
        stdout_lines = result.stdout.split('\n')
        for line in stdout_lines:
            if '发现' in line or '索引完成' in line or '无需更新' in line:
                output.append(f"- {line.strip()}")

        output.append("\n✅ **刷新完成！**")
        return "\n".join(output)

    except subprocess.TimeoutExpired:
        return "❌ 操作超时，请稍后重试"
    except Exception as e:
        return f"❌ 刷新失败: {str(e)}"

# ============ 工具 4: 获取统计信息 ============
@mcp.tool()
async def get_stats() -> str:
    """
    查看备忘录数量和索引状态

    Returns:
        统计信息，包括总笔记数、已索引数、覆盖率等
    """
    try:
        # 从 SQLite 获取总数
        if not NOTES_DB.exists():
            return "❌ 备忘录数据库不存在，请先运行刷新索引"

        conn = sqlite3.connect(str(NOTES_DB))
        cursor = conn.execute("SELECT COUNT(*) FROM notes")
        total_notes = cursor.fetchone()[0]
        conn.close()

        # 从 ChromaDB 获取索引数
        collection = get_collection()
        indexed_count = collection.count()

        # 计算覆盖率
        coverage = (indexed_count / total_notes * 100) if total_notes > 0 else 0

        return f"""# 备忘录统计

📊 **总体情况**
- 总笔记数: {total_notes}
- 已索引数: {indexed_count}
- 索引覆盖率: {coverage:.1f}%

📂 **文件位置**
- SQLite 数据库: `{NOTES_DB}`
- 向量数据库: `{CHROMA_DB}`

💡 **提示**
如果覆盖率低于 100%，请运行 `refresh_index` 更新索引。
"""

    except Exception as e:
        return f"❌ 获取统计失败: {str(e)}"

# ============ 启动服务器 ============
if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Apple Notes MCP 服务器启动中 (HTTP/SSE 模式)...")
    print("=" * 60)
    print(f"📂 备忘录数据库: {NOTES_DB}")
    print(f"🗂️  向量数据库: {CHROMA_DB}")
    print(f"🔧 索引脚本: {INDEXER_SCRIPT}")
    print()
    print(f"🌐 服务器地址: http://{HOST}:{PORT}/sse")
    print(f"   (用于 Poke AI 等远程 MCP 客户端)")
    print()
    print("✅ 可用工具:")
    print("  - search_notes: 语义搜索备忘录")
    print("  - refine_search: 精细化搜索（带日期过滤）")
    print("  - refresh_index: 刷新索引")
    print("  - get_stats: 查看统计信息")
    print()
    print("⏳ 等待客户端连接...")
    print("=" * 60)
    print()

    # 运行 MCP 服务器（SSE 传输，用于远程客户端）
    mcp.run(transport="sse", host=HOST, port=PORT)
