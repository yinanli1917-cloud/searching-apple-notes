#!/usr/bin/env python3
"""
修复版的 Apple Notes 导出脚本
- UTF-8 编码（修复中文乱码）
- 遍历文件夹获取 folder 归属
- 从正文提取 #tag
"""

import subprocess
import sqlite3
import secrets
import re
from pathlib import Path

NOTES_DB = Path.home() / "notes.db"

# 遍历所有文件夹中的笔记，通过文件夹层面获取归属
EXTRACT_SCRIPT = """
tell application "Notes"
   repeat with f in every folder
      set folderName to name of f
      repeat with eachNote in every note of f
         set noteId to the id of eachNote
         set noteTitle to the name of eachNote
         set noteBody to the body of eachNote
         set noteCreatedDate to the creation date of eachNote
         set noteCreated to (noteCreatedDate as «class isot» as string)
         set noteUpdatedDate to the modification date of eachNote
         set noteUpdated to (noteUpdatedDate as «class isot» as string)
         log "{split}-id: " & noteId & "\\n"
         log "{split}-created: " & noteCreated & "\\n"
         log "{split}-updated: " & noteUpdated & "\\n"
         log "{split}-folder: " & folderName & "\\n"
         log "{split}-title: " & noteTitle & "\\n\\n"
         log noteBody & "\\n"
         log "{split}{split}" & "\\n"
      end repeat
   end repeat
end tell
""".strip()

# CSS 颜色码（3/6/8 位 hex）+ 常见 HTML 属性名，排除误判
HEX_COLOR = re.compile(r'^[0-9a-fA-F]{3,8}$')
HTML_NOISE = {"view", "page", "chapter", "overview", "rd", "ED", "offer",
              "page5", "section", "div", "span", "href", "src", "img"}
# 以 hex 色码开头的混合 tag（如 #E94335红）
HEX_PREFIX = re.compile(r'^[0-9a-fA-F]{3,}')


def extract_notes():
    """遍历文件夹，按 UTF-8 编码导出备忘录"""
    split = secrets.token_hex(8)

    process = subprocess.Popen(
        ["osascript", "-e", EXTRACT_SCRIPT.format(split=split)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    note = {}
    body = []

    for line in process.stdout:
        try:
            line = line.decode("utf-8").strip()
        except UnicodeDecodeError:
            try:
                line = line.decode("utf-16").strip()
            except:
                continue

        # 笔记分隔符
        if line == f"{split}{split}":
            if note.get("id"):
                note["body"] = "\\n".join(body).strip()
                yield note
            note = {}
            body = []
            continue

        # 解析元数据字段
        found_key = False
        for key in ("id", "title", "created", "updated", "folder"):
            prefix = f"{split}-{key}: "
            prefix_bare = f"{split}-{key}:"
            if line.startswith(prefix):
                note[key] = line[len(prefix):]
                found_key = True
                break
            elif line == prefix_bare:
                note[key] = ""
                found_key = True
                break

        if not found_key:
            body.append(line)


def extract_tags(body_html):
    """从 HTML body 中提取 Apple Notes #tag

    Apple Notes 的 tag 格式: #tagName[话题]#
    """
    plain = re.sub(r'<[^>]+>', ' ', body_html)
    # 优先匹配 Apple Notes 原生格式: #xxx[话题]#
    native_tags = set(re.findall(r'#([\w\u4e00-\u9fff]+)\[话题\]#', plain))
    if native_tags:
        return list(native_tags)
    # 回退：匹配普通 #tag（用户手写的）
    raw = set(re.findall(r'#([A-Za-z\u4e00-\u9fff][\w\u4e00-\u9fff]*)', plain))
    return [t for t in raw
            if len(t) > 1
            and not HEX_COLOR.match(t)
            and not HEX_PREFIX.match(t)
            and t not in HTML_NOISE]


def main():
    print("=" * 60)
    print("📤 导出 Apple Notes (UTF-8 + folder + tags)")
    print("=" * 60)

    conn = sqlite3.connect(str(NOTES_DB))
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id TEXT PRIMARY KEY,
            title TEXT,
            body TEXT,
            created TEXT,
            updated TEXT,
            folder TEXT,
            tags TEXT
        )
    """)
    for col in ("folder", "tags"):
        try:
            cursor.execute(f"ALTER TABLE notes ADD COLUMN {col} TEXT")
        except sqlite3.OperationalError:
            pass

    count = 0
    for note in extract_notes():
        body = note.get("body", "")
        tags = extract_tags(body)
        tags_str = ",".join(sorted(tags)) if tags else ""

        cursor.execute("""
            INSERT OR REPLACE INTO notes (id, title, body, created, updated, folder, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            note.get("id"),
            note.get("title"),
            body,
            note.get("created"),
            note.get("updated"),
            note.get("folder", ""),
            tags_str
        ))
        count += 1
        if count % 50 == 0:
            print(f"✓ 已导出 {count} 条笔记...")

    conn.commit()
    conn.close()

    print(f"\\n✅ 导出完成！共 {count} 条笔记")

    # 验证
    conn = sqlite3.connect(str(NOTES_DB))
    folders = conn.execute("""
        SELECT folder, COUNT(*) FROM notes
        WHERE folder != '' GROUP BY folder ORDER BY COUNT(*) DESC
    """).fetchall()
    print("\\n📁 文件夹分布:")
    for f, c in folders:
        print(f"  {f}: {c}")
    conn.close()


if __name__ == "__main__":
    main()
