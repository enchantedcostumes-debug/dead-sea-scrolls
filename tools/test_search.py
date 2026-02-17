#!/usr/bin/env python3
"""
Test: Search Functionality Across All 36 Chapters (Phase 7)
===========================================================
Verifies that:
1. search.js exists with required functions
2. All 36 chapter HTML files load search.js
3. All chapters have search button in toolbar
4. Index page has search UI
5. Search index data file exists with correct structure
6. CSS has search-related styles

Copyright (c) 2026 Tammy L Casey. All rights reserved.
"""

import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.join(SCRIPT_DIR, '..')


def test_search_js_exists():
    """search.js exists with required functions."""
    js_path = os.path.join(PROJECT_ROOT, 'js', 'search.js')
    assert os.path.exists(js_path), "FAIL: js/search.js not found"

    with open(js_path, 'r', encoding='utf-8') as f:
        content = f.read()

    required = [
        'openSearch',
        'closeSearch',
        'performSearch',
        'searchIndex',
    ]

    for func in required:
        assert func in content, \
            f"FAIL: search.js missing '{func}'"

    print(f"[PASS] search.js has all {len(required)} required functions/variables")


def test_chapters_load_search_js():
    """All 36 chapters load search.js."""
    chapters_dir = os.path.join(PROJECT_ROOT, '1_enoch')
    missing = []
    for i in range(1, 37):
        path = os.path.join(chapters_dir, f'{i}.html')
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        if 'search.js' not in content:
            missing.append(i)

    assert not missing, \
        f"FAIL: {len(missing)} chapters not loading search.js: {missing[:5]}"

    print("[PASS] All 36 chapters load search.js")


def test_chapters_have_search_button():
    """All 36 chapters have search button in toolbar."""
    chapters_dir = os.path.join(PROJECT_ROOT, '1_enoch')
    missing = []
    for i in range(1, 37):
        path = os.path.join(chapters_dir, f'{i}.html')
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        if 'search-toggle' not in content and 'openSearch' not in content:
            missing.append(i)

    assert not missing, \
        f"FAIL: {len(missing)} chapters missing search button: {missing[:5]}"

    print("[PASS] All 36 chapters have search button")


def test_index_has_search():
    """Index page has search UI."""
    index_path = os.path.join(PROJECT_ROOT, 'index.html')
    with open(index_path, 'r', encoding='utf-8') as f:
        content = f.read()

    assert 'search' in content.lower(), \
        "FAIL: index.html has no search-related content"

    print("[PASS] Index page has search UI")


def test_search_index_data():
    """Search index data exists with correct structure."""
    # The search index is built from words.json - check it has what search needs
    words_path = os.path.join(PROJECT_ROOT, 'words.json')
    with open(words_path, 'r', encoding='utf-8') as f:
        words = json.load(f)

    # Verify search-relevant fields exist
    searchable = 0
    for geez, data in words.items():
        has_def = bool(data.get('definition') or data.get('english_definition'))
        has_trans = bool(data.get('transliteration'))
        has_occ = bool(data.get('first_occurrence'))
        if has_def and has_trans and has_occ:
            searchable += 1

    pct = searchable / len(words) * 100
    assert pct >= 80, \
        f"FAIL: Only {pct:.1f}% words have searchable fields (need 80%+)"

    print(f"[PASS] Search index: {searchable}/{len(words)} words searchable ({pct:.1f}%)")


def test_css_search_styles():
    """CSS has search-related styles."""
    css_path = os.path.join(PROJECT_ROOT, 'css', 'ethiopic-theme.css')
    with open(css_path, 'r', encoding='utf-8') as f:
        content = f.read()

    required = [
        'search-modal',
        'search-input',
        'search-results',
    ]

    for cls in required:
        assert cls in content, \
            f"FAIL: CSS missing '{cls}' style"

    print(f"[PASS] CSS has all {len(required)} search styles")


if __name__ == '__main__':
    print("=" * 60)
    print("TESTING: Search Functionality (Phase 7)")
    print("=" * 60)
    print()

    try:
        test_search_js_exists()
        test_chapters_load_search_js()
        test_chapters_have_search_button()
        test_index_has_search()
        test_search_index_data()
        test_css_search_styles()

        print()
        print("[OK] ALL 6 TESTS PASSED")
    except AssertionError as e:
        print()
        print(f"[FAIL] {e}")
        sys.exit(1)
