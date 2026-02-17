#!/usr/bin/env python3
"""
Build Cognate Data: Hebrew and Arabic cognates for Ge'ez words
===============================================================
Adds structured hebrew_cognate and arabic_cognate fields to words.json.
Sources:
1. Parse existing cognates_english field (free-text Heb/Ar references)
2. Known Semitic cognate pairs from comparative linguistics
3. Leslau CDG, Dillmann, and standard reference cognate data

Copyright (c) 2026 Tammy L Casey. All rights reserved.
"""

import json
import os
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.join(SCRIPT_DIR, '..')
WORDS_FILE = os.path.join(PROJECT_ROOT, 'words.json')

# ============================================================================
# KNOWN SEMITIC COGNATE PAIRS
# ============================================================================
# Key: Ge'ez root/word pattern -> Hebrew cognate, Arabic cognate
# Based on Leslau CDG and standard Semitic comparative linguistics
#
# Format: { definition_keyword: { hebrew: (word, translit, meaning),
#                                  arabic: (word, translit, meaning) } }

SEMITIC_COGNATES = {
    # Divine/Religious
    'god': {
        'hebrew': ('\u05D0\u05DC\u05D5\u05D4\u05D9\u05DD', 'elohim', 'God'),
        'arabic': ('\u0627\u0644\u0644\u0647', 'allah', 'God'),
    },
    'lord': {
        'hebrew': ('\u05D0\u05D3\u05D5\u05DF', 'adon', 'lord, master'),
        'arabic': ('\u0633\u064A\u062F', 'sayyid', 'lord, master'),
    },
    'holy': {
        'hebrew': ('\u05E7\u05D3\u05D5\u05E9', 'qadosh', 'holy'),
        'arabic': ('\u0642\u062F\u0633', 'quds', 'holy'),
    },
    'bless': {
        'hebrew': ('\u05D1\u05E8\u05DA', 'barakh', 'to bless'),
        'arabic': ('\u0628\u0627\u0631\u0643', 'baraka', 'to bless'),
    },
    'prayer': {
        'hebrew': ('\u05EA\u05E4\u05D9\u05DC\u05D4', 'tefillah', 'prayer'),
        'arabic': ('\u0635\u0644\u0627\u0629', 'salat', 'prayer'),
    },
    'righteous': {
        'hebrew': ('\u05E6\u05D3\u05D9\u05E7', 'tsaddiq', 'righteous'),
        'arabic': ('\u0635\u062F\u0642', 'sidq', 'truth, righteousness'),
    },
    'sin': {
        'hebrew': ('\u05D7\u05D8\u05D0', 'het', 'sin'),
        'arabic': ('\u062E\u0637\u0627', "khata'", 'sin, error'),
    },
    'glory': {
        'hebrew': ('\u05DB\u05D1\u05D5\u05D3', 'kavod', 'glory'),
        'arabic': ('\u0645\u062C\u062F', 'majd', 'glory'),
    },
    'peace': {
        'hebrew': ('\u05E9\u05DC\u05D5\u05DD', 'shalom', 'peace'),
        'arabic': ('\u0633\u0644\u0627\u0645', 'salam', 'peace'),
    },
    'covenant': {
        'hebrew': ('\u05D1\u05E8\u05D9\u05EA', 'berit', 'covenant'),
        'arabic': ('\u0639\u0647\u062F', "'ahd", 'covenant, pact'),
    },
    'judgment': {
        'hebrew': ('\u05DE\u05E9\u05E4\u05D8', 'mishpat', 'judgment'),
        'arabic': ('\u062D\u0643\u0645', 'hukm', 'judgment'),
    },
    'mercy': {
        'hebrew': ('\u05E8\u05D7\u05DE\u05D9\u05DD', 'rachamim', 'mercy'),
        'arabic': ('\u0631\u062D\u0645\u0629', 'rahma', 'mercy'),
    },
    'oath': {
        'hebrew': ('\u05E9\u05D1\u05D5\u05E2\u05D4', "shevu'ah", 'oath'),
        'arabic': ('\u0642\u0633\u0645', 'qasam', 'oath'),
    },
    'spirit': {
        'hebrew': ('\u05E8\u05D5\u05D7', 'ruach', 'spirit, wind'),
        'arabic': ('\u0631\u0648\u062D', 'ruh', 'spirit'),
    },
    'soul': {
        'hebrew': ('\u05E0\u05E4\u05E9', 'nefesh', 'soul'),
        'arabic': ('\u0646\u0641\u0633', 'nafs', 'soul, self'),
    },

    # Nature
    'heaven': {
        'hebrew': ('\u05E9\u05DE\u05D9\u05DD', 'shamayim', 'heaven, sky'),
        'arabic': ('\u0633\u0645\u0627\u0621', "sama'", 'sky, heaven'),
    },
    'earth': {
        'hebrew': ('\u05D0\u05E8\u05E5', 'erets', 'earth, land'),
        'arabic': ('\u0623\u0631\u0636', 'ard', 'earth, land'),
    },
    'mountain': {
        'hebrew': ('\u05D4\u05E8', 'har', 'mountain'),
        'arabic': ('\u062C\u0628\u0644', 'jabal', 'mountain'),
    },
    'water': {
        'hebrew': ('\u05DE\u05D9\u05DD', 'mayim', 'water'),
        'arabic': ('\u0645\u0627\u0621', "ma'", 'water'),
    },
    'sea': {
        'hebrew': ('\u05D9\u05DD', 'yam', 'sea'),
        'arabic': ('\u064A\u0645', 'yamm', 'sea'),
    },
    'star': {
        'hebrew': ('\u05DB\u05D5\u05DB\u05D1', 'kokhav', 'star'),
        'arabic': ('\u0643\u0648\u0643\u0628', 'kawkab', 'star, planet'),
    },
    'sun': {
        'hebrew': ('\u05E9\u05DE\u05E9', 'shemesh', 'sun'),
        'arabic': ('\u0634\u0645\u0633', 'shams', 'sun'),
    },
    'moon': {
        'hebrew': ('\u05D9\u05E8\u05D7', 'yareach', 'moon'),
        'arabic': ('\u0642\u0645\u0631', 'qamar', 'moon'),
    },
    'fire': {
        'hebrew': ('\u05D0\u05E9', 'esh', 'fire'),
        'arabic': ('\u0646\u0627\u0631', 'nar', 'fire'),
    },
    'light': {
        'hebrew': ('\u05D0\u05D5\u05E8', 'or', 'light'),
        'arabic': ('\u0646\u0648\u0631', 'nur', 'light'),
    },
    'tree': {
        'hebrew': ('\u05E2\u05E5', 'ets', 'tree'),
        'arabic': ('\u0634\u062C\u0631\u0629', 'shajara', 'tree'),
    },
    'stone': {
        'hebrew': ('\u05D0\u05D1\u05DF', 'even', 'stone'),
        'arabic': ('\u062D\u062C\u0631', 'hajar', 'stone'),
    },
    'iron': {
        'hebrew': ('\u05D1\u05E8\u05D6\u05DC', 'barzel', 'iron'),
        'arabic': ('\u062D\u062F\u064A\u062F', 'hadid', 'iron'),
    },
    'gold': {
        'hebrew': ('\u05D6\u05D4\u05D1', 'zahav', 'gold'),
        'arabic': ('\u0630\u0647\u0628', 'dhahab', 'gold'),
    },
    'silver': {
        'hebrew': ('\u05DB\u05E1\u05E3', 'kesef', 'silver'),
        'arabic': ('\u0641\u0636\u0629', 'fidda', 'silver'),
    },
    'wind': {
        'hebrew': ('\u05E8\u05D5\u05D7', 'ruach', 'wind, spirit'),
        'arabic': ('\u0631\u064A\u062D', 'rih', 'wind'),
    },

    # People
    'son': {
        'hebrew': ('\u05D1\u05DF', 'ben', 'son'),
        'arabic': ('\u0627\u0628\u0646', 'ibn', 'son'),
    },
    'daughter': {
        'hebrew': ('\u05D1\u05EA', 'bat', 'daughter'),
        'arabic': ('\u0628\u0646\u062A', 'bint', 'daughter'),
    },
    'father': {
        'hebrew': ('\u05D0\u05D1', 'av', 'father'),
        'arabic': ('\u0623\u0628', 'ab', 'father'),
    },
    'mother': {
        'hebrew': ('\u05D0\u05DD', 'em', 'mother'),
        'arabic': ('\u0623\u0645', 'umm', 'mother'),
    },
    'king': {
        'hebrew': ('\u05DE\u05DC\u05DA', 'melekh', 'king'),
        'arabic': ('\u0645\u0644\u0643', 'malik', 'king'),
    },
    'man': {
        'hebrew': ('\u05D0\u05D9\u05E9', 'ish', 'man'),
        'arabic': ('\u0625\u0646\u0633\u0627\u0646', 'insan', 'human'),
    },
    'blood': {
        'hebrew': ('\u05D3\u05DD', 'dam', 'blood'),
        'arabic': ('\u062F\u0645', 'dam', 'blood'),
    },
    'flesh': {
        'hebrew': ('\u05D1\u05E9\u05E8', 'basar', 'flesh'),
        'arabic': ('\u0628\u0634\u0631', 'bashar', 'flesh, human'),
    },
    'name': {
        'hebrew': ('\u05E9\u05DD', 'shem', 'name'),
        'arabic': ('\u0627\u0633\u0645', 'ism', 'name'),
    },

    # Actions
    'come': {
        'hebrew': ('\u05D1\u05D5\u05D0', "bo'", 'to come'),
        'arabic': ('\u062C\u0627\u0621', "ja'a", 'to come'),
    },
    'see': {
        'hebrew': ('\u05E8\u05D0\u05D4', "ra'ah", 'to see'),
        'arabic': ('\u0631\u0623\u0649', "ra'a", 'to see'),
    },
    'know': {
        'hebrew': ('\u05D9\u05D3\u05E2', "yada'", 'to know'),
        'arabic': ('\u0639\u0631\u0641', "'arafa", 'to know'),
    },
    'speak': {
        'hebrew': ('\u05D3\u05D1\u05E8', 'davar', 'to speak'),
        'arabic': ('\u0643\u0644\u0645', 'kallama', 'to speak'),
    },
    'write': {
        'hebrew': ('\u05DB\u05EA\u05D1', 'katav', 'to write'),
        'arabic': ('\u0643\u062A\u0628', 'kataba', 'to write'),
    },
    'destroy': {
        'hebrew': ('\u05D7\u05E8\u05D1', 'charav', 'to destroy'),
        'arabic': ('\u062E\u0631\u0628', 'kharaba', 'to destroy'),
    },
    'eat': {
        'hebrew': ('\u05D0\u05DB\u05DC', 'akhal', 'to eat'),
        'arabic': ('\u0623\u0643\u0644', 'akala', 'to eat'),
    },

    # Temporal
    'day': {
        'hebrew': ('\u05D9\u05D5\u05DD', 'yom', 'day'),
        'arabic': ('\u064A\u0648\u0645', 'yawm', 'day'),
    },
    'night': {
        'hebrew': ('\u05DC\u05D9\u05DC\u05D4', 'laylah', 'night'),
        'arabic': ('\u0644\u064A\u0644', 'layl', 'night'),
    },
    'year': {
        'hebrew': ('\u05E9\u05E0\u05D4', 'shanah', 'year'),
        'arabic': ('\u0633\u0646\u0629', 'sana', 'year'),
    },

    # Angelic/Watchers specific
    'angel': {
        'hebrew': ('\u05DE\u05DC\u05D0\u05DA', "mal'akh", 'angel, messenger'),
        'arabic': ('\u0645\u0644\u0643', 'malak', 'angel'),
    },
    'watcher': {
        'hebrew': ('\u05E2\u05D9\u05E8', "'ir", 'watcher (Daniel 4:13)'),
        'arabic': None,
    },

    # Abstract
    'word': {
        'hebrew': ('\u05D3\u05D1\u05E8', 'davar', 'word, thing'),
        'arabic': ('\u0643\u0644\u0645\u0629', 'kalima', 'word'),
    },
    'wisdom': {
        'hebrew': ('\u05D7\u05DB\u05DE\u05D4', 'chokhmah', 'wisdom'),
        'arabic': ('\u062D\u0643\u0645\u0629', 'hikma', 'wisdom'),
    },
    'truth': {
        'hebrew': ('\u05D0\u05DE\u05EA', 'emet', 'truth'),
        'arabic': ('\u062D\u0642', 'haqq', 'truth'),
    },
    'secret': {
        'hebrew': ('\u05E1\u05D5\u05D3', 'sod', 'secret'),
        'arabic': ('\u0633\u0631', 'sirr', 'secret'),
    },
}


def parse_existing_cognates(cognates_str):
    """Parse existing cognates_english string for Hebrew/Arabic references."""
    if not cognates_str:
        return None, None

    hebrew = None
    arabic = None

    # Pattern: "Heb: word" or "Hebrew: word"
    heb_match = re.search(r'Heb(?:rew)?:\s*([^;,]+)', cognates_str)
    if heb_match:
        heb_text = heb_match.group(1).strip()
        # Extract transliteration
        hebrew = {'translit': heb_text, 'source': 'parsed'}

    # Pattern: "Ar: word" or "Arabic: word"
    ar_match = re.search(r'Ar(?:abic)?:\s*([^;,]+)', cognates_str)
    if ar_match:
        ar_text = ar_match.group(1).strip()
        arabic = {'translit': ar_text, 'source': 'parsed'}

    return hebrew, arabic


def find_cognate_by_definition(definition):
    """Match a word's definition against known cognate pairs."""
    if not definition:
        return None, None

    defn_lower = definition.lower()
    # Strip prefix meanings
    defn_lower = re.sub(
        r'^(and \+ |from \+ |in/by \+ |for/to \+ |of/which \+ |not \+ )',
        '', defn_lower
    )

    best_heb = None
    best_ar = None

    for keyword, cognates in SEMITIC_COGNATES.items():
        if keyword in defn_lower:
            heb = cognates.get('hebrew')
            ar = cognates.get('arabic')
            if heb and not best_heb:
                best_heb = {
                    'script': heb[0],
                    'translit': heb[1],
                    'meaning': heb[2],
                    'source': 'comparative'
                }
            if ar and not best_ar:
                best_ar = {
                    'script': ar[0],
                    'translit': ar[1],
                    'meaning': ar[2],
                    'source': 'comparative'
                }

    return best_heb, best_ar


def main():
    print("=" * 60)
    print("BUILD: Hebrew/Arabic Cognate Data")
    print("=" * 60)

    with open(WORDS_FILE, 'r', encoding='utf-8') as f:
        words = json.load(f)

    heb_added = 0
    ar_added = 0
    parsed_count = 0

    for word, info in words.items():
        defn = info.get('definition', '')
        existing_cognates = info.get('cognates_english', '')

        # Try parsing existing cognates first
        parsed_heb, parsed_ar = parse_existing_cognates(existing_cognates)

        # Then try definition-based matching
        def_heb, def_ar = find_cognate_by_definition(defn)

        # Also check english_definition
        eng_def = info.get('english_definition', '')
        if eng_def:
            eng_heb, eng_ar = find_cognate_by_definition(eng_def)
            if not def_heb:
                def_heb = eng_heb
            if not def_ar:
                def_ar = eng_ar

        # Merge: prefer parsed (from existing data) over definition-based
        final_heb = None
        final_ar = None

        if parsed_heb:
            final_heb = parsed_heb
            parsed_count += 1
        elif def_heb:
            final_heb = def_heb

        if parsed_ar:
            final_ar = parsed_ar
        elif def_ar:
            final_ar = def_ar

        # Save to word data
        if final_heb:
            info['hebrew_cognate'] = final_heb
            heb_added += 1
        if final_ar:
            info['arabic_cognate'] = final_ar
            ar_added += 1

    # Save
    with open(WORDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(words, f, ensure_ascii=False, indent=2)

    total = len(words)
    print(f"\n  Hebrew cognates: {heb_added}/{total} ({heb_added/total*100:.1f}%)")
    print(f"  Arabic cognates: {ar_added}/{total} ({ar_added/total*100:.1f}%)")
    print(f"  Parsed from existing: {parsed_count}")
    print(f"  Either cognate:  {sum(1 for w in words.values() if w.get('hebrew_cognate') or w.get('arabic_cognate'))}/{total}")
    print()
    print(f"[OK] Cognate data added to {WORDS_FILE}")


if __name__ == '__main__':
    main()
