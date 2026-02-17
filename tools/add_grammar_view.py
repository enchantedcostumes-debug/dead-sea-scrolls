#!/usr/bin/env python3
"""
Add grammar view toggle button and JS to all 36 chapter HTML files.
Inserts toggle button in toolbar and script tag before closing body.

Copyright (c) 2026 Tammy L Casey. All rights reserved.
"""

import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.join(SCRIPT_DIR, '..')
CHAPTERS_DIR = os.path.join(PROJECT_ROOT, '1_enoch')


def update_chapter(filepath):
    """Add grammar view toggle and script to a chapter file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    modified = False

    # 1. Add grammar toggle button to toolbar (if not already present)
    if 'grammar-toggle' not in content:
        # Insert after parallel toggle button
        old_btn = '<button id="parallel-toggle" onclick="toggleParallel()">Parallel View</button>'
        new_btn = (
            '<button id="parallel-toggle" onclick="toggleParallel()">Parallel View</button>'
            '\n            <button id="grammar-toggle" onclick="toggleGrammar()">Grammar View</button>'
        )
        if old_btn in content:
            content = content.replace(old_btn, new_btn)
            modified = True

    # 2. Add grammar-view.js script (if not already present)
    if 'grammar-view.js' not in content:
        # Insert after parallel-view.js
        old_script = '<script src="../js/parallel-view.js"></script>'
        new_script = (
            '<script src="../js/parallel-view.js"></script>\n'
            '<script src="../js/grammar-view.js"></script>'
        )
        if old_script in content:
            content = content.replace(old_script, new_script)
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
            print(f"[--] Chapter {i} already has grammar view")

    print()
    print(f"[OK] Updated {updated}/36 chapters with grammar view")


if __name__ == '__main__':
    main()
