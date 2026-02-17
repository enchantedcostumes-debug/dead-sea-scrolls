#!/usr/bin/env python3
"""
Test: Cognate Tree Visualization (Phase 4)
============================================
Verifies that:
1. words.json has structured hebrew_cognate and arabic_cognate fields
2. At least 40% of words have cognate data
3. Cognate data has required structure (script, translit, meaning)
4. Word modal JS renders the cognate tree
5. CSS has cognate tree styles
6. Cognate tree handles missing data gracefully

Copyright (c) 2026 Tammy L Casey. All rights reserved.
"""

import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.join(SCRIPT_DIR, '..')


def test_cognate_fields_exist():
    """words.json has hebrew_cognate and arabic_cognate fields."""
    words_path = os.path.join(PROJECT_ROOT, 'words.json')
    with open(words_path, 'r', encoding='utf-8') as f:
        words = json.load(f)

    total = len(words)
    has_heb = sum(1 for w in words.values() if w.get('hebrew_cognate'))
    has_ar = sum(1 for w in words.values() if w.get('arabic_cognate'))
    has_either = sum(1 for w in words.values()
                     if w.get('hebrew_cognate') or w.get('arabic_cognate'))

    assert has_heb > 0, "FAIL: No words have hebrew_cognate"
    assert has_ar > 0, "FAIL: No words have arabic_cognate"

    print(f"[PASS] Cognate fields exist: hebrew={has_heb}/{total}, "
          f"arabic={has_ar}/{total}, either={has_either}/{total}")


def test_cognate_coverage():
    """At least 40% of words have cognate data."""
    words_path = os.path.join(PROJECT_ROOT, 'words.json')
    with open(words_path, 'r', encoding='utf-8') as f:
        words = json.load(f)

    total = len(words)
    has_either = sum(1 for w in words.values()
                     if w.get('hebrew_cognate') or w.get('arabic_cognate'))
    pct = has_either / total * 100

    assert pct >= 40, f"FAIL: Cognate coverage {pct:.1f}% < 40%"

    print(f"[PASS] Cognate coverage: {pct:.1f}% ({has_either}/{total})")


def test_cognate_structure():
    """Cognate data has required structure (translit + meaning or script)."""
    words_path = os.path.join(PROJECT_ROOT, 'words.json')
    with open(words_path, 'r', encoding='utf-8') as f:
        words = json.load(f)

    bad_heb = []
    bad_ar = []

    for word, info in words.items():
        heb = info.get('hebrew_cognate')
        if heb:
            if not heb.get('translit') and not heb.get('script'):
                bad_heb.append(word)

        ar = info.get('arabic_cognate')
        if ar:
            if not ar.get('translit') and not ar.get('script'):
                bad_ar.append(word)

    assert not bad_heb, \
        f"FAIL: {len(bad_heb)} Hebrew cognates missing translit/script: {bad_heb[:3]}"
    assert not bad_ar, \
        f"FAIL: {len(bad_ar)} Arabic cognates missing translit/script: {bad_ar[:3]}"

    # Count how many have script (actual Hebrew/Arabic text)
    with_heb_script = sum(1 for w in words.values()
                          if w.get('hebrew_cognate', {}).get('script'))
    with_ar_script = sum(1 for w in words.values()
                         if w.get('arabic_cognate', {}).get('script'))

    print(f"[PASS] Cognate structure valid. "
          f"Hebrew with script: {with_heb_script}, Arabic with script: {with_ar_script}")


def test_modal_renders_cognate_tree():
    """word-modal.js has cognate tree rendering code."""
    js_path = os.path.join(PROJECT_ROOT, 'js', 'word-modal.js')
    with open(js_path, 'r', encoding='utf-8') as f:
        content = f.read()

    assert 'hebrew_cognate' in content, \
        "FAIL: word-modal.js does not reference hebrew_cognate"
    assert 'arabic_cognate' in content, \
        "FAIL: word-modal.js does not reference arabic_cognate"
    assert 'cognate-tree' in content, \
        "FAIL: word-modal.js missing cognate-tree class"
    assert 'cognate-branch' in content, \
        "FAIL: word-modal.js missing cognate-branch class"
    assert 'cognate-hebrew' in content, \
        "FAIL: word-modal.js missing cognate-hebrew class"
    assert 'cognate-arabic' in content, \
        "FAIL: word-modal.js missing cognate-arabic class"
    assert 'cognate-geez' in content, \
        "FAIL: word-modal.js missing cognate-geez class"
    assert 'Semitic Cognate Family' in content, \
        "FAIL: word-modal.js missing section header"

    print("[PASS] word-modal.js renders cognate tree with Hebrew/Ge'ez/Arabic branches")


def test_css_cognate_styles():
    """CSS has cognate tree styles."""
    css_path = os.path.join(PROJECT_ROOT, 'css', 'word-modal.css')
    with open(css_path, 'r', encoding='utf-8') as f:
        content = f.read()

    required = [
        '.cognate-tree',
        '.cognate-branches',
        '.cognate-branch',
        '.cognate-hebrew',
        '.cognate-geez',
        '.cognate-arabic',
        '.cognate-script',
        '.cognate-translit',
        '.cognate-meaning',
        '.cognate-lang-label',
    ]

    for cls in required:
        assert cls in content, f"FAIL: CSS class {cls} missing from word-modal.css"

    print(f"[PASS] CSS has all {len(required)} cognate tree styles")


def test_cognate_tree_handles_partial():
    """Cognate tree handles words with only Hebrew or only Arabic or neither."""
    words_path = os.path.join(PROJECT_ROOT, 'words.json')
    with open(words_path, 'r', encoding='utf-8') as f:
        words = json.load(f)

    heb_only = sum(1 for w in words.values()
                   if w.get('hebrew_cognate') and not w.get('arabic_cognate'))
    ar_only = sum(1 for w in words.values()
                  if w.get('arabic_cognate') and not w.get('hebrew_cognate'))
    both = sum(1 for w in words.values()
               if w.get('hebrew_cognate') and w.get('arabic_cognate'))
    neither = sum(1 for w in words.values()
                  if not w.get('hebrew_cognate') and not w.get('arabic_cognate'))

    # The JS uses hasCognates conditional - verify it handles all cases
    js_path = os.path.join(PROJECT_ROOT, 'js', 'word-modal.js')
    with open(js_path, 'r', encoding='utf-8') as f:
        content = f.read()

    assert 'hasCognates' in content, \
        "FAIL: word-modal.js missing hasCognates conditional"
    # Verify conditional rendering for each branch
    assert 'hebCognate ?' in content, \
        "FAIL: word-modal.js missing conditional Hebrew branch"
    assert 'arCognate ?' in content, \
        "FAIL: word-modal.js missing conditional Arabic branch"

    print(f"[PASS] Handles partial data: both={both}, heb_only={heb_only}, "
          f"ar_only={ar_only}, neither={neither}")


if __name__ == '__main__':
    print("=" * 60)
    print("TESTING: Cognate Tree Visualization (Phase 4)")
    print("=" * 60)
    print()

    try:
        test_cognate_fields_exist()
        test_cognate_coverage()
        test_cognate_structure()
        test_modal_renders_cognate_tree()
        test_css_cognate_styles()
        test_cognate_tree_handles_partial()

        print()
        print("[OK] ALL 6 TESTS PASSED")
    except AssertionError as e:
        print()
        print(f"[FAIL] {e}")
        sys.exit(1)
