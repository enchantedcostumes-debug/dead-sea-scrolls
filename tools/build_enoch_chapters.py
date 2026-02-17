#!/usr/bin/env python3
"""
Build 1 Enoch Chapter HTML Files (Chapters 1-36: Book of the Watchers)
======================================================================
Reads data/enoch_geez_text.json and generates:
- 1_enoch/1.html through 1_enoch/36.html (chapter pages)
- 1_enoch/index.html (chapter listing)

Follows the EXACT pattern from mechanical-bible genesis/1.html
adapted for Ge'ez (Ethiopic) script.

Copyright (c) 2026 Tammy L Casey. All rights reserved.
"""

import json
import os
import re
import sys
import html as html_mod

# ============================================================================
# CONFIGURATION
# ============================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.join(SCRIPT_DIR, '..')
DATA_FILE = os.path.join(PROJECT_ROOT, 'data', 'enoch_geez_text.json')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, '1_enoch')
TOTAL_CHAPTERS = 36

# ============================================================================
# GE'EZ GEMATRIA TABLE
# ============================================================================
# Base consonants and their traditional Ethiopic numeral values.
# All vowel orders (1st-7th) for each consonant share the same value.
# Each Ethiopic syllable block = base + 0..6 for the 7 vowel orders.

GEEZ_BASE_VALUES = {
    0x1200: 1,   # ha (ha-hu-hi-ha-he-h-ho)
    0x1208: 2,   # la
    0x1210: 3,   # hha (pharyngeal)
    0x1218: 4,   # ma
    0x1220: 5,   # sza (archaic)
    0x1228: 6,   # ra
    0x1230: 7,   # sa
    0x1238: 7,   # sha (same value as sa)
    0x1240: 8,   # qa
    0x1248: 8,   # qwa (labio-velar, same base as qa)
    0x1250: 9,   # ba (some systems use different, but standard = 9)
    0x1258: 9,   # bwa
    0x1260: 10,  # ta (some list as va/beta)
    0x1268: 10,  # twa
    0x1270: 10,  # ta
    0x1278: 11,  # ca (cha)
    0x1280: 11,  # xa (pharyngeal h)
    0x1288: 11,  # xwa
    0x1290: 12,  # na
    0x1298: 12,  # nya
    0x12A0: 13,  # 'a (glottal)
    0x12A8: 14,  # ka
    0x12B0: 14,  # kwa
    0x12B8: 14,  # kxwa
    0x12C0: 14,  # kxwa variant
    0x12C8: 15,  # wa
    0x12D0: 16,  # 'ayin
    0x12D8: 17,  # za
    0x12E0: 17,  # zha
    0x12E8: 18,  # ya
    0x12F0: 19,  # da
    0x12F8: 19,  # dda
    0x1300: 20,  # ga (ja)
    0x1308: 20,  # ga
    0x1310: 20,  # gwa
    0x1318: 20,  # ggwa
    0x1320: 21,  # tha (emphatic t)
    0x1328: 22,  # pha (emphatic p)
    0x1330: 23,  # tsa (emphatic ts)
    0x1338: 24,  # tsa' (another emphatic)
    0x1340: 25,  # fa
    0x1348: 26,  # pa
}


def geez_char_value(char):
    """Get gematria value for a single Ge'ez character."""
    code = ord(char)
    # Check if in Ethiopic range
    if 0x1200 <= code <= 0x137F:
        # Find the base consonant (each has 8 slots for vowel orders)
        base = (code // 8) * 8
        return GEEZ_BASE_VALUES.get(base, 0)
    return 0


def verse_gematria(text):
    """Calculate gematria for a verse of Ge'ez text."""
    total = 0
    for char in text:
        total += geez_char_value(char)
    return total


# ============================================================================
# WORD SPLITTING
# ============================================================================

# Ethiopic punctuation to strip from onclick parameter
ETHIOPIC_PUNCT = set('\u1361\u1362\u1363\u1364\u1365\u1366\u1367\u1368')
# U+1361 = Ethiopic Wordspace
# U+1362 = Ethiopic Full Stop
# U+1363-U+1368 = various Ethiopic punctuation


def split_geez_words(text):
    """Split Ge'ez text into words by Ethiopic wordspace and regular spaces.

    Returns list of (display_word, clean_word) tuples.
    display_word = what shows in the HTML (may include punctuation)
    clean_word = what goes into showWordEvolution() (stripped of punctuation)
    """
    if not text or not text.strip():
        return []

    # Split on spaces and Ethiopic wordspace
    raw_tokens = re.split(r'[\s\u1361]+', text.strip())
    words = []
    for token in raw_tokens:
        if not token:
            continue
        # Check if token has any Ethiopic characters
        has_ethiopic = any(0x1200 <= ord(c) <= 0x137F for c in token)
        if not has_ethiopic:
            continue
        display = token
        # Strip Ethiopic punctuation for the onclick param
        clean = ''.join(c for c in token if c not in ETHIOPIC_PUNCT)
        if clean:
            words.append((display, clean))
    return words


# ============================================================================
# HTML GENERATION
# ============================================================================

def build_chapter_nav(total_chapters, current_chapter):
    """Build chapter nav bar like genesis pattern."""
    parts = []
    for ch in range(1, total_chapters + 1):
        if ch == current_chapter:
            parts.append(f'<a href="{ch}.html" class="active">{ch}</a>')
        else:
            parts.append(f'<a href="{ch}.html">{ch}</a>')
    return '<div class="chapter-nav">' + ''.join(parts) + '</div>'


def build_verse_html(chapter_num, verse_num, geez_text, english_text):
    """Build HTML for a single verse following the mechanical-bible pattern."""
    gematria = verse_gematria(geez_text)
    words = split_geez_words(geez_text)

    # Build clickable word spans
    word_spans = []
    for display_word, clean_word in words:
        escaped_clean = html_mod.escape(clean_word, quote=True)
        escaped_display = html_mod.escape(display_word)
        span = (
            f'<span class="word" lang="gez" translate="no" '
            f"onclick=\"showWordEvolution('{escaped_clean}')\">"
            f'{escaped_display}</span>'
        )
        word_spans.append(span)

    words_html = ' '.join(word_spans)
    escaped_english = html_mod.escape(english_text) if english_text else ''

    return f"""            <div class="verse-block">
                <div class="verse-ref">
                    <span class="verse-number">{chapter_num}:{verse_num}</span>
                    <span class="verse-gematria" title="Verse Gematria">G: {gematria}</span>
                </div>
                <div class="original-text geez" lang="gez" translate="no">{words_html}</div>
                <div class="translation">{escaped_english}</div>
            </div>"""


def build_chapter_html(chapter_num, chapter_data):
    """Build a complete chapter HTML page."""
    verses_html_parts = []
    verses = chapter_data.get('verses', {})

    # Sort verses numerically
    for v_num in sorted(verses.keys(), key=lambda x: int(x)):
        v_data = verses[v_num]
        geez_text = v_data.get('geez', '')
        english_text = v_data.get('english', '')
        verses_html_parts.append(
            build_verse_html(chapter_num, v_num, geez_text, english_text)
        )

    verses_html = '\n'.join(verses_html_parts)

    # Navigation links
    nav_prev = ''
    nav_next = ''
    if chapter_num > 1:
        nav_prev = f'<a href="{chapter_num - 1}.html">&larr; Chapter {chapter_num - 1}</a>'
    if chapter_num < TOTAL_CHAPTERS:
        nav_next = f'<a href="{chapter_num + 1}.html">Chapter {chapter_num + 1} &rarr;</a>'

    chapter_nav = build_chapter_nav(TOTAL_CHAPTERS, chapter_num)

    return f"""<!DOCTYPE html>
<html lang="en" translate="no">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="google" content="notranslate">
    <meta http-equiv="Content-Language" content="en">
    <title>1 Enoch {chapter_num} - Dead Sea Scrolls Mechanical Translation</title>
    <link rel="stylesheet" href="../css/ethiopic-theme.css">
    <link rel="stylesheet" href="../css/word-modal.css">
</head>
<body>
<div class="container">
        <h1>1 Enoch</h1>
        <p class="subtitle">Chapter {chapter_num}</p>
        <nav>
            <a href="../index.html">Home</a>
            <a href="index.html">Chapters</a>
        </nav>
        {chapter_nav}
        <div class="view-toolbar">
            <button id="interlinear-toggle" onclick="toggleInterlinear()">Interlinear View</button>
        </div>
{verses_html}
        <div class="page-nav">{nav_prev}<a href="index.html">All Chapters</a>{nav_next}</div>
</div>
<script>
document.addEventListener('keydown', function(e) {{
    if (e.key === 'Escape') closeModal();
}});
</script>
    <script src="../js/word-modal.js"></script>
    <script src="../js/interlinear.js"></script>
</body>
</html>"""


def build_index_html():
    """Build the chapter listing index page."""
    links = []
    for ch in range(1, TOTAL_CHAPTERS + 1):
        links.append(f'<a href="{ch}.html">{ch}</a>')
    chapter_nav = '<div class="chapter-nav">' + ''.join(links) + '</div>'

    return f"""<!DOCTYPE html>
<html lang="en" translate="no">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="google" content="notranslate">
    <meta http-equiv="Content-Language" content="en">
    <title>1 Enoch - Dead Sea Scrolls Mechanical Translation</title>
    <link rel="stylesheet" href="../css/ethiopic-theme.css">
    <link rel="stylesheet" href="../css/word-modal.css">
</head>
<body>
<div class="container">
        <h1>1 Enoch</h1>
        <p class="subtitle">Book of the Watchers - Select a Chapter</p>
        <nav><a href="../index.html">Home</a></nav>
        {chapter_nav}
</div>
</body>
</html>"""


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 60)
    print("BUILD: 1 Enoch Chapter HTML Files (1-36)")
    print("=" * 60)
    print()

    # Check data file
    if not os.path.exists(DATA_FILE):
        print(f"[FAIL] Data file not found: {DATA_FILE}")
        print("[INFO] Please create data/enoch_geez_text.json first.")
        print("[INFO] Expected format:")
        print('  {"1": {"verses": {"1": {"geez": "...", "english": "..."}, ...}}, ...}')
        sys.exit(1)

    # Load data
    print(f"[INFO] Loading: {DATA_FILE}")
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    chapter_count = len(data)
    print(f"[OK] Loaded {chapter_count} chapters")

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"[OK] Output directory: {OUTPUT_DIR}")
    print()

    # Generate chapter files
    total_verses = 0
    total_words = 0
    generated = 0

    for ch_num in range(1, TOTAL_CHAPTERS + 1):
        ch_key = str(ch_num)
        if ch_key not in data:
            print(f"[WARN] Chapter {ch_num} not found in data - skipping")
            continue

        ch_data = data[ch_key]
        verses = ch_data.get('verses', {})
        v_count = len(verses)
        total_verses += v_count

        # Count words
        for v in verses.values():
            geez = v.get('geez', '')
            words = split_geez_words(geez)
            total_words += len(words)

        # Generate HTML
        chapter_html = build_chapter_html(ch_num, ch_data)
        out_path = os.path.join(OUTPUT_DIR, f'{ch_num}.html')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(chapter_html)

        generated += 1
        print(f"  [OK] Chapter {ch_num:2d} - {v_count:3d} verses -> {ch_num}.html")

    print()

    # Generate index
    index_html = build_index_html()
    index_path = os.path.join(OUTPUT_DIR, 'index.html')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_html)
    print(f"[OK] Index page -> index.html")

    # Summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Chapters generated: {generated}/{TOTAL_CHAPTERS}")
    print(f"  Total verses:       {total_verses}")
    print(f"  Total Ge'ez words:  {total_words}")
    print(f"  Index page:         1_enoch/index.html")
    print(f"  Chapter pages:      1_enoch/1.html - 1_enoch/{generated}.html")
    print()

    if generated == TOTAL_CHAPTERS:
        print(f"[OK] ALL {TOTAL_CHAPTERS} CHAPTERS GENERATED SUCCESSFULLY")
    else:
        print(f"[WARN] Only {generated}/{TOTAL_CHAPTERS} chapters generated")
        print("[INFO] Missing chapters need data in enoch_geez_text.json")

    return generated


if __name__ == '__main__':
    main()
