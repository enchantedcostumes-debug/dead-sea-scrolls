#!/usr/bin/env python3
"""
Test: Leslau Dictionary Enrichment (Phase 3)
=============================================
Verifies that:
1. words.json has enriched fields (english_definition, part_of_speech, semantic_domain)
2. Coverage meets thresholds (>90% for each field)
3. Domain distribution is reasonable (no single domain > 60%)
4. Word modal JS displays enriched fields
5. Interlinear JS prefers english_definition for gloss
6. CSS has styles for new enriched elements

Copyright (c) 2026 Tammy L Casey. All rights reserved.
"""

import json
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.join(SCRIPT_DIR, '..')


def test_enriched_fields_exist():
    """words.json has english_definition, part_of_speech, semantic_domain fields."""
    words_path = os.path.join(PROJECT_ROOT, 'words.json')
    assert os.path.exists(words_path), f"FAIL: {words_path} not found"

    with open(words_path, 'r', encoding='utf-8') as f:
        words = json.load(f)

    total = len(words)
    has_english = sum(1 for w in words.values() if w.get('english_definition'))
    has_pos = sum(1 for w in words.values() if w.get('part_of_speech'))
    has_domain = sum(1 for w in words.values()
                     if w.get('semantic_domain') and w.get('semantic_domain') != 'unclassified')

    assert has_english > 0, "FAIL: No words have english_definition"
    assert has_pos > 0, "FAIL: No words have part_of_speech"
    assert has_domain > 0, "FAIL: No words have semantic_domain"

    print(f"[PASS] Enriched fields exist: english_def={has_english}/{total}, "
          f"pos={has_pos}/{total}, domain={has_domain}/{total}")


def test_coverage_thresholds():
    """Coverage exceeds 90% for all enriched fields."""
    words_path = os.path.join(PROJECT_ROOT, 'words.json')
    with open(words_path, 'r', encoding='utf-8') as f:
        words = json.load(f)

    total = len(words)
    has_english = sum(1 for w in words.values() if w.get('english_definition'))
    has_pos = sum(1 for w in words.values() if w.get('part_of_speech'))
    has_domain = sum(1 for w in words.values()
                     if w.get('semantic_domain') and w.get('semantic_domain') != 'unclassified')

    eng_pct = has_english / total * 100
    pos_pct = has_pos / total * 100
    dom_pct = has_domain / total * 100

    assert eng_pct >= 90, f"FAIL: english_definition coverage {eng_pct:.1f}% < 90%"
    assert pos_pct >= 90, f"FAIL: part_of_speech coverage {pos_pct:.1f}% < 90%"
    assert dom_pct >= 90, f"FAIL: semantic_domain coverage {dom_pct:.1f}% < 90%"

    print(f"[PASS] Coverage thresholds met: english={eng_pct:.1f}%, "
          f"pos={pos_pct:.1f}%, domain={dom_pct:.1f}%")


def test_domain_distribution():
    """Domain distribution is reasonable (no single domain > 60%)."""
    words_path = os.path.join(PROJECT_ROOT, 'words.json')
    with open(words_path, 'r', encoding='utf-8') as f:
        words = json.load(f)

    domains = {}
    for w in words.values():
        d = w.get('semantic_domain', 'unclassified')
        domains[d] = domains.get(d, 0) + 1

    total = len(words)
    for domain, count in domains.items():
        pct = count / total * 100
        assert pct <= 60, \
            f"FAIL: Domain '{domain}' has {pct:.1f}% - exceeds 60% limit"

    # Verify at least 5 distinct domains
    non_empty = [d for d, c in domains.items() if c > 0 and d != 'unclassified']
    assert len(non_empty) >= 5, \
        f"FAIL: Only {len(non_empty)} domains - need at least 5"

    print(f"[PASS] Domain distribution reasonable: {len(non_empty)} domains, "
          f"largest = {max(domains.values())}/{total} "
          f"({max(domains.values())/total*100:.1f}%)")


def test_word_modal_displays_enriched():
    """word-modal.js has code to display english_definition, POS badge, domain badge."""
    js_path = os.path.join(PROJECT_ROOT, 'js', 'word-modal.js')
    assert os.path.exists(js_path), f"FAIL: {js_path} not found"

    with open(js_path, 'r', encoding='utf-8') as f:
        content = f.read()

    assert 'english_definition' in content, \
        "FAIL: word-modal.js does not reference english_definition"
    assert 'part_of_speech' in content, \
        "FAIL: word-modal.js does not reference part_of_speech"
    assert 'semantic_domain' in content, \
        "FAIL: word-modal.js does not reference semantic_domain"
    assert 'word-pos-badge' in content, \
        "FAIL: word-modal.js missing POS badge class"
    assert 'word-domain-badge' in content, \
        "FAIL: word-modal.js missing domain badge class"
    assert 'word-english-def' in content, \
        "FAIL: word-modal.js missing english definition display"

    print("[PASS] word-modal.js displays enriched fields (english_def, POS badge, domain badge)")


def test_interlinear_prefers_english_def():
    """interlinear.js prefers english_definition over raw definition for gloss."""
    js_path = os.path.join(PROJECT_ROOT, 'js', 'interlinear.js')
    assert os.path.exists(js_path), f"FAIL: {js_path} not found"

    with open(js_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # The getWordGloss function should check english_definition first
    assert 'english_definition' in content, \
        "FAIL: interlinear.js does not reference english_definition"

    # Find the getWordGloss function and check priority order
    gloss_match = re.search(r'function getWordGloss.*?return.*?---', content, re.DOTALL)
    assert gloss_match, "FAIL: getWordGloss function not found"

    gloss_body = gloss_match.group()
    eng_pos = gloss_body.find('english_definition')
    def_pos = gloss_body.find('.definition')
    assert eng_pos < def_pos, \
        "FAIL: english_definition should be checked BEFORE .definition in getWordGloss"

    print("[PASS] interlinear.js prefers english_definition for gloss")


def test_css_enriched_styles():
    """CSS has styles for new enriched elements."""
    css_path = os.path.join(PROJECT_ROOT, 'css', 'word-modal.css')
    assert os.path.exists(css_path), f"FAIL: {css_path} not found"

    with open(css_path, 'r', encoding='utf-8') as f:
        content = f.read()

    required = [
        '.word-pos-badge',
        '.word-domain-badge',
        '.word-english-section',
        '.word-english-def',
        '.word-badges',
    ]

    for cls in required:
        assert cls in content, f"FAIL: CSS class {cls} missing from word-modal.css"

    print(f"[PASS] CSS has all {len(required)} enriched element styles")


if __name__ == '__main__':
    print("=" * 60)
    print("TESTING: Leslau Dictionary Enrichment (Phase 3)")
    print("=" * 60)
    print()

    try:
        test_enriched_fields_exist()
        test_coverage_thresholds()
        test_domain_distribution()
        test_word_modal_displays_enriched()
        test_interlinear_prefers_english_def()
        test_css_enriched_styles()

        print()
        print("[OK] ALL 6 TESTS PASSED")
    except AssertionError as e:
        print()
        print(f"[FAIL] {e}")
        sys.exit(1)
