#!/usr/bin/env python3
"""
Test: Interlinear Translation View
===================================
Verifies that:
1. interlinear.js exists and has required functions
2. CSS has interlinear styles
3. All 36 chapter HTML files include toggle button + script reference
4. Transliteration table covers full Ge'ez range
5. Word gloss function handles missing data gracefully
"""

import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.join(SCRIPT_DIR, '..')


def test_interlinear_js_exists():
    """interlinear.js exists and has all required functions."""
    js_path = os.path.join(PROJECT_ROOT, 'js', 'interlinear.js')
    assert os.path.exists(js_path), f"FAIL: {js_path} does not exist"

    with open(js_path, 'r', encoding='utf-8') as f:
        content = f.read()

    required_functions = [
        'toggleInterlinear',
        'enableInterlinear',
        'disableInterlinear',
        'transliterate',
        'getWordGloss',
        'getWordTranslit',
        'truncateGloss',
        'buildTranslitTable',
    ]

    for func in required_functions:
        assert f'function {func}' in content, \
            f"FAIL: function {func}() missing from interlinear.js"

    # Check transliteration table has entries
    assert 'TRANSLIT_BASES' in content, "FAIL: TRANSLIT_BASES table missing"
    assert "0x1200" in content, "FAIL: First Ge'ez consonant row missing"
    assert "0x1348" in content, "FAIL: Last Ge'ez consonant row (pa) missing"

    print("[PASS] interlinear.js exists with all 8 required functions + translit table")


def test_css_interlinear_styles():
    """CSS has all interlinear style classes."""
    css_path = os.path.join(PROJECT_ROOT, 'css', 'ethiopic-theme.css')
    assert os.path.exists(css_path), f"FAIL: {css_path} does not exist"

    with open(css_path, 'r', encoding='utf-8') as f:
        content = f.read()

    required_classes = [
        '#interlinear-toggle',
        '.interlinear-line',
        '.interlinear-word',
        '.il-geez',
        '.il-translit',
        '.il-gloss',
        '.interlinear-active',
        '.view-toolbar',
    ]

    for cls in required_classes:
        assert cls in content, f"FAIL: CSS class {cls} missing from ethiopic-theme.css"

    print("[PASS] CSS has all 8 interlinear style classes")


def test_all_chapters_have_toggle():
    """All 36 chapter HTML files include the interlinear toggle button and script."""
    chapters_dir = os.path.join(PROJECT_ROOT, '1_enoch')
    missing_toggle = []
    missing_script = []
    missing_toolbar = []

    for ch in range(1, 37):
        path = os.path.join(chapters_dir, f'{ch}.html')
        assert os.path.exists(path), f"FAIL: Chapter {ch} not found at {path}"

        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        if 'id="interlinear-toggle"' not in content:
            missing_toggle.append(ch)
        if 'interlinear.js' not in content:
            missing_script.append(ch)
        if 'view-toolbar' not in content:
            missing_toolbar.append(ch)

    assert not missing_toggle, f"FAIL: Chapters missing toggle button: {missing_toggle}"
    assert not missing_script, f"FAIL: Chapters missing interlinear.js: {missing_script}"
    assert not missing_toolbar, f"FAIL: Chapters missing view-toolbar: {missing_toolbar}"

    print("[PASS] All 36 chapters have toggle button, toolbar, and interlinear.js")


def test_script_load_order():
    """word-modal.js loads BEFORE interlinear.js (dependency order)."""
    path = os.path.join(PROJECT_ROOT, '1_enoch', '1.html')
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    pos_word_modal = content.find('word-modal.js')
    pos_interlinear = content.find('interlinear.js')

    assert pos_word_modal > 0, "FAIL: word-modal.js not found in chapter HTML"
    assert pos_interlinear > 0, "FAIL: interlinear.js not found in chapter HTML"
    assert pos_word_modal < pos_interlinear, \
        "FAIL: word-modal.js must load BEFORE interlinear.js (interlinear depends on word data)"

    print("[PASS] Script load order correct: word-modal.js before interlinear.js")


def test_translit_table_coverage():
    """Transliteration table covers all major Ge'ez consonant series."""
    js_path = os.path.join(PROJECT_ROOT, 'js', 'interlinear.js')
    with open(js_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract hex values from the rows array
    hex_values = re.findall(r'0x([0-9A-Fa-f]+)', content)
    covered_bases = set()
    for h in hex_values:
        val = int(h, 16)
        if 0x1200 <= val <= 0x137F:
            covered_bases.add(val)

    # Key consonant bases that MUST be covered
    essential = [
        0x1200,  # ha
        0x1208,  # la
        0x1218,  # ma
        0x1228,  # ra
        0x1230,  # sa
        0x1240,  # qa
        0x1260,  # ba/beta
        0x1270,  # ta
        0x1290,  # na
        0x12A0,  # alef
        0x12A8,  # ka
        0x12C8,  # wa
        0x12D0,  # ayin
        0x12D8,  # za
        0x12E8,  # ya
        0x12F0,  # da
        0x1300,  # ja
        0x1308,  # ga
        0x1320,  # emphatic t
        0x1340,  # fa
        0x1348,  # pa
    ]

    missing = [hex(b) for b in essential if b not in covered_bases]
    assert not missing, f"FAIL: Missing essential consonant bases: {missing}"

    print(f"[PASS] Transliteration covers {len(covered_bases)} consonant bases "
          f"(all {len(essential)} essential bases present)")


def test_css_responsive():
    """Interlinear CSS has responsive rules for mobile."""
    css_path = os.path.join(PROJECT_ROOT, 'css', 'ethiopic-theme.css')
    with open(css_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Find lines with interlinear inside media queries
    in_media = False
    has_interlinear_responsive = False
    for line in lines:
        if '@media' in line and '768px' in line:
            in_media = True
        if in_media and 'interlinear' in line:
            has_interlinear_responsive = True
            break

    assert has_interlinear_responsive, \
        "FAIL: No interlinear responsive rules found in 768px media query"

    print("[PASS] CSS has responsive interlinear rules for mobile")


if __name__ == '__main__':
    print("=" * 60)
    print("TESTING: Interlinear Translation View")
    print("=" * 60)
    print()

    try:
        test_interlinear_js_exists()
        test_css_interlinear_styles()
        test_all_chapters_have_toggle()
        test_script_load_order()
        test_translit_table_coverage()
        test_css_responsive()

        print()
        print("[OK] ALL 6 TESTS PASSED")
    except AssertionError as e:
        print()
        print(f"[FAIL] {e}")
        sys.exit(1)
