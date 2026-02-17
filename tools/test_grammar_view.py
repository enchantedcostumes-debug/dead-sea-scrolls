#!/usr/bin/env python3
"""
Test: Verse-by-Verse Grammatical Parsing with Color Coding (Phase 6)
=====================================================================
Verifies that:
1. All 36 chapter HTML files have grammar view toggle button
2. All chapters load grammar-view.js
3. grammar-view.js has required functions and POS color mapping
4. CSS has grammar view styles including legend
5. words.json has POS data for 90%+ of words
6. POS color assignments cover all used POS categories

Copyright (c) 2026 Tammy L Casey. All rights reserved.
"""

import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.join(SCRIPT_DIR, '..')


def test_grammar_toggle_in_chapters():
    """All 36 chapter HTML files have grammar view toggle button."""
    chapters_dir = os.path.join(PROJECT_ROOT, '1_enoch')
    missing = []
    for i in range(1, 37):
        path = os.path.join(chapters_dir, f'{i}.html')
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        if 'grammar-toggle' not in content:
            missing.append(i)

    assert not missing, \
        f"FAIL: {len(missing)} chapters missing grammar toggle: {missing[:5]}"

    print("[PASS] All 36 chapters have grammar view toggle button")


def test_chapters_load_grammar_js():
    """All 36 chapters load grammar-view.js."""
    chapters_dir = os.path.join(PROJECT_ROOT, '1_enoch')
    missing = []
    for i in range(1, 37):
        path = os.path.join(chapters_dir, f'{i}.html')
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        if 'grammar-view.js' not in content:
            missing.append(i)

    assert not missing, \
        f"FAIL: {len(missing)} chapters not loading grammar-view.js: {missing[:5]}"

    print("[PASS] All 36 chapters load grammar-view.js")


def test_grammar_js_functions():
    """grammar-view.js has required functions and POS color mapping."""
    js_path = os.path.join(PROJECT_ROOT, 'js', 'grammar-view.js')
    assert os.path.exists(js_path), "FAIL: js/grammar-view.js not found"

    with open(js_path, 'r', encoding='utf-8') as f:
        content = f.read()

    assert 'toggleGrammar' in content, \
        "FAIL: grammar-view.js missing toggleGrammar function"
    assert 'enableGrammar' in content, \
        "FAIL: grammar-view.js missing enableGrammar function"
    assert 'disableGrammar' in content, \
        "FAIL: grammar-view.js missing disableGrammar function"
    assert 'POS_COLORS' in content, \
        "FAIL: grammar-view.js missing POS_COLORS mapping"
    assert 'grammar-legend' in content, \
        "FAIL: grammar-view.js missing grammar-legend class"

    print("[PASS] grammar-view.js has all required functions and POS colors")


def test_css_grammar_styles():
    """CSS has grammar view styles including legend."""
    css_path = os.path.join(PROJECT_ROOT, 'css', 'ethiopic-theme.css')
    with open(css_path, 'r', encoding='utf-8') as f:
        content = f.read()

    required = [
        '.grammar-legend',
        '.grammar-legend-item',
        '#grammar-toggle',
    ]

    for cls in required:
        assert cls in content, f"FAIL: CSS class {cls} missing from ethiopic-theme.css"

    print(f"[PASS] CSS has all {len(required)} grammar view styles")


def test_pos_data_coverage():
    """words.json has POS data for 90%+ of words."""
    words_path = os.path.join(PROJECT_ROOT, 'words.json')
    with open(words_path, 'r', encoding='utf-8') as f:
        words = json.load(f)

    total = len(words)
    has_pos = sum(1 for w in words.values() if w.get('part_of_speech'))
    pct = has_pos / total * 100

    assert pct >= 90, f"FAIL: POS coverage {pct:.1f}% < 90%"

    print(f"[PASS] POS coverage: {pct:.1f}% ({has_pos}/{total})")


def test_pos_colors_cover_all_categories():
    """POS color assignments in JS cover all used POS categories."""
    js_path = os.path.join(PROJECT_ROOT, 'js', 'grammar-view.js')
    with open(js_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Get all POS categories from words.json
    words_path = os.path.join(PROJECT_ROOT, 'words.json')
    with open(words_path, 'r', encoding='utf-8') as f:
        words = json.load(f)

    pos_categories = set()
    for w in words.values():
        pos = w.get('part_of_speech', '')
        if pos:
            pos_categories.add(pos)

    missing = []
    for pos in pos_categories:
        # Check if POS is referenced in the color mapping
        if f"'{pos}'" not in content and f'"{pos}"' not in content:
            missing.append(pos)

    assert not missing, \
        f"FAIL: POS categories not in color map: {missing}"

    print(f"[PASS] All {len(pos_categories)} POS categories have color assignments")


if __name__ == '__main__':
    print("=" * 60)
    print("TESTING: Grammatical Parsing with Color Coding (Phase 6)")
    print("=" * 60)
    print()

    try:
        test_grammar_toggle_in_chapters()
        test_chapters_load_grammar_js()
        test_grammar_js_functions()
        test_css_grammar_styles()
        test_pos_data_coverage()
        test_pos_colors_cover_all_categories()

        print()
        print("[OK] ALL 6 TESTS PASSED")
    except AssertionError as e:
        print()
        print(f"[FAIL] {e}")
        sys.exit(1)
