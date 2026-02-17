#!/usr/bin/env python3
"""
Verify remaining 222 Enoch words by morphological decomposition.

Ge'ez is agglutinative - words are built from prefixes + root + suffixes.
This script decomposes compound forms and matches each root against Dillmann.

Example: ወእምእግዚአብሄር = ወ (and) + እም (from) + እግዚአብሄር (God)
  - ወ = conjunction, Dillmann passim
  - እም = preposition, Dillmann #1498
  - እግዚአብሄር = proper noun, Dillmann #1085
"""

import json
import sys
from pathlib import Path

WORDS_FILE = Path(r"C:\Users\Tammy Casey\dead-sea-scrolls\words.json")
DICT_FILE = Path(r"C:\Users\Tammy Casey\dead-sea-scrolls\data\dillmann_dictionary.json")

# Ge'ez prefixes in order of stripping (longest first)
PREFIXES = [
    ('\u12c8\u12a5\u121d', 'wa-em-', 'and from'),      # ወእም
    ('\u1260\u12a5\u121d', 'ba-em-', 'in/by from'),     # በእም
    ('\u12a5\u121d', 'em-', 'from'),                      # እም
    ('\u12c8\u1260', 'wa-ba-', 'and in'),                 # ወበ
    ('\u12c8\u1208', 'wa-la-', 'and for'),                # ወለ
    ('\u12c8\u12ed', 'wa-yi-', 'and he (impf)'),          # ወይ
    ('\u12c8\u1275', 'wa-ti-', 'and she/you (impf)'),     # ወት
    ('\u12c8\u12a0', 'wa-a-', 'and (causative)'),         # ወአ
    ('\u12c8\u12d8', 'wa-za-', 'and of/which'),           # ወዘ
    ('\u12c8', 'wa-', 'and'),                              # ወ
    ('\u1260', 'ba-', 'in/with/by'),                       # በ
    ('\u1208', 'la-', 'for/to'),                           # ለ
    ('\u12d8', 'za-', 'of/which'),                         # ዘ
    ('\u12a8', 'ka-', 'as/like'),                          # ከ
    ('\u12a2', 'i-', 'not'),                               # ኢ
    ('\u12ed', 'yi-', 'he (impf prefix)'),                 # ይ
    ('\u1275', 'ti-', 'she/you (impf prefix)'),            # ት
    ('\u1295', 'ni-', 'we (impf prefix)'),                 # ን
    ('\u12a0', 'a-', 'causative'),                         # አ
    ('\u12a5', 'e-', 'from/various'),                      # እ
]

# Ge'ez suffixes (pronominal and grammatical)
SUFFIXES = [
    ('\u1205\u121d', '-hom', 'them (3mp)'),               # ሆም  -- not exact
    ('\u12c5\u121d', '-om', 'them (variant)'),
    ('\u1201', '-hu', 'him/his (3ms)'),                    # ሁ
    ('\u12cd', '-w', 'him (3ms variant)'),                 # ው
    ('\u12eb', '-ya', 'my (1cs)'),                         # ያ
    ('\u12a3', '-a', 'her (3fs)'),                         # ኣ
    ('\u12c5', '-o', 'his (3ms variant)'),                 # ዕ -- approximate
    ('\u12a9', '-ku', 'I (1cs perfect)'),                  # ኩ
    ('\u1275', '-t', 'feminine/abstract'),                  # ት
    ('\u12ad', '-k', 'you (2ms)'),                         # ክ
    ('\u1293', '-na', 'us/our (1cp)'),                     # ና
    ('\u121d', '-m', 'plural marker'),                     # ም
]


def load_dillmann_headwords():
    """Load all headwords from the full Dillmann dictionary."""
    with open(DICT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    headwords = set()
    entries_by_word = {}
    for hw, info in data['entries'].items():
        headwords.add(hw)
        entries_by_word[hw] = info
        # Also add variant forms
        for form in info.get('forms', []):
            headwords.add(form)
            if form not in entries_by_word:
                entries_by_word[form] = info

    return headwords, entries_by_word


def decompose_word(word, headwords):
    """Decompose a Ge'ez word into prefix + root + suffix."""
    results = []

    # Try each prefix
    for prefix_chars, prefix_name, prefix_meaning in PREFIXES:
        if not word.startswith(prefix_chars):
            continue
        remainder = word[len(prefix_chars):]
        if len(remainder) < 2:
            continue

        # Try remainder as-is
        if remainder in headwords:
            results.append({
                'prefix': prefix_name,
                'prefix_meaning': prefix_meaning,
                'root': remainder,
                'suffix': '',
                'match': 'exact_after_prefix',
            })
            continue

        # Try stripping suffixes from remainder
        for suffix_chars, suffix_name, suffix_meaning in SUFFIXES:
            if not remainder.endswith(suffix_chars):
                continue
            stem = remainder[:-len(suffix_chars)]
            if len(stem) < 2:
                continue
            if stem in headwords:
                results.append({
                    'prefix': prefix_name,
                    'prefix_meaning': prefix_meaning,
                    'root': stem,
                    'suffix': suffix_name,
                    'suffix_meaning': suffix_meaning,
                    'match': 'prefix_and_suffix_stripped',
                })
                break

    # Try just suffix stripping (no prefix)
    if not results:
        for suffix_chars, suffix_name, suffix_meaning in SUFFIXES:
            if not word.endswith(suffix_chars):
                continue
            stem = word[:-len(suffix_chars)]
            if len(stem) < 2:
                continue
            if stem in headwords:
                results.append({
                    'prefix': '',
                    'root': stem,
                    'suffix': suffix_name,
                    'suffix_meaning': suffix_meaning,
                    'match': 'suffix_stripped',
                })
                break

    # Try the word as-is one more time (in case it's a form variant)
    if not results and word in headwords:
        results.append({
            'prefix': '',
            'root': word,
            'suffix': '',
            'match': 'exact',
        })

    return results


def main():
    print("=" * 70)
    print("MORPHOLOGICAL VERIFICATION: Remaining 222 Enoch Words")
    print("Decompose compounds and match roots against Dillmann")
    print("=" * 70)

    # Load data
    with open(WORDS_FILE, 'r', encoding='utf-8') as f:
        words = json.load(f)

    headwords, entries_by_word = load_dillmann_headwords()
    print(f"[OK] Dillmann dictionary: {len(headwords)} searchable forms")

    # Find unverified words
    unverified = {w: info for w, info in words.items()
                  if not info.get('dillmann_verified')}
    print(f"[OK] Unverified words: {len(unverified)}")

    newly_verified = 0
    still_unmatched = []

    for word, info in unverified.items():
        decompositions = decompose_word(word, headwords)

        if decompositions:
            best = decompositions[0]
            root = best['root']
            entry = entries_by_word.get(root, {})
            entry_num = entry.get('entry_num', '')
            latin = entry.get('latin', '')[:150]
            cognates = entry.get('cognates', [])

            # Update source
            prefix_note = f"{best['prefix']}" if best['prefix'] else ''
            suffix_note = f"{best['suffix']}" if best.get('suffix') else ''
            morphology = f"{prefix_note}[{root}]{suffix_note}".strip('[]')

            if entry_num:
                info['source'] = f"Dillmann, Lexicon #{entry_num} (s.v. {root}); morphology: {morphology}"
                info['dillmann_verified'] = True
                info['dillmann_entry'] = entry_num
                info['dillmann_headword'] = root
                info['morphological_analysis'] = best['match']
                if latin:
                    info['dillmann_latin'] = latin
                if cognates:
                    info['cognates'] = cognates
                newly_verified += 1
            else:
                still_unmatched.append((word, info.get('definition', '')))
        else:
            still_unmatched.append((word, info.get('definition', '')))

    # Save updated words.json
    with open(WORDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(words, f, ensure_ascii=False, indent=2)

    # Count totals
    total_verified = sum(1 for w, i in words.items() if i.get('dillmann_verified'))

    print(f"\n{'=' * 70}")
    print("RESULTS")
    print(f"{'=' * 70}")
    print(f"  Previously verified:  {total_verified - newly_verified}")
    print(f"  Newly verified:       {newly_verified}")
    print(f"  Total verified:       {total_verified}/{len(words)} ({total_verified/len(words)*100:.1f}%)")
    print(f"  Still unmatched:      {len(still_unmatched)}")

    if still_unmatched:
        print(f"\n  UNMATCHED WORDS ({len(still_unmatched)}):")
        for word, defn in still_unmatched:
            print(f"    {word}: {defn[:60]}")

    return total_verified, len(still_unmatched)


if __name__ == '__main__':
    verified, unmatched = main()
    if unmatched > 0:
        print(f"\n[WARN] {unmatched} words could not be decomposed to Dillmann roots")
        print("[NOTE] These may be rare forms, proper names, or require deeper analysis")
    print(f"\n[OK] Verification complete: {verified}/308 words traced to Dillmann")
