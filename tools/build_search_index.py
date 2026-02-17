#!/usr/bin/env python3
"""
Build search index mapping every Ge'ez word to its chapter:verse locations.
Scans all 36 chapter HTML files and produces data/search_index.json.

Copyright (c) 2026 Tammy L Casey. All rights reserved.
"""

import json
import os
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.join(SCRIPT_DIR, '..')
CHAPTERS_DIR = os.path.join(PROJECT_ROOT, '1_enoch')
OUTPUT_PATH = os.path.join(PROJECT_ROOT, 'data', 'search_index.json')


def extract_verse_data(html_content, chapter_num):
    """Extract word-to-verse mappings from chapter HTML."""
    verses = []

    # Find each verse block
    verse_pattern = re.compile(
        r'<span class="verse-number">(\d+:\d+)</span>.*?'
        r'<div class="original-text geez"[^>]*>(.*?)</div>\s*'
        r'<div class="translation">(.*?)</div>',
        re.DOTALL
    )

    for match in verse_pattern.finditer(html_content):
        verse_ref = match.group(1)
        geez_html = match.group(2)
        english = match.group(3).strip()

        # Extract individual words
        word_pattern = re.compile(r"showWordEvolution\('([^']+)'\)")
        geez_words = word_pattern.findall(geez_html)

        verses.append({
            'ref': verse_ref,
            'chapter': chapter_num,
            'words': geez_words,
            'english': english,
        })

    return verses


def main():
    # Ensure data directory exists
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    # Load words.json for enrichment
    words_path = os.path.join(PROJECT_ROOT, 'words.json')
    with open(words_path, 'r', encoding='utf-8') as f:
        words_data = json.load(f)

    all_verses = []
    word_locations = {}  # geez_word -> list of verse refs

    for i in range(1, 37):
        filepath = os.path.join(CHAPTERS_DIR, f'{i}.html')
        if not os.path.exists(filepath):
            print(f"[WARN] Missing: {filepath}")
            continue

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        verses = extract_verse_data(content, i)
        all_verses.extend(verses)

        for verse in verses:
            for word in verse['words']:
                if word not in word_locations:
                    word_locations[word] = []
                word_locations[word].append(verse['ref'])

    # Build search index
    search_index = {
        'verses': all_verses,
        'word_count': len(word_locations),
        'verse_count': len(all_verses),
        'chapter_count': 36,
    }

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(search_index, f, ensure_ascii=False, indent=2)

    print(f"[OK] Search index built: {len(all_verses)} verses, {len(word_locations)} unique words")
    print(f"[OK] Saved to {OUTPUT_PATH}")


if __name__ == '__main__':
    main()
