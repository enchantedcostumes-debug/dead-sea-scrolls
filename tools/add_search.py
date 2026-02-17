#!/usr/bin/env python3
"""
Add search button and JS to all 36 chapter HTML files.
Inserts search button in toolbar and script tag before closing body.

Copyright (c) 2026 Tammy L Casey. All rights reserved.
"""

import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.join(SCRIPT_DIR, '..')
CHAPTERS_DIR = os.path.join(PROJECT_ROOT, '1_enoch')


def update_chapter(filepath):
    """Add search button and script to a chapter file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    modified = False

    # 1. Add search button to toolbar (if not already present)
    if 'openSearch' not in content:
        old_btn = '<button id="grammar-toggle" onclick="toggleGrammar()">Grammar View</button>'
        new_btn = (
            '<button id="grammar-toggle" onclick="toggleGrammar()">Grammar View</button>\n'
            '            <button id="search-toggle" onclick="openSearch()">Search</button>'
        )
        if old_btn in content:
            content = content.replace(old_btn, new_btn)
            modified = True

    # 2. Add search.js script (if not already present)
    if 'search.js' not in content:
        old_script = '<script src="../js/grammar-view.js"></script>'
        new_script = (
            '<script src="../js/grammar-view.js"></script>\n'
            '<script src="../js/search.js"></script>'
        )
        if old_script in content:
            content = content.replace(old_script, new_script)
            modified = True

    # 3. Add verse anchors for deep linking (id="v1-1" etc.)
    if 'id="v' not in content:
        import re
        def add_anchor(match):
            verse_ref = match.group(1)
            anchor_id = 'v' + verse_ref.replace(':', '-')
            return '<div class="verse-block" id="' + anchor_id + '">'

        # Replace verse blocks with anchored versions
        pattern = r'<div class="verse-block">\s*\n\s*<div class="verse-ref">\s*\n\s*<span class="verse-number">(\d+:\d+)</span>'
        new_content = re.sub(
            pattern,
            lambda m: '<div class="verse-block" id="v' + m.group(1).replace(':', '-') + '">\n'
            + '                <div class="verse-ref">\n'
            + '                    <span class="verse-number">' + m.group(1) + '</span>',
            content
        )
        if new_content != content:
            content = new_content
            modified = True

    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

    return modified


def main():
    updated = 0
    for i in range(1, 37):
        filepath = os.path.join(CHAPTERS_DIR, f'{i}.html')
        if not os.path.exists(filepath):
            print(f"[WARN] Missing: {filepath}")
            continue
        if update_chapter(filepath):
            updated += 1
            print(f"[OK] Updated chapter {i}")
        else:
            print(f"[--] Chapter {i} already has search")

    print()
    print(f"[OK] Updated {updated}/36 chapters with search")


if __name__ == '__main__':
    main()
