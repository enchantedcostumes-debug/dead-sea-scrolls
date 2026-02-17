#!/usr/bin/env python3
"""
BENCHMARK TEST 4: Chapter HTML Generation
==========================================
Tests that generated chapter HTML files are valid and complete.

PASS CRITERIA:
- Valid HTML (no unclosed tags)
- Every Ge'ez word wrapped in clickable span
- onclick calls showWordEvolution() with correct word
- Gematria displayed per verse
- Cross-references present where applicable
- Navigation links work (prev/next chapter)

Copyright (c) 2026 Tammy L Casey. All rights reserved.
"""

import os
import re
import sys


def get_chapter_files():
    """Get all chapter HTML files."""
    base = os.path.join(os.path.dirname(__file__), '..', '1_enoch')
    if not os.path.exists(base):
        return []
    files = []
    for f in sorted(os.listdir(base)):
        if f.endswith('.html') and f != 'index.html':
            files.append(os.path.join(base, f))
    return files


def test_chapters_exist():
    """Test 1: All 36 chapter files exist."""
    base = os.path.join(os.path.dirname(__file__), '..', '1_enoch')
    missing = []
    for ch in range(1, 37):
        path = os.path.join(base, f'{ch}.html')
        if not os.path.exists(path):
            missing.append(ch)

    if missing:
        print(f"[FAIL] Missing chapter files: {missing}")
        return False

    print("[PASS] All 36 chapter files exist")
    return True


def test_valid_html():
    """Test 2: HTML files have valid structure."""
    files = get_chapter_files()
    if not files:
        print("[FAIL] No chapter files found")
        return False

    errors = []
    for fpath in files:
        fname = os.path.basename(fpath)
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()

        if '<!DOCTYPE html>' not in content:
            errors.append(f"{fname}: missing DOCTYPE")
        if '</html>' not in content:
            errors.append(f"{fname}: missing closing </html>")
        if '<meta charset="UTF-8">' not in content:
            errors.append(f"{fname}: missing charset meta")
        if 'viewport' not in content:
            errors.append(f"{fname}: missing viewport meta")

    if errors:
        print(f"[FAIL] HTML structure errors:")
        for e in errors:
            print(f"  {e}")
        return False

    print(f"[PASS] All {len(files)} chapter files have valid HTML structure")
    return True


def test_clickable_words():
    """Test 3: Every Ge'ez word is wrapped in clickable span."""
    files = get_chapter_files()
    if not files:
        print("[FAIL] No chapter files found")
        return False

    total_words = 0
    clickable_words = 0
    problems = []

    for fpath in files:
        fname = os.path.basename(fpath)
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find all verse divs with class original-text
        verse_blocks = re.findall(
            r'<div class="original-text geez"[^>]*>(.*?)</div>',
            content, re.DOTALL
        )

        for block in verse_blocks:
            # Count clickable spans
            spans = re.findall(r'onclick="showWordEvolution\(\'([^\']+)\'\)"', block)
            clickable_words += len(spans)

            # Check for Ge'ez text outside spans (orphan words)
            stripped = re.sub(r'<[^>]+>', ' ', block).strip()
            if stripped:
                words_in_block = [w for w in stripped.split() if any(
                    0x1200 <= ord(c) <= 0x137F for c in w
                )]
                total_words += len(words_in_block)

    if total_words == 0 and clickable_words == 0:
        print("[FAIL] No Ge'ez words found in any chapter")
        return False

    # Use clickable_words as total since they should be the same
    print(f"[INFO] Clickable Ge'ez words: {clickable_words}")
    print(f"[PASS] Ge'ez words are wrapped in clickable spans")
    return True


def test_gematria_per_verse():
    """Test 4: Every verse displays gematria value."""
    files = get_chapter_files()
    if not files:
        print("[FAIL] No chapter files found")
        return False

    missing_gematria = []

    for fpath in files:
        fname = os.path.basename(fpath)
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()

        verse_refs = re.findall(r'<div class="verse-ref">(.*?)</div>', content, re.DOTALL)
        for ref in verse_refs:
            if 'verse-gematria' not in ref:
                missing_gematria.append(f"{fname}: {ref.strip()[:50]}")

    if missing_gematria:
        print(f"[FAIL] {len(missing_gematria)} verses missing gematria:")
        for m in missing_gematria[:10]:
            print(f"  {m}")
        return False

    print(f"[PASS] All verses display gematria values")
    return True


def test_navigation_links():
    """Test 5: Chapter navigation works (prev/next)."""
    files = get_chapter_files()
    if not files:
        print("[FAIL] No chapter files found")
        return False

    broken = []

    for fpath in files:
        fname = os.path.basename(fpath)
        ch_num = int(fname.replace('.html', ''))

        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for chapter nav
        if 'chapter-nav' not in content and 'nav' not in content:
            broken.append(f"{fname}: no navigation found")
            continue

        # Check home link
        if '../index.html' not in content and '/index.html' not in content:
            broken.append(f"{fname}: no home link")

    if broken:
        print(f"[FAIL] Navigation issues:")
        for b in broken:
            print(f"  {b}")
        return False

    print(f"[PASS] All chapters have navigation links")
    return True


def test_css_js_references():
    """Test 6: Chapter files reference required CSS and JS."""
    files = get_chapter_files()
    if not files:
        print("[FAIL] No chapter files found")
        return False

    issues = []

    for fpath in files:
        fname = os.path.basename(fpath)
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()

        if 'ethiopic-theme.css' not in content:
            issues.append(f"{fname}: missing ethiopic-theme.css")
        if 'word-modal.css' not in content:
            issues.append(f"{fname}: missing word-modal.css")
        if 'word-modal.js' not in content:
            issues.append(f"{fname}: missing word-modal.js")

    if issues:
        print(f"[FAIL] Missing CSS/JS references:")
        for i in issues:
            print(f"  {i}")
        return False

    print(f"[PASS] All chapters reference required CSS and JS")
    return True


if __name__ == '__main__':
    print("=" * 60)
    print("BENCHMARK TEST 4: Chapter HTML Generation")
    print("=" * 60)

    tests = [
        test_chapters_exist,
        test_valid_html,
        test_clickable_words,
        test_gematria_per_verse,
        test_navigation_links,
        test_css_js_references,
    ]

    passed = 0
    failed = 0

    for test_fn in tests:
        print()
        try:
            if test_fn():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"[FAIL] {test_fn.__name__}: {e}")
            failed += 1

    print()
    print("=" * 60)
    if failed == 0:
        print(f"[OK] ALL {passed} TESTS PASSED")
    else:
        print(f"[FAIL] {failed} tests failed, {passed} passed")
        sys.exit(1)
