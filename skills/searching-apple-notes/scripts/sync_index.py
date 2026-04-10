#!/usr/bin/env python3.12
"""
One-shot Apple Notes sync — Skill helper script.

[INPUT]:  Notes.app, NoteStore.sqlite, the existing scripts at <repo>/scripts/
[OUTPUT]: Updated ~/notes.db (SQLite) and <repo>/chroma_db/ (vector index)
[POS]:    Convenience wrapper that runs the full sync pipeline in one command

Pipeline:
  1. Full export from Notes.app via <repo>/scripts/export_notes_fixed.py
     (idempotent — uses INSERT OR REPLACE)
  2. Bridge native Apple Notes hashtags from NoteStore.sqlite into our SQLite
     (the clever bit: native tags live in ZICCLOUDSYNCINGOBJECT keyed by Z_PK)
  3. Incremental vector index update via <repo>/scripts/indexer.py
     (re-embeds only notes whose `updated` timestamp is newer than .last_sync)
"""

import subprocess
import sys
import sqlite3
import re
from pathlib import Path
from datetime import datetime

# ============ Path resolution ============
# This script lives at: <repo>/skills/searching-apple-notes/scripts/sync_index.py
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]  # scripts -> searching-apple-notes -> skills -> repo
EXPORT_SCRIPT = REPO_ROOT / "scripts/export_notes_fixed.py"
INDEXER_SCRIPT = REPO_ROOT / "scripts/indexer.py"

# Data files (these are user data, not repo data — they live in standard locations)
NOTES_DB = Path.home() / "notes.db"
NOTESTORE_DB = Path.home() / "Library/Group Containers/group.com.apple.notes/NoteStore.sqlite"


def get_db_count():
    """Count notes currently in our SQLite mirror."""
    if not NOTES_DB.exists():
        return 0
    conn = sqlite3.connect(NOTES_DB)
    count = conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
    conn.close()
    return count


def sync_tags_from_notestore():
    """
    Bridge native Apple Notes hashtags into our SQLite mirror.

    Apple stores native #hashtag attachments in NoteStore.sqlite, in the table
    ZICCLOUDSYNCINGOBJECT, where ZTYPEUTI1 = 'com.apple.notes.inlinetextattachment.hashtag'.
    Each tag row links to its parent note via ZNOTE1 → Z_PK. Our note IDs end
    in /pN where N is the same Z_PK, so we can join the two databases by
    parsing the trailing /pN out of our IDs.
    """
    if not NOTESTORE_DB.exists():
        print("  ⚠️  NoteStore.sqlite not accessible, skipping tag bridge")
        return 0

    try:
        ns = sqlite3.connect(str(NOTESTORE_DB))
        our = sqlite3.connect(str(NOTES_DB))
    except Exception as e:
        print(f"  ⚠️  Failed to open databases: {e}")
        return 0

    # Build Z_PK -> [tag1, tag2, ...] map from NoteStore
    tag_map = {}
    for pk, tag in ns.execute("""
        SELECT ZNOTE1, ZALTTEXT
        FROM ZICCLOUDSYNCINGOBJECT
        WHERE ZTYPEUTI1 = 'com.apple.notes.inlinetextattachment.hashtag'
    """).fetchall():
        tag_map.setdefault(pk, []).append(tag.lstrip('#'))

    # Write tags into our SQLite
    updated = 0
    for (our_id,) in our.execute('SELECT id FROM notes').fetchall():
        m = re.search(r'/p(\d+)$', our_id)
        if not m:
            continue
        pk = int(m.group(1))
        tags_str = ','.join(sorted(tag_map[pk])) if pk in tag_map else ''
        our.execute('UPDATE notes SET tags = ? WHERE id = ?', (tags_str, our_id))
        if pk in tag_map:
            updated += 1

    our.commit()
    ns.close()
    our.close()
    return updated


def get_chromadb_count():
    """Count vectors currently in the index."""
    try:
        import chromadb
        db_path = REPO_ROOT / "chroma_db"
        client = chromadb.PersistentClient(path=str(db_path))
        collection = client.get_collection("apple_notes")
        return collection.count()
    except Exception:
        return 0


def run_step(name, script):
    """Run a child script via python3.12, fail loudly on non-zero exit."""
    icon = "📤" if "export" in str(script) else "🔄"
    print(f"\n{icon} {name}...")
    result = subprocess.run(
        ["python3.12", str(script)],
        cwd=str(REPO_ROOT / "scripts")
    )
    if result.returncode != 0:
        print(f"❌ {name} failed")
        return False
    return True


def main():
    print("=" * 50)
    print("📝 Apple Notes Sync")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    # Snapshot before
    db_before = get_db_count()
    chroma_before = get_chromadb_count()
    print(f"\n📊 Before: SQLite={db_before}, ChromaDB={chroma_before}")

    # Step 1: full export from Notes.app (idempotent)
    if not run_step("Export notes to SQLite", EXPORT_SCRIPT):
        return 1

    # Step 2: bridge native hashtags from NoteStore.sqlite
    print("\n🏷️  Syncing native Apple Notes hashtags...")
    tag_count = sync_tags_from_notestore()
    print(f"   {tag_count} notes have tags")

    # Step 3: incremental vector index update
    if not run_step("Update vector index", INDEXER_SCRIPT):
        return 1

    # Snapshot after
    db_after = get_db_count()
    chroma_after = get_chromadb_count()

    print(f"\n✅ Sync complete!")
    print(f"   SQLite:   {db_before} → {db_after} ({db_after - db_before:+d})")
    print(f"   ChromaDB: {chroma_before} → {chroma_after} ({chroma_after - chroma_before:+d})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
