#!/usr/bin/env python3
"""
Cross-reference Enoch lexicon against Dillmann's Lexicon Linguae Aethiopicae (1865).

Uses the BetaMasaheft DillmannData repository (13,742 TEI-XML entries)
to verify and replace training-data definitions with REAL dictionary entries.

SCHOLARLY STANDARD: Every definition must trace to Dillmann entry number.
"""

import json
import os
import sys
import xml.etree.ElementTree as ET
import re
from pathlib import Path

# Paths
DILLMANN_DIR = Path(r"C:\Users\Tammy Casey\DillmannData")
WORDS_FILE = Path(r"C:\Users\Tammy Casey\dead-sea-scrolls\words.json")
OUTPUT_FILE = Path(r"C:\Users\Tammy Casey\dead-sea-scrolls\tools\dillmann_matches.json")

# TEI namespace
NS = '{http://www.tei-c.org/ns/1.0}'

# Latin-to-English common translations for Dillmann definitions
LATIN_TO_ENGLISH = {
    'terra': 'earth, land',
    'aqua': 'water',
    'ignis': 'fire',
    'caelum': 'heaven, sky',
    'deus': 'God',
    'dominus': 'lord, master',
    'rex': 'king',
    'homo': 'man, human',
    'angelus': 'angel, messenger',
    'nuntius': 'messenger, envoy',
    'legatus': 'envoy, ambassador',
    'anima': 'soul, spirit',
    'spiritus': 'spirit, breath',
    'verbum': 'word, speech',
    'dies': 'day',
    'nox': 'night',
    'lux': 'light',
    'tenebrae': 'darkness',
    'mons': 'mountain',
    'flumen': 'river',
    'mare': 'sea',
    'arbor': 'tree',
    'filius': 'son',
    'filia': 'daughter',
    'pater': 'father',
    'mater': 'mother',
    'populus': 'people, nation',
    'via': 'way, path',
    'justitia': 'justice, righteousness',
    'peccatum': 'sin',
    'sanguis': 'blood',
    'mors': 'death',
    'vita': 'life',
    'gloria': 'glory',
    'sanctus': 'holy, sacred',
    'magnus': 'great',
    'malus': 'evil, bad',
    'bonus': 'good',
    'omnis': 'all, every',
    'facere': 'to do, to make',
    'venire': 'to come',
    'ire': 'to go',
    'videre': 'to see',
    'dicere': 'to say, to speak',
    'dare': 'to give',
    'scribere': 'to write',
    'judicare': 'to judge',
    'occidere': 'to kill',
    'peccare': 'to sin',
    'jurare': 'to swear',
    'docere': 'to teach',
    'descendere': 'to descend',
    'ascendere': 'to ascend',
    'subst.': '',
    'part.': '',
    'fem.': '',
    'adj.': '',
    'Pl.': '',
    'cubans': 'lying down',
    'ardor': 'burning, zeal',
    'scriptura': 'writing, scripture',
    'liber': 'book',
}


def extract_entry(filepath):
    """Extract Ge'ez headword(s), Latin definition, and entry number from XML."""
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()

        # Get title (headword)
        title_elem = root.find(f'{NS}teiHeader/{NS}fileDesc/{NS}titleStmt/{NS}title')
        title = title_elem.text.strip() if title_elem is not None and title_elem.text else ''

        # Get entry number
        entry_elem = root.find(f'.//{NS}entry')
        entry_num = entry_elem.get('n', '') if entry_elem is not None else ''
        entry_id = entry_elem.get('{http://www.w3.org/XML/1998/namespace}id', '') if entry_elem is not None else ''

        # Get all Ge'ez forms from <foreign> elements
        geez_forms = set()
        if title:
            geez_forms.add(title)
        for foreign in root.iter(f'{NS}foreign'):
            text = (foreign.text or '').strip().rstrip('\u1361\u1362')
            if text and any('\u1200' <= c <= '\u137f' for c in text):
                # Only short forms (single words, not phrases)
                if len(text) <= 20 and '\u1361' not in text:
                    geez_forms.add(text)

        # Get sense text (Latin definitions)
        senses = []
        for sense in root.iter(f'{NS}sense'):
            all_text = ''.join(sense.itertext()).strip()
            # Clean up whitespace
            all_text = re.sub(r'\s+', ' ', all_text)
            if all_text and len(all_text) > 3:
                senses.append(all_text[:300])

        if not geez_forms:
            return None

        return {
            'title': title,
            'entry_num': entry_num,
            'entry_id': entry_id,
            'geez_forms': list(geez_forms),
            'senses': senses[:3],
            'file': os.path.basename(filepath),
        }

    except (ET.ParseError, Exception):
        return None


def build_dillmann_index():
    """Build an index of all Ge'ez words in the Dillmann data."""
    print("[SCAN] Building Dillmann index from 13,742 XML files...")

    index = {}  # geez_word -> [entry_info, ...]
    file_count = 0
    entry_count = 0

    for subdir in sorted(DILLMANN_DIR.iterdir()):
        if not subdir.is_dir() or subdir.name.startswith('.'):
            continue
        if subdir.name in ('schema', 'test', '.github', 'new', 'new1'):
            continue

        for xml_file in subdir.glob('*.xml'):
            file_count += 1
            if file_count % 2000 == 0:
                print(f"  [SCAN] {file_count} files, {entry_count} entries, {len(index)} forms...")

            entry = extract_entry(xml_file)
            if entry:
                entry_count += 1
                for word in entry['geez_forms']:
                    # Clean the word
                    clean = word.strip().rstrip('\u1361\u1362')
                    if not clean:
                        continue

                    if clean not in index:
                        index[clean] = []
                    index[clean].append(entry)

    print(f"[OK] Dillmann index: {file_count} files, {entry_count} entries, {len(index)} unique forms")
    return index


def strip_prefixes(word):
    """Strip common Ge'ez prefixes to find the root word."""
    variants = {word}

    # Single prefixes
    single = [
        ('\u12c8', 'wa'),   # ወ and
        ('\u1260', 'ba'),   # በ in/with
        ('\u1208', 'la'),   # ለ for/to
        ('\u12d8', 'za'),   # ዘ of/which
        ('\u12a8', 'ka'),   # ከ as/like
        ('\u12a2', 'i'),    # ኢ not
        ('\u12ed', 'yi'),   # ይ impf prefix
        ('\u1275', 'ti'),   # ት 2nd/refl
        ('\u1295', 'ni'),   # ን 1pl
        ('\u12a0', 'a'),    # አ causative
        ('\u12a5', 'e'),    # እ various
    ]

    for prefix, name in single:
        if word.startswith(prefix) and len(word) > len(prefix) + 1:
            rest = word[len(prefix):]
            variants.add(rest)

    # Double prefixes: wa + X
    if word.startswith('\u12c8') and len(word) > 3:
        rest = word[1:]
        for prefix, name in single:
            if rest.startswith(prefix) and len(rest) > len(prefix) + 1:
                variants.add(rest[len(prefix):])

    # Common prefix combo: እም (from)
    if word.startswith('\u12a5\u121d') and len(word) > 3:
        variants.add(word[2:])

    return variants


def cross_reference(words_data, dillmann_index):
    """Cross-reference our words against the Dillmann index."""
    print(f"\n[SCAN] Cross-referencing {len(words_data)} words against Dillmann...")

    matches = {}
    no_match = []

    for geez_word, word_info in words_data.items():
        found = False

        # Try exact match
        if geez_word in dillmann_index:
            matches[geez_word] = {
                'match_type': 'exact',
                'entries': dillmann_index[geez_word][:3],
                'current_def': word_info.get('definition', ''),
            }
            found = True
            continue

        # Try prefix-stripped variants
        variants = strip_prefixes(geez_word)
        for v in variants:
            if v != geez_word and v in dillmann_index:
                matches[geez_word] = {
                    'match_type': f'prefix_stripped ({v})',
                    'entries': dillmann_index[v][:3],
                    'current_def': word_info.get('definition', ''),
                }
                found = True
                break

        if found:
            continue

        # Try with common suffixes stripped
        suffixes = ['\u1201', '\u1205\u121d', '\u12cd', '\u12c5']  # -hu, -hom, -w, -a
        for suffix in suffixes:
            if geez_word.endswith(suffix) and len(geez_word) > len(suffix) + 2:
                stem = geez_word[:-len(suffix)]
                if stem in dillmann_index:
                    matches[geez_word] = {
                        'match_type': f'suffix_stripped ({stem})',
                        'entries': dillmann_index[stem][:3],
                        'current_def': word_info.get('definition', ''),
                    }
                    found = True
                    break
                # Also try prefix+suffix strip
                for v in strip_prefixes(stem):
                    if v != stem and v in dillmann_index:
                        matches[geez_word] = {
                            'match_type': f'affix_stripped ({v})',
                            'entries': dillmann_index[v][:3],
                            'current_def': word_info.get('definition', ''),
                        }
                        found = True
                        break
                if found:
                    break

        if found:
            continue

        # Try partial match: our word contains a Dillmann headword
        for dword in dillmann_index:
            if len(dword) >= 3 and dword in geez_word and len(dword) < len(geez_word):
                matches[geez_word] = {
                    'match_type': f'contains_root ({dword})',
                    'entries': dillmann_index[dword][:2],
                    'current_def': word_info.get('definition', ''),
                }
                found = True
                break

        if not found:
            no_match.append({
                'word': geez_word,
                'def': word_info.get('definition', ''),
            })

    matched = len(matches)
    total = len(words_data)
    print(f"[OK] Matched: {matched}/{total} ({matched/total*100:.1f}%)")
    print(f"[WARN] Unmatched: {len(no_match)}/{total}")

    return matches, no_match


def main():
    print("=" * 70)
    print("DILLMANN CROSS-REFERENCE")
    print("Verify 1 Enoch Lexicon Against Real Dictionary (13,742 entries)")
    print("=" * 70)

    if not DILLMANN_DIR.exists():
        print("[FAIL] DillmannData not found!")
        sys.exit(1)

    # Load our lexicon
    print(f"\n[LOAD] Reading words.json...")
    with open(WORDS_FILE, 'r', encoding='utf-8') as f:
        words_data = json.load(f)
    print(f"[OK] {len(words_data)} Ge'ez words loaded")

    # Build index
    dillmann_index = build_dillmann_index()

    # Cross-reference
    matches, no_match = cross_reference(words_data, dillmann_index)

    # Build output
    results = {
        'total_words': len(words_data),
        'matched': len(matches),
        'unmatched': len(no_match),
        'match_rate': f"{len(matches)/len(words_data)*100:.1f}%",
        'matches': {},
        'no_match': no_match,
    }

    type_counts = {}
    for word, info in matches.items():
        mt = info['match_type'].split(' ')[0]
        type_counts[mt] = type_counts.get(mt, 0) + 1

        results['matches'][word] = {
            'match_type': info['match_type'],
            'current_def': info['current_def'],
            'dillmann_entry_nums': [e.get('entry_num', '') for e in info['entries']],
            'dillmann_titles': [e.get('title', '') for e in info['entries']],
            'dillmann_senses': [e.get('senses', [])[:1] for e in info['entries']],
        }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # Summary
    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print(f"{'=' * 70}")
    print(f"  Total Enoch words:    {len(words_data)}")
    print(f"  Found in Dillmann:    {len(matches)} ({len(matches)/len(words_data)*100:.1f}%)")
    print(f"  Not found:            {len(no_match)} ({len(no_match)/len(words_data)*100:.1f}%)")
    print(f"\n  Match types:")
    for mt, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"    {mt}: {count}")

    if no_match:
        print(f"\n  Unmatched (first 15):")
        for item in no_match[:15]:
            print(f"    {item['word']}: {item['def'][:50]}")

    print(f"\n[OK] Results saved to {OUTPUT_FILE}")
    return len(matches), len(no_match)


if __name__ == '__main__':
    matched, unmatched = main()
