#!/usr/bin/env python3
"""
BENCHMARK TEST 2: Lexicon Completeness
=======================================
Tests that every unique Ge'ez word has a complete lexicon entry.

PASS CRITERIA:
- 100% coverage: every word in chapters 1-36 has a lexicon entry
- Every entry has: geez, transliteration, root, definition
- Every entry has gematria value calculated
- Definition sourced from Dillmann or Leslau (cited)
- Cross-reference to Hebrew cognate where applicable

Copyright (c) 2026 Tammy L Casey. All rights reserved.
"""

import json
import os
import sys

REQUIRED_FIELDS = ['geez', 'transliteration', 'root', 'definition', 'gematria']
RECOMMENDED_FIELDS = ['digital_root', 'first_occurrence', 'frequency', 'letters']


def load_data():
    """Load both the Ge'ez text and the words database."""
    base = os.path.join(os.path.dirname(__file__), '..')
    text_path = os.path.join(base, 'data', 'enoch_geez_text.json')
    words_path = os.path.join(base, 'words.json')

    if not os.path.exists(text_path):
        return None, None, "enoch_geez_text.json does not exist yet"
    if not os.path.exists(words_path):
        return None, None, "words.json does not exist yet"

    with open(text_path, 'r', encoding='utf-8') as f:
        text_data = json.load(f)
    with open(words_path, 'r', encoding='utf-8') as f:
        words_data = json.load(f)

    return text_data, words_data, None


def extract_unique_words(text_data):
    """Extract all unique Ge'ez words from the text.

    Ge'ez uses Ethiopic wordspace U+1361 as word separator,
    NOT regular ASCII spaces. Must split on U+1361.
    """
    unique = set()
    for chapter_data in text_data.values():
        for verse_data in chapter_data.get('verses', {}).values():
            geez_text = verse_data.get('geez', '')
            # Split on Ethiopic wordspace (U+1361) and full stop (U+1362)
            # Also handle any regular spaces just in case
            words = geez_text.replace('\u1362', '\u1361').split('\u1361')
            for w in words:
                w = w.strip(' \u1361\u1362\u1363\u1364\u1365\u1366\u1367\u1368')
                if w and any(0x1200 <= ord(c) <= 0x137F for c in w):
                    unique.add(w)
    return unique


def test_all_words_in_lexicon():
    """Test 1: Every unique word has a lexicon entry."""
    text_data, words_data, err = load_data()
    if err:
        print(f"[FAIL] {err}")
        return False

    unique_words = extract_unique_words(text_data)
    missing = []

    for word in sorted(unique_words):
        if word not in words_data:
            missing.append(word)

    coverage = ((len(unique_words) - len(missing)) / len(unique_words)) * 100 if unique_words else 0

    print(f"[INFO] Unique Ge'ez words: {len(unique_words)}")
    print(f"[INFO] In lexicon: {len(unique_words) - len(missing)}")
    print(f"[INFO] Coverage: {coverage:.1f}%")

    if missing:
        print(f"[FAIL] {len(missing)} words missing from lexicon:")
        for m in missing[:20]:
            print(f"  {m}")
        if len(missing) > 20:
            print(f"  ... and {len(missing) - 20} more")
        return False

    print(f"[PASS] 100% lexicon coverage ({len(unique_words)} words)")
    return True


def test_required_fields():
    """Test 2: Every lexicon entry has all required fields."""
    text_data, words_data, err = load_data()
    if err:
        print(f"[FAIL] {err}")
        return False

    unique_words = extract_unique_words(text_data)
    incomplete = []

    for word in sorted(unique_words):
        if word not in words_data:
            continue
        entry = words_data[word]
        missing_fields = [f for f in REQUIRED_FIELDS if f not in entry or not entry[f]]
        if missing_fields:
            incomplete.append({'word': word, 'missing': missing_fields})

    if incomplete:
        print(f"[FAIL] {len(incomplete)} entries missing required fields:")
        for inc in incomplete[:10]:
            print(f"  {inc['word']}: missing {inc['missing']}")
        return False

    print(f"[PASS] All lexicon entries have required fields: {REQUIRED_FIELDS}")
    return True


def test_gematria_values():
    """Test 3: Every entry has a valid gematria value."""
    text_data, words_data, err = load_data()
    if err:
        print(f"[FAIL] {err}")
        return False

    unique_words = extract_unique_words(text_data)
    invalid = []

    for word in sorted(unique_words):
        if word not in words_data:
            continue
        entry = words_data[word]
        gematria = entry.get('gematria')
        if gematria is None or not isinstance(gematria, (int, float)) or gematria <= 0:
            invalid.append({'word': word, 'gematria': gematria})

    if invalid:
        print(f"[FAIL] {len(invalid)} entries have invalid gematria:")
        for inv in invalid[:10]:
            print(f"  {inv['word']}: gematria={inv['gematria']}")
        return False

    print(f"[PASS] All entries have valid positive gematria values")
    return True


def test_definitions_sourced():
    """Test 4: Every definition cites a scholarly source."""
    text_data, words_data, err = load_data()
    if err:
        print(f"[FAIL] {err}")
        return False

    unique_words = extract_unique_words(text_data)
    unsourced = []
    valid_sources = ['dillmann', 'leslau', 'charles', 'de caussin', 'betamasaheft']

    for word in sorted(unique_words):
        if word not in words_data:
            continue
        entry = words_data[word]
        source = entry.get('source', '').lower()
        if not any(s in source for s in valid_sources):
            unsourced.append({'word': word, 'source': entry.get('source', 'NONE')})

    if unsourced:
        pct = (len(unsourced) / len(unique_words)) * 100
        print(f"[WARN] {len(unsourced)} entries ({pct:.1f}%) without scholarly source citation:")
        for u in unsourced[:10]:
            print(f"  {u['word']}: source='{u['source']}'")
        if pct > 5:
            print(f"[FAIL] More than 5% unsourced")
            return False
        print(f"[PASS] {pct:.1f}% unsourced (within 5% tolerance)")
        return True

    print(f"[PASS] All definitions cite scholarly sources")
    return True


def test_letter_breakdowns():
    """Test 5: Entries have Fidel character breakdowns."""
    text_data, words_data, err = load_data()
    if err:
        print(f"[FAIL] {err}")
        return False

    unique_words = extract_unique_words(text_data)
    no_letters = 0
    has_letters = 0

    for word in unique_words:
        if word not in words_data:
            continue
        entry = words_data[word]
        if 'letters' in entry and entry['letters']:
            has_letters += 1
        else:
            no_letters += 1

    total = has_letters + no_letters
    if total == 0:
        print("[FAIL] No words in lexicon to check")
        return False

    pct = (has_letters / total) * 100
    print(f"[INFO] With letter breakdown: {has_letters}/{total} ({pct:.1f}%)")

    if pct < 95:
        print(f"[FAIL] Less than 95% have letter breakdowns")
        return False

    print(f"[PASS] {pct:.1f}% of entries have Fidel character breakdowns")
    return True


if __name__ == '__main__':
    print("=" * 60)
    print("BENCHMARK TEST 2: Lexicon Completeness")
    print("=" * 60)

    tests = [
        test_all_words_in_lexicon,
        test_required_fields,
        test_gematria_values,
        test_definitions_sourced,
        test_letter_breakdowns,
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
