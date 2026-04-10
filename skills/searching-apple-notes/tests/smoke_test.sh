#!/usr/bin/env bash
# ============================================================================
# Smoke test for the searching-apple-notes skill.
#
# Verifies that the four helper scripts can run end-to-end against a real
# index. Run this after a fresh clone, after upgrading dependencies, or
# after editing any of the helper scripts.
#
# What it checks:
#   1. python3.12 is on PATH (required for BGE-M3 + ChromaDB)
#   2. The skill scripts resolve their paths correctly from any working dir
#   3. vector_search.py --stats returns a valid JSON object with a non-zero
#      indexed_notes count
#   4. vector_search.py "smoke test query" returns a JSON array (may be empty
#      if no notes match — that's still a pass)
#   5. The parent repo's chroma_db exists at the location vector_search.py
#      expects it
#
# What it does NOT check:
#   - create_note.py (would actually create a note in your Apple Notes — too
#     destructive for a smoke test)
#   - sync_index.py (takes too long to be a smoke test; run manually)
#   - get_note.py (depends on Notes.app state and is index-sensitive)
#
# Usage:
#   bash skills/searching-apple-notes/tests/smoke_test.sh
#
# Exit code 0 = pass, non-zero = fail.
# ============================================================================

set -e
set -o pipefail

# ----- Resolve paths from this script's own location -----
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$SKILL_DIR/../.." && pwd)"

echo "==============================================="
echo "  searching-apple-notes — smoke test"
echo "==============================================="
echo "Skill dir: $SKILL_DIR"
echo "Repo root: $REPO_ROOT"
echo ""

# ----- 1. Check python3.12 is available -----
echo "[1/4] Checking python3.12 is on PATH..."
if ! command -v python3.12 >/dev/null 2>&1; then
    echo "  FAIL: python3.12 not found. Install Python 3.12 first."
    exit 1
fi
echo "  OK ($(python3.12 --version))"
echo ""

# ----- 2. Check ChromaDB exists at the expected repo-relative location -----
echo "[2/4] Checking ChromaDB exists at <repo>/chroma_db..."
if [ ! -d "$REPO_ROOT/chroma_db" ]; then
    echo "  FAIL: $REPO_ROOT/chroma_db does not exist."
    echo "  Run the parent repo setup first:"
    echo "    python3.12 $REPO_ROOT/scripts/export_notes_fixed.py"
    echo "    python3.12 $REPO_ROOT/scripts/indexer.py"
    exit 1
fi
echo "  OK ($(du -sh "$REPO_ROOT/chroma_db" | cut -f1) on disk)"
echo ""

# ----- 3. vector_search.py --stats returns valid JSON -----
echo "[3/4] Running vector_search.py --stats..."
STATS_JSON="$(python3.12 "$SKILL_DIR/scripts/vector_search.py" --stats 2>/dev/null)"
if [ -z "$STATS_JSON" ]; then
    echo "  FAIL: --stats returned empty output."
    exit 1
fi
INDEXED_COUNT="$(echo "$STATS_JSON" | python3.12 -c 'import json, sys; print(json.load(sys.stdin).get("indexed_notes", 0))' 2>/dev/null || echo "0")"
if [ "$INDEXED_COUNT" -lt 1 ]; then
    echo "  FAIL: index has 0 notes. Run sync_index.py first."
    echo "  Stats output: $STATS_JSON"
    exit 1
fi
echo "  OK ($INDEXED_COUNT notes indexed)"
echo ""

# ----- 4. vector_search.py with a real query returns valid JSON -----
echo "[4/4] Running vector_search.py 'smoke test query' -n 1..."
SEARCH_JSON="$(python3.12 "$SKILL_DIR/scripts/vector_search.py" "smoke test query" -n 1 2>/dev/null)"
if [ -z "$SEARCH_JSON" ]; then
    echo "  FAIL: search returned empty output (expected at least '[]')."
    exit 1
fi
# Validate it parses as a JSON array
echo "$SEARCH_JSON" | python3.12 -c 'import json, sys; d = json.load(sys.stdin); assert isinstance(d, list), "not a list"' 2>/dev/null || {
    echo "  FAIL: search output is not a valid JSON array."
    echo "  Output: $SEARCH_JSON"
    exit 1
}
echo "  OK (returned valid JSON array)"
echo ""

echo "==============================================="
echo "  PASS — smoke test complete"
echo "==============================================="
