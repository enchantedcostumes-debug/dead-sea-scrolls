#!/usr/bin/env python3
"""
Build FULL Ge'ez dictionary from Dillmann's 12,336 entries.
Also updates words.json sources with verified Dillmann entry numbers.

This is NOT just 308 words. This is the ENTIRE Dillmann dictionary
converted to JSON for the Dead Sea Scrolls project.
"""

import json
import os
import sys
import xml.etree.ElementTree as ET
import re
from pathlib import Path

DILLMANN_DIR = Path(r"C:\Users\Tammy Casey\DillmannData")
WORDS_FILE = Path(r"C:\Users\Tammy Casey\dead-sea-scrolls\words.json")
FULL_DICT_FILE = Path(r"C:\Users\Tammy Casey\dead-sea-scrolls\data\dillmann_dictionary.json")
UPDATED_WORDS = Path(r"C:\Users\Tammy Casey\dead-sea-scrolls\words_verified.json")

NS = '{http://www.tei-c.org/ns/1.0}'


def parse_entry(filepath):
    """Parse a single Dillmann XML entry into a dict."""
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()

        title_elem = root.find(f'{NS}teiHeader/{NS}fileDesc/{NS}titleStmt/{NS}title')
        title = title_elem.text.strip() if title_elem is not None and title_elem.text else ''

        entry_elem = root.find(f'.//{NS}entry')
        if entry_elem is None:
            return None
        entry_num = entry_elem.get('n', '')
        entry_id = entry_elem.get('{http://www.w3.org/XML/1998/namespace}id', '')

        # Collect all Ge'ez forms
        geez_forms = set()
        if title and any('\u1200' <= c <= '\u137f' for c in title):
            geez_forms.add(title.rstrip('\u1361\u1362'))

        for foreign in root.iter(f'{NS}foreign'):
            text = (foreign.text or '').strip()
            # Only single words in Ge'ez range
            clean = text.rstrip('\u1361\u1362').strip()
            if clean and any('\u1200' <= c <= '\u137f' for c in clean):
                if len(clean) <= 15 and '\u1361' not in clean:
                    geez_forms.add(clean)

        # Get senses
        senses = []
        for sense in root.iter(f'{NS}sense'):
            text = ''.join(sense.itertext()).strip()
            text = re.sub(r'\s+', ' ', text)
            if text and len(text) > 3:
                senses.append(text[:500])

        # Extract Latin definition keywords
        latin_def = ''
        if senses:
            # First sense is usually the main definition
            first = senses[0]
            # Remove grammar labels
            first = re.sub(r'^(subst\.|part\.|adj\.|adv\.|n\. ag\.|n\. act\.|conj\.|prep\.|pron\.)\s*', '', first)
            first = re.sub(r',?\s*(fem\.|m\.|Pl\.)\s*', ' ', first)
            # Get the Latin words before any Ge'ez citations
            latin_part = re.split(r'[\u1200-\u137f]', first)[0].strip()
            if latin_part:
                latin_def = latin_part[:200]

        # Get Hebrew/Arabic cognates
        cognates = []
        for sense_text in senses[:1]:
            # Hebrew in square brackets
            heb = re.findall(r'[\u0590-\u05FF]+', sense_text)
            if heb:
                cognates.extend([f'Heb: {h}' for h in heb[:2]])
            # Arabic
            arab = re.findall(r'[\u0600-\u06FF]+', sense_text)
            if arab:
                cognates.extend([f'Ar: {a}' for a in arab[:2]])

        if not geez_forms:
            return None

        return {
            'entry_num': entry_num,
            'entry_id': entry_id,
            'headword': title.rstrip('\u1361\u1362').strip(),
            'forms': sorted(geez_forms),
            'latin_definition': latin_def,
            'senses': senses[:3],
            'cognates': cognates[:4],
        }

    except Exception:
        return None


def build_full_dictionary():
    """Build the complete Ge'ez dictionary from all XML files."""
    print("[SCAN] Building FULL Ge'ez dictionary from Dillmann XML files...")

    entries = []
    headword_index = {}  # headword -> entry
    file_count = 0

    for subdir in sorted(DILLMANN_DIR.iterdir()):
        if not subdir.is_dir() or subdir.name.startswith('.'):
            continue
        if subdir.name in ('schema', 'test', '.github', 'new', 'new1'):
            continue

        for xml_file in subdir.glob('*.xml'):
            file_count += 1
            if file_count % 2000 == 0:
                print(f"  [SCAN] {file_count} files, {len(entries)} entries...")

            entry = parse_entry(xml_file)
            if entry:
                entries.append(entry)
                # Index by headword
                hw = entry['headword']
                if hw:
                    headword_index[hw] = entry
                # Also index by all forms
                for form in entry['forms']:
                    if form not in headword_index:
                        headword_index[form] = entry

    print(f"[OK] {len(entries)} dictionary entries, {len(headword_index)} indexed forms")
    return entries, headword_index


def update_words_json(headword_index):
    """Update words.json sources with verified Dillmann entry numbers."""
    print(f"\n[UPDATE] Updating words.json with verified Dillmann references...")

    with open(WORDS_FILE, 'r', encoding='utf-8') as f:
        words = json.load(f)

    updated = 0
    verified = 0

    for geez_word, info in words.items():
        # Try exact match
        entry = headword_index.get(geez_word)

        # Try prefix stripping
        if not entry:
            prefixes = ['\u12c8', '\u1260', '\u1208', '\u12d8', '\u12a8', '\u12a2',
                       '\u12ed', '\u1275', '\u1295', '\u12a0', '\u12a5']
            for p in prefixes:
                if geez_word.startswith(p) and len(geez_word) > len(p) + 1:
                    rest = geez_word[len(p):]
                    entry = headword_index.get(rest)
                    if entry:
                        break
                    # Double prefix
                    if geez_word.startswith('\u12c8') and len(geez_word) > 3:
                        for p2 in prefixes:
                            if rest.startswith(p2):
                                entry = headword_index.get(rest[len(p2):])
                                if entry:
                                    break

        # Try em- prefix (2 chars)
        if not entry and geez_word.startswith('\u12a5\u121d') and len(geez_word) > 3:
            entry = headword_index.get(geez_word[2:])

        if entry:
            entry_num = entry['entry_num']
            headword = entry['headword']
            old_source = info.get('source', '')
            new_source = f"Dillmann, Lexicon #{entry_num} (s.v. {headword})"

            # Only update if we have a real entry number
            if entry_num:
                info['source'] = new_source
                info['dillmann_verified'] = True
                info['dillmann_entry'] = entry_num
                info['dillmann_headword'] = headword
                if entry['latin_definition']:
                    info['dillmann_latin'] = entry['latin_definition'][:200]
                if entry['cognates']:
                    info['cognates'] = entry['cognates']
                verified += 1
                updated += 1

    # Save updated words.json
    with open(UPDATED_WORDS, 'w', encoding='utf-8') as f:
        json.dump(words, f, ensure_ascii=False, indent=2)

    print(f"[OK] {verified}/{len(words)} words verified against Dillmann")
    print(f"[OK] Updated words saved to {UPDATED_WORDS}")

    return words, verified


def main():
    print("=" * 70)
    print("BUILD FULL GE'EZ DICTIONARY FROM DILLMANN (12,336 entries)")
    print("AND UPDATE ENOCH LEXICON WITH VERIFIED SOURCES")
    print("=" * 70)

    if not DILLMANN_DIR.exists():
        print("[FAIL] DillmannData not found!")
        sys.exit(1)

    # Build full dictionary
    entries, headword_index = build_full_dictionary()

    # Save full dictionary
    os.makedirs(FULL_DICT_FILE.parent, exist_ok=True)

    dict_output = {
        'title': "Dillmann's Lexicon Linguae Aethiopicae (1865)",
        'source': 'BetaMasaheft/DillmannData (TEI-XML)',
        'license': 'CC BY-SA-NC 4.0',
        'total_entries': len(entries),
        'entries': {}
    }

    for entry in entries:
        hw = entry['headword']
        if hw:
            dict_output['entries'][hw] = {
                'entry_num': entry['entry_num'],
                'forms': entry['forms'],
                'latin': entry['latin_definition'],
                'senses': entry['senses'][:2],
                'cognates': entry['cognates'],
            }

    with open(FULL_DICT_FILE, 'w', encoding='utf-8') as f:
        json.dump(dict_output, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] Full dictionary saved: {FULL_DICT_FILE}")
    print(f"     {len(dict_output['entries'])} headwords")

    # Update words.json
    words, verified = update_words_json(headword_index)

    # Summary
    print(f"\n{'=' * 70}")
    print("FINAL SUMMARY")
    print(f"{'=' * 70}")
    print(f"  Full Ge'ez dictionary: {len(dict_output['entries'])} headwords (from Dillmann 1865)")
    print(f"  Enoch words verified:  {verified}/308 against Dillmann entry numbers")
    print(f"  Dictionary file:       {FULL_DICT_FILE}")
    print(f"  Updated lexicon:       {UPDATED_WORDS}")


if __name__ == '__main__':
    main()
