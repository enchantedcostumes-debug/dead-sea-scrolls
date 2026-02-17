#!/usr/bin/env python3
"""
Test: Parallel English Translation View (Phase 5)
===================================================
Verifies that:
1. All 36 chapter HTML files have parallel view toggle button
2. All chapters load parallel-view.js
3. CSS has parallel view styles
4. parallel-view.js has required functions
5. Each verse has both Ge'ez original and English translation
6. Charles 1917 attribution is present

Copyright (c) 2026 Tammy L Casey. All rights reserved.
"""

import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.join(SCRIPT_DIR, '..')


def test_parallel_toggle_in_chapters():
    """All 36 chapter HTML files have parallel view toggle button."""
    chapters_dir = os.path.join(PROJECT_ROOT, '1_enoch')
    missing = []
    for i in range(1, 37):
        path = os.path.join(chapters_dir, f'{i}.html')
        assert os.path.exists(path), f"FAIL: {path} not found"
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        if 'parallel-toggle' not in content:
            missing.append(i)

    assert not missing, \
        f"FAIL: {len(missing)} chapters missing parallel toggle: {missing[:5]}"

    print(f"[PASS] All 36 chapters have parallel view toggle button")


def test_chapters_load_parallel_js():
    """All 36 chapters load parallel-view.js."""
    chapters_dir = os.path.join(PROJECT_ROOT, '1_enoch')
    missing = []
    for i in range(1, 37):
        path = os.path.join(chapters_dir, f'{i}.html')
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        if 'parallel-view.js' not in content:
            missing.append(i)

    assert not missing, \
        f"FAIL: {len(missing)} chapters not loading parallel-view.js: {missing[:5]}"

    print(f"[PASS] All 36 chapters load parallel-view.js")


def test_css_parallel_styles():
    """CSS has parallel view layout styles."""
    css_path = os.path.join(PROJECT_ROOT, 'css', 'ethiopic-theme.css')
    with open(css_path, 'r', encoding='utf-8') as f:
        content = f.read()

    required = [
        '.parallel-verse',
        '.parallel-geez',
        '.parallel-english',
        '#parallel-toggle',
    ]

    for cls in required:
        assert cls in content, f"FAIL: CSS class {cls} missing from ethiopic-theme.css"

    print(f"[PASS] CSS has all {len(required)} parallel view styles")


def test_parallel_js_functions():
    """parallel-view.js has required functions and structure."""
    js_path = os.path.join(PROJECT_ROOT, 'js', 'parallel-view.js')
    assert os.path.exists(js_path), "FAIL: js/parallel-view.js not found"

    with open(js_path, 'r', encoding='utf-8') as f:
        content = f.read()

    assert 'toggleParallel' in content, \
        "FAIL: parallel-view.js missing toggleParallel function"
    assert 'enableParallel' in content, \
        "FAIL: parallel-view.js missing enableParallel function"
    assert 'disableParallel' in content, \
        "FAIL: parallel-view.js missing disableParallel function"
    assert 'parallel-verse' in content, \
        "FAIL: parallel-view.js missing parallel-verse class"
    assert 'parallel-geez' in content, \
        "FAIL: parallel-view.js missing parallel-geez class"
    assert 'parallel-english' in content, \
        "FAIL: parallel-view.js missing parallel-english class"

    print("[PASS] parallel-view.js has all required functions and classes")


def test_verses_have_both_texts():
    """Each verse block in chapter 1 has both Ge'ez and English translation."""
    ch1_path = os.path.join(PROJECT_ROOT, '1_enoch', '1.html')
    with open(ch1_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Count verse blocks, original texts, and translations
    verse_blocks = content.count('class="verse-block"')
    original_texts = content.count('class="original-text geez"')
    translations = content.count('class="translation"')

    assert verse_blocks > 0, "FAIL: No verse blocks found in chapter 1"
    assert original_texts == verse_blocks, \
        f"FAIL: Mismatch - {verse_blocks} verse blocks but {original_texts} original texts"
    assert translations == verse_blocks, \
        f"FAIL: Mismatch - {verse_blocks} verse blocks but {translations} translations"

    print(f"[PASS] Chapter 1 has {verse_blocks} complete verse blocks "
          f"(Ge'ez + English in each)")


def test_charles_attribution():
    """Charles 1917 attribution is present in parallel view JS."""
    js_path = os.path.join(PROJECT_ROOT, 'js', 'parallel-view.js')
    with open(js_path, 'r', encoding='utf-8') as f:
        content = f.read()

    assert 'Charles' in content, \
        "FAIL: parallel-view.js missing Charles attribution"
    assert '1917' in content, \
        "FAIL: parallel-view.js missing 1917 date reference"

    print("[PASS] Charles 1917 attribution present in parallel view")


if __name__ == '__main__':
    print("=" * 60)
    print("TESTING: Parallel English Translation View (Phase 5)")
    print("=" * 60)
    print()

    try:
        test_parallel_toggle_in_chapters()
        test_chapters_load_parallel_js()
        test_css_parallel_styles()
        test_parallel_js_functions()
        test_verses_have_both_texts()
        test_charles_attribution()

        print()
        print("[OK] ALL 6 TESTS PASSED")
    except AssertionError as e:
        print()
        print(f"[FAIL] {e}")
        sys.exit(1)
