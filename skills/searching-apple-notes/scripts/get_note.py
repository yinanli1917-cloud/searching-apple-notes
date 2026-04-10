#!/usr/bin/env python3
"""
Get full note content by index — Skill helper script.

[INPUT]:  Apple Notes via AppleScript
[OUTPUT]: JSON with full plain-text content of the requested note(s)
[POS]:    Companion to vector_search.py — used when the snippet isn't enough

Usage:
    python3 get_note.py --index 5
    python3 get_note.py --indices 1,5,12
"""

import subprocess
import json
import re
import sys
import argparse
from typing import Optional


def html_to_text(html: str) -> str:
    """Convert Apple Notes HTML body to clean plain text."""
    if not html:
        return ""
    text = re.sub(r'<br\s*/?>', '\n', html, flags=re.IGNORECASE)
    text = re.sub(r'</p>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</div>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</h[1-6]>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</li>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    return text.strip()


def run_applescript(script: str, timeout: int = 30) -> Optional[str]:
    """Execute AppleScript via osascript."""
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        if result.returncode != 0:
            print(f"Error: {result.stderr}", file=sys.stderr)
            return None
        return result.stdout.strip()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return None


def get_note_by_index(index: int) -> Optional[dict]:
    """Fetch a note by its 1-based index in Notes.app."""
    script = f'''
tell application "Notes"
    set theNote to note {index}
    set noteTitle to name of theNote
    set noteBody to body of theNote
    return noteTitle & "<<<SEP>>>" & noteBody
end tell
'''
    result = run_applescript(script)
    if not result:
        return None

    parts = result.split("<<<SEP>>>", 1)
    if len(parts) < 2:
        return None

    return {
        "index": index,
        "title": parts[0],
        "content": html_to_text(parts[1])
    }


def get_notes_by_indices(indices: list) -> list:
    """Fetch multiple notes by index."""
    notes = []
    for idx in indices:
        note = get_note_by_index(idx)
        if note:
            notes.append(note)
    return notes


def main():
    parser = argparse.ArgumentParser(description='Get full Apple Notes content by index')
    parser.add_argument('--index', '-i', type=int, help='Note index (1-based)')
    parser.add_argument('--indices', '-I', type=str, help='Comma-separated indices')
    args = parser.parse_args()

    if args.indices:
        indices = [int(i.strip()) for i in args.indices.split(',')]
        notes = get_notes_by_indices(indices)
        print(json.dumps(notes, ensure_ascii=False, indent=2))
    elif args.index:
        note = get_note_by_index(args.index)
        if note:
            print(json.dumps(note, ensure_ascii=False, indent=2))
        else:
            print("Note not found", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
