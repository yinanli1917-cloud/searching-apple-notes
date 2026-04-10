#!/usr/bin/env python3
"""
Create an Apple Note via AppleScript — Skill helper script.

[INPUT]:  Title and body (markdown supported, hashtags as #Tag)
[OUTPUT]: New note ID printed to stdout
[POS]:    Lets the skill turn dialogue insights into Apple Notes

Tags work natively: write #TagName anywhere in the body and Apple Notes
auto-converts it to a real searchable tag.

Usage:
    python3 create_note.py "Title" "Body content with #Tag1 #Tag2"
    python3 create_note.py "Title" "Body" --folder "Notes"
    echo "long body" | python3 create_note.py "Title" --stdin
"""

import subprocess
import sys
import argparse
import re


def escape_applescript(text: str) -> str:
    """Escape backslashes and quotes for AppleScript string literals."""
    return text.replace('\\', '\\\\').replace('"', '\\"')


def md_to_apple_html(text: str) -> str:
    """
    Convert a subset of markdown to HTML that Apple Notes renders correctly.

    Supported: h1/h2/h3, bold, italic, inline code, bullet lists, horizontal
    rules, strikethrough. Apple Notes quirks worked around: <ol> becomes <ul>,
    <a href> loses links, <blockquote> is stripped — so we don't emit them.
    """
    lines = text.split('\n')
    html_lines = []
    in_list = False

    for line in lines:
        stripped = line.strip()

        # Close any open list when we leave list items
        if in_list and not re.match(r'^[-*+] ', stripped):
            html_lines.append('</ul>')
            in_list = False

        # Headings: # → h1, ## → h2, ### → h3
        m = re.match(r'^(#{1,3}) (.+)$', stripped)
        if m:
            level = len(m.group(1))
            heading_text = _inline_format(m.group(2))
            if level == 1:
                html_lines.append(f'<h1>{heading_text}</h1>')
            elif level == 2:
                html_lines.append(f'<h2>{heading_text}</h2>')
            else:
                html_lines.append(f'<h3>{heading_text}</h3>')
            continue

        # Horizontal rule: --- or ***
        if re.match(r'^[-*]{3,}\s*$', stripped):
            html_lines.append('<div><font color="#808080">———</font></div>')
            continue

        # Bullet list items
        m = re.match(r'^[-*+] (.+)$', stripped)
        if m:
            if not in_list:
                html_lines.append('<ul>')
                in_list = True
            html_lines.append(f'<li>{_inline_format(m.group(1))}</li>')
            continue

        # Empty line → spacing div
        if stripped == '':
            html_lines.append('<div><br></div>')
            continue

        # Plain paragraph
        html_lines.append(f'<div>{_inline_format(stripped)}</div>')

    if in_list:
        html_lines.append('</ul>')

    return ''.join(html_lines)


def _inline_format(text: str) -> str:
    """Convert inline markdown: **bold**, *italic*, `code`, ~~strike~~."""
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'__(.+?)__', r'<b>\1</b>', text)
    text = re.sub(r'(?<!\w)\*(.+?)\*(?!\w)', r'<i>\1</i>', text)
    text = re.sub(r'(?<!\w)_(.+?)_(?!\w)', r'<i>\1</i>', text)
    text = re.sub(r'`(.+?)`', r'<font face="Courier">\1</font>', text)
    text = re.sub(r'~~(.+?)~~', r'<s>\1</s>', text)
    return text


def create_note(title: str, body: str, folder: str = "Notes") -> str:
    """Create a note in Apple Notes. Returns the new note's ID."""
    html_body = md_to_apple_html(body)

    escaped_title = escape_applescript(title)
    escaped_body = escape_applescript(html_body)
    escaped_folder = escape_applescript(folder)

    script = f'''
tell application "Notes"
    set targetFolder to folder "{escaped_folder}" of default account
    set newNote to make new note at targetFolder with properties {{name:"{escaped_title}", body:"{escaped_body}"}}
    return id of newNote
end tell
'''
    result = subprocess.run(
        ['osascript', '-e', script],
        capture_output=True, text=True, timeout=30
    )

    if result.returncode != 0:
        print(f"Error: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)

    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser(description='Create an Apple Note from markdown')
    parser.add_argument('title', help='Note title')
    parser.add_argument('body', nargs='?', default=None, help='Note body (supports #tags)')
    parser.add_argument('--folder', default='Notes', help='Target folder (default: Notes)')
    parser.add_argument('--stdin', action='store_true', help='Read body from stdin')

    args = parser.parse_args()

    if args.stdin:
        body = sys.stdin.read().strip()
    elif args.body:
        body = args.body
    else:
        print("Error: provide body as argument or use --stdin", file=sys.stderr)
        sys.exit(1)

    note_id = create_note(args.title, body, args.folder)
    print(f"Created: {note_id}")


if __name__ == '__main__':
    main()
