#!/usr/bin/env python3.12
"""
Vector Search for Apple Notes — Skill helper script.

[INPUT]:  Reads from <repo>/chroma_db/ (BGE-M3 vector index built by ../../../scripts/indexer.py)
[OUTPUT]: JSON array of search results to stdout
[POS]:    Core search engine for the searching-apple-notes Claude skill

This script is invoked by Claude Code when the skill activates. It does
semantic vector search over the user's Apple Notes archive, with optional
filtering by tag, folder, and date range.

Usage:
    python3.12 vector_search.py "query"
    python3.12 vector_search.py "query" -n 20
    python3.12 vector_search.py "query" --tag MyTag
    python3.12 vector_search.py "query" --folder MyFolder
    python3.12 vector_search.py "query" --after 2025-01-01
    python3.12 vector_search.py --stats
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Optional

# ============ Path resolution ============
# This script lives at: <repo>/skills/searching-apple-notes/scripts/vector_search.py
# So the repo root is 4 levels up from __file__.
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]  # scripts -> searching-apple-notes -> skills -> repo
CHROMA_DB = REPO_ROOT / "chroma_db"
COLLECTION_NAME = "apple_notes"

# ============ Lazy-loaded globals ============
_model = None
_client = None
_collection = None


def get_model():
    """Lazy-load the BGE-M3 model. ~10s cold start, then cached."""
    global _model
    if _model is None:
        print("Loading BGE-M3 model...", file=sys.stderr)
        from FlagEmbedding import FlagModel
        _model = FlagModel(
            'BAAI/bge-m3',
            query_instruction_for_retrieval="为这个句子生成表示以用于检索相关文章：",
            use_fp16=True
        )
        print("Model loaded.", file=sys.stderr)
    return _model


def get_collection():
    """Lazy-load the ChromaDB collection."""
    global _client, _collection
    if _collection is None:
        import chromadb
        from chromadb.api.types import EmbeddingFunction, Documents

        class BGEEmbeddingFunction(EmbeddingFunction):
            def __call__(self, input: Documents) -> List[List[float]]:
                model = get_model()
                return model.encode(input).tolist()

        _client = chromadb.PersistentClient(path=str(CHROMA_DB))
        _collection = _client.get_collection(
            COLLECTION_NAME,
            embedding_function=BGEEmbeddingFunction()
        )
    return _collection


def search(
    query: str,
    limit: int = 10,
    date_after: Optional[str] = None,
    date_before: Optional[str] = None,
    tag: Optional[str] = None,
    folder: Optional[str] = None,
) -> List[Dict]:
    """Semantic vector search with tag/folder/date filtering."""
    if not CHROMA_DB.exists():
        return [{
            "error": f"ChromaDB not found at {CHROMA_DB}. "
                     f"Run the setup steps in the repo README first."
        }]

    collection = get_collection()

    # Build server-side filter conditions (date and folder)
    conditions = []
    if date_after:
        conditions.append({"updated": {"$gte": date_after}})
    if date_before:
        conditions.append({"updated": {"$lte": date_before}})
    if folder:
        conditions.append({"folder": folder})

    where = None
    if len(conditions) == 1:
        where = conditions[0]
    elif len(conditions) > 1:
        where = {"$and": conditions}

    # Tag is filtered client-side because ChromaDB's $contains is unreliable
    # on comma-joined strings. Fetch extra results to leave room for filtering.
    fetch_limit = limit * 3 if tag else limit
    results = collection.query(
        query_texts=[query],
        n_results=fetch_limit,
        where=where
    )

    if not results['documents'][0]:
        return []

    output = []
    for doc, metadata, distance in zip(
        results['documents'][0],
        results['metadatas'][0],
        results['distances'][0] if 'distances' in results else [0] * len(results['documents'][0])
    ):
        # Client-side tag filter
        if tag and tag not in (metadata.get('tags') or '').split(','):
            continue
        output.append({
            "rank": len(output) + 1,
            "title": metadata.get('title', '(untitled)'),
            "score": round(1.0 - distance, 3),
            "snippet": doc[:500] if doc else "",
            "updated": metadata.get('updated', ''),
            "folder": metadata.get('folder', ''),
            "tags": metadata.get('tags', ''),
            "id": metadata.get('id', '')
        })
        if len(output) >= limit:
            break

    return output


def get_stats() -> Dict:
    """Index health snapshot."""
    if not CHROMA_DB.exists():
        return {"error": f"ChromaDB not found at {CHROMA_DB}"}

    collection = get_collection()
    return {
        "indexed_notes": collection.count(),
        "model": "BGE-M3",
        "dimensions": 1024,
        "chroma_db_path": str(CHROMA_DB)
    }


# ============ CLI ============
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Vector Semantic Search for Apple Notes')
    parser.add_argument('query', nargs='?', help='Search query')
    parser.add_argument('-n', '--limit', type=int, default=10, help='Number of results (default: 10)')
    parser.add_argument('--after', type=str, help='Only notes modified after this date (YYYY-MM-DD)')
    parser.add_argument('--before', type=str, help='Only notes modified before this date (YYYY-MM-DD)')
    parser.add_argument('--tag', type=str, help='Filter by Apple Notes hashtag (e.g. Ideas)')
    parser.add_argument('--folder', type=str, help='Filter by folder name')
    parser.add_argument('--stats', action='store_true', help='Show index statistics')

    args = parser.parse_args()

    if args.stats:
        print(json.dumps(get_stats(), ensure_ascii=False, indent=2))
    elif args.query:
        results = search(args.query, args.limit, args.after, args.before, args.tag, args.folder)
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        parser.print_help()
