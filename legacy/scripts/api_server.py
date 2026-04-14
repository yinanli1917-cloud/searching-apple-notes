#!/usr/bin/env python3.12
"""
Apple Notes 搜索 API 服务器
提供 REST API 供 Cloudflare Workers 调用
"""

import sys
import os
from pathlib import Path
from typing import List
from flask import Flask, request, jsonify
from flask_cors import CORS

import chromadb
from chromadb.api.types import EmbeddingFunction, Documents

# 导入 BGE-M3 模型
from FlagEmbedding import FlagModel

# ============ 配置 ============
NOTES_DB = Path.home() / "notes.db"
CHROMA_DB = Path.home() / "Documents/apple-notes-mcp/chroma_db"

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

# ============ 初始化 Flask 和 ChromaDB ============
app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 延迟初始化 ChromaDB
_chroma_client = None
_collection = None
_bge_ef = None

def get_collection():
    """获取 ChromaDB collection（懒加载）"""
    global _chroma_client, _collection, _bge_ef
    if _collection is None:
        print("📂 初始化 ChromaDB...", file=sys.stderr)
        _chroma_client = chromadb.PersistentClient(path=str(CHROMA_DB))

        if _bge_ef is None:
            _bge_ef = BGEEmbeddingFunction()

        _collection = _chroma_client.get_or_create_collection(
            "apple_notes",
            embedding_function=_bge_ef
        )
        print("✅ ChromaDB 初始化完成", file=sys.stderr)
    return _collection

# ============ API 端点 ============

@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({
        "status": "running",
        "service": "Apple Notes Search API",
        "version": "1.0.0"
    })

@app.route('/search', methods=['POST'])
def search():
    """
    搜索备忘录

    请求格式:
    {
        "query": "搜索关键词",
        "limit": 5
    }

    返回格式:
    {
        "results": [
            {
                "title": "标题",
                "content": "内容",
                "updated": "更新时间",
                "score": 0.95
            }
        ],
        "total": 5
    }
    """
    try:
        data = request.get_json()
        query = data.get('query', '')
        limit = min(data.get('limit', 5), 20)

        if not query:
            return jsonify({"error": "查询不能为空"}), 400

        collection = get_collection()
        results = collection.query(
            query_texts=[query],
            n_results=limit
        )

        if not results['documents'][0]:
            return jsonify({
                "results": [],
                "total": 0,
                "message": "没有找到相关备忘录"
            })

        # 格式化结果
        formatted_results = []
        for i, (doc, metadata, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0] if 'distances' in results else [0] * len(results['documents'][0])
        )):
            formatted_results.append({
                "title": metadata.get('title', '(无标题)'),
                "content": doc,
                "updated": metadata.get('updated', ''),
                "score": 1.0 - distance  # 转换距离为相似度分数
            })

        return jsonify({
            "results": formatted_results,
            "total": len(formatted_results),
            "query": query
        })

    except Exception as e:
        print(f"❌ 搜索失败: {str(e)}", file=sys.stderr)
        return jsonify({"error": f"搜索失败: {str(e)}"}), 500

@app.route('/stats', methods=['GET'])
def stats():
    """获取统计信息"""
    try:
        collection = get_collection()
        count = collection.count()

        return jsonify({
            "indexed_notes": count,
            "model": "BGE-M3",
            "dimensions": 1024,
            "status": "ready"
        })
    except Exception as e:
        return jsonify({"error": f"获取统计失败: {str(e)}"}), 500

# ============ 启动服务器 ============
if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Apple Notes 搜索 API 服务器")
    print("=" * 60)
    print(f"📍 监听地址: http://0.0.0.0:8001")
    print(f"📂 ChromaDB: {CHROMA_DB}")
    print("=" * 60)

    # 监听所有网络接口，端口 8001（避免与 HTTP MCP 服务器冲突）
    app.run(host='0.0.0.0', port=8001, debug=False)
