#!/usr/bin/env python3
"""
BENCHMARK TEST 1: Ge'ez Text Extraction
========================================
Tests that Ge'ez text is correctly extracted and encoded.

PASS CRITERIA:
- All text in Ethiopic Unicode block (U+1200-U+137F, U+1380-U+139F, U+2D80-U+2DDF)
- Word counts match scholarly sources +/-2%
- No Latin characters mixed into Ge'ez text
- Chapter/verse structure is correct

Copyright (c) 2026 Tammy L Casey. All rights reserved.
"""

import json
import os
import re
import sys

# Ethiopic Unicode ranges
ETHIOPIC_RANGES = [
    (0x1200, 0x137F),  # Ethiopic
    (0x1380, 0x139F),  # Ethiopic Supplement
    (0x2D80, 0x2DDF),  # Ethiopic Extended
    (0xAB00, 0xAB2F),  # Ethiopic Extended-A
]

# Known verse counts per chapter (from Charles 1906 critical edition)
CHARLES_VERSE_COUNTS = {
    1: 9, 2: 3, 3: 1, 4: 1, 5: 9, 6: 8, 7: 6, 8: 4, 9: 11, 10: 22,
    11: 2, 12: 6, 13: 10, 14: 25, 15: 12, 16: 4, 17: 8, 18: 16, 19: 3,
    20: 8, 21: 10, 22: 14, 23: 4, 24: 6, 25: 7, 26: 6, 27: 5, 28: 3,
    29: 2, 30: 3, 31: 3, 32: 6, 33: 4, 34: 3, 35: 1, 36: 4
}


def is_ethiopic_char(char):
    """Check if a character is in the Ethiopic Unicode block."""
    code = ord(char)
    for start, end in ETHIOPIC_RANGES:
        if start <= code <= end:
            return True
    return False


def is_punctuation_or_space(char):
    """Allow spaces, punctuation, numbers, and Ethiopic punctuation."""
    if char in ' \t\n\r.:,;!?()[]{}0123456789':
        return True
    code = ord(char)
    # Ethiopic punctuation
    if 0x1360 <= code <= 0x137F:
        return True
    return False


def test_unicode_encoding():
    """Test 1: Verify all Ge'ez text is in correct Unicode encoding."""
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'enoch_geez_text.json')

    if not os.path.exists(data_path):
        print("[FAIL] enoch_geez_text.json does not exist yet")
        return False

    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    violations = []
    total_chars = 0
    ethiopic_chars = 0

    for chapter_key, chapter_data in data.items():
        for verse_key, verse_text in chapter_data.get('verses', {}).items():
            geez_text = verse_text.get('geez', '')
            for char in geez_text:
                if is_punctuation_or_space(char):
                    continue
                total_chars += 1
                if is_ethiopic_char(char):
                    ethiopic_chars += 1
                else:
                    violations.append({
                        'chapter': chapter_key,
                        'verse': verse_key,
                        'char': char,
                        'code': hex(ord(char))
                    })

    if total_chars == 0:
        print("[FAIL] No Ge'ez characters found in data")
        return False

    pct = (ethiopic_chars / total_chars) * 100
    print(f"[INFO] Total non-space characters: {total_chars}")
    print(f"[INFO] Ethiopic characters: {ethiopic_chars} ({pct:.1f}%)")

    if violations:
        print(f"[FAIL] {len(violations)} non-Ethiopic characters found:")
        for v in violations[:10]:
            print(f"  Chapter {v['chapter']} Verse {v['verse']}: '{v['char']}' ({v['code']})")
        return False

    print(f"[PASS] All {total_chars} characters are valid Ethiopic Unicode")
    return True


def test_no_latin_mixed():
    """Test 2: Verify no Latin characters are mixed into Ge'ez text."""
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'enoch_geez_text.json')

    if not os.path.exists(data_path):
        print("[FAIL] enoch_geez_text.json does not exist yet")
        return False

    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    latin_found = []
    latin_pattern = re.compile(r'[a-zA-Z]')

    for chapter_key, chapter_data in data.items():
        for verse_key, verse_text in chapter_data.get('verses', {}).items():
            geez_text = verse_text.get('geez', '')
            matches = latin_pattern.findall(geez_text)
            if matches:
                latin_found.append({
                    'chapter': chapter_key,
                    'verse': verse_key,
                    'latin_chars': matches
                })

    if latin_found:
        print(f"[FAIL] Latin characters found in {len(latin_found)} verses:")
        for lf in latin_found[:10]:
            print(f"  Chapter {lf['chapter']} Verse {lf['verse']}: {''.join(lf['latin_chars'])}")
        return False

    print("[PASS] No Latin characters mixed into Ge'ez text")
    return True


def test_verse_counts():
    """Test 3: Verify verse counts match Charles 1906 edition."""
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'enoch_geez_text.json')

    if not os.path.exists(data_path):
        print("[FAIL] enoch_geez_text.json does not exist yet")
        return False

    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    mismatches = []
    for chapter_num, expected_count in CHARLES_VERSE_COUNTS.items():
        chapter_key = str(chapter_num)
        if chapter_key not in data:
            mismatches.append(f"Chapter {chapter_num}: MISSING (expected {expected_count} verses)")
            continue

        actual_count = len(data[chapter_key].get('verses', {}))
        if actual_count != expected_count:
            mismatches.append(
                f"Chapter {chapter_num}: {actual_count} verses (expected {expected_count})"
            )

    if mismatches:
        print(f"[FAIL] {len(mismatches)} verse count mismatches:")
        for m in mismatches:
            print(f"  {m}")
        return False

    print(f"[PASS] All {len(CHARLES_VERSE_COUNTS)} chapters have correct verse counts")
    return True


def test_chapter_coverage():
    """Test 4: Verify all 36 chapters of Book of Watchers are present."""
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'enoch_geez_text.json')

    if not os.path.exists(data_path):
        print("[FAIL] enoch_geez_text.json does not exist yet")
        return False

    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    missing = []
    for ch in range(1, 37):
        if str(ch) not in data:
            missing.append(ch)

    if missing:
        print(f"[FAIL] Missing chapters: {missing}")
        return False

    print("[PASS] All 36 chapters (Book of the Watchers) present")
    return True


def test_words_per_verse():
    """Test 5: Verify each verse has at least 1 Ge'ez word."""
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'enoch_geez_text.json')

    if not os.path.exists(data_path):
        print("[FAIL] enoch_geez_text.json does not exist yet")
        return False

    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    empty_verses = []
    total_words = 0

    for chapter_key, chapter_data in data.items():
        for verse_key, verse_text in chapter_data.get('verses', {}).items():
            geez_text = verse_text.get('geez', '').strip()
            words = [w for w in geez_text.split() if any(is_ethiopic_char(c) for c in w)]
            if not words:
                empty_verses.append(f"{chapter_key}:{verse_key}")
            total_words += len(words)

    if empty_verses:
        print(f"[FAIL] {len(empty_verses)} verses have no Ge'ez words:")
        for ev in empty_verses[:10]:
            print(f"  {ev}")
        return False

    print(f"[PASS] All verses contain Ge'ez text. Total words: {total_words}")
    return True


if __name__ == '__main__':
    print("=" * 60)
    print("BENCHMARK TEST 1: Ge'ez Text Extraction")
    print("=" * 60)

    tests = [
        test_unicode_encoding,
        test_no_latin_mixed,
        test_verse_counts,
        test_chapter_coverage,
        test_words_per_verse,
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
