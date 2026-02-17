#!/usr/bin/env python3
"""
Add parallel view toggle button and JS to all 36 chapter HTML files.
Inserts toggle button in toolbar and script tag before closing body.

Copyright (c) 2026 Tammy L Casey. All rights reserved.
"""

import os
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.join(SCRIPT_DIR, '..')
CHAPTERS_DIR = os.path.join(PROJECT_ROOT, '1_enoch')


def update_chapter(filepath):
    """Add parallel view toggle and script to a chapter file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    modified = False

    # 1. Add parallel toggle button to toolbar (if not already present)
    if 'parallel-toggle' not in content:
        # Insert after interlinear toggle button
        old_toolbar = '<button id="interlinear-toggle" onclick="toggleInterlinear()">Interlinear View</button>'
        new_toolbar = (
            '<button id="interlinear-toggle" onclick="toggleInterlinear()">Interlinear View</button>'
            '\n            <button id="parallel-toggle" onclick="toggleParallel()">Parallel View</button>'
        )
        if old_toolbar in content:
            content = content.replace(old_toolbar, new_toolbar)
            modified = True

    # 2. Add parallel-view.js script (if not already present)
    if 'parallel-view.js' not in content:
        # Insert after interlinear.js
        old_script = '<script src="../js/interlinear.js"></script>'
        new_script = (
            '<script src="../js/interlinear.js"></script>\n'
            '<script src="../js/parallel-view.js"></script>'
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
            print(f"[--] Chapter {i} already has parallel view")

    print()
    print(f"[OK] Updated {updated}/36 chapters with parallel view")


if __name__ == '__main__':
    main()
