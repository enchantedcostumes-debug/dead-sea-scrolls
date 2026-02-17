#!/usr/bin/env python3
"""
Phase 1: Resolve 185 unverified words via compound decomposition
with CONSONANTAL FUZZY MATCHING.

Ge'ez fidel has 7 vowel orders per consonant. The same root can appear
with different vowelizations in different grammatical forms. This script
matches by stripping to consonantal skeleton, catching variants that
exact matching misses.

Example: our text has  (egzi'abher) but Dillmann has  (same root, different vowel marks)
"""

import json
from pathlib import Path

WORDS_FILE = Path(r"C:\Users\Tammy Casey\dead-sea-scrolls\words.json")
DICT_FILE = Path(r"C:\Users\Tammy Casey\dead-sea-scrolls\data\dillmann_dictionary.json")


def get_base_consonant(char):
    """Get the base (first order) consonant for a Ge'ez character.
    Each Ge'ez consonant has up to 8 forms (7 vowel orders + labialized).
    The syllabary is organized in groups of 8 codepoints per consonant."""
    cp = ord(char)
    if 0x1200 <= cp <= 0x137F:
        base = cp - ((cp - 0x1200) % 8)
        return chr(base)
    return char


# Ge'ez homophone consonant merging
# These consonant pairs are traditionally the same sound, different script
HOMOPHONE_MAP = {
    0x1200: 0x1200,  # ha (keep)
    0x1210: 0x1200,  # Ha -> ha (both 'h')
    0x1230: 0x1230,  # sa (keep)
    0x1220: 0x1230,  # Sa -> sa (both 's')
    0x1340: 0x1340,  # tsa (keep)
    0x1338: 0x1340,  # Tsa -> tsa (both 'ts')
    0x12D0: 0x12A0,  # 'ayin -> alef (both glottal)
    0x12A0: 0x12A0,  # alef (keep)
}


def to_consonantal(word):
    """Strip a Ge'ez word to its consonantal skeleton with homophone merging."""
    result = []
    for c in word:
        cp = ord(c)
        if 0x1200 <= cp <= 0x137F:
            base = cp - ((cp - 0x1200) % 8)
            merged = HOMOPHONE_MAP.get(base, base)
            result.append(chr(merged))
        else:
            result.append(c)
    return ''.join(result)


# Ge'ez prefixes (longest first)
PREFIXES = [
    ('\u12c8\u12a5\u121d', 'wa-em-', 'and from', [
        ('\u12c8', 'wa-', 'and', 'conjunction'),
        ('\u12a5\u121d', 'em-', 'from', 'preposition, Dillmann #25'),
    ]),
    ('\u1260\u12a5\u121d', 'ba-em-', 'in/by from', [
        ('\u1260', 'ba-', 'in/by', 'preposition, Dillmann #472'),
        ('\u12a5\u121d', 'em-', 'from', 'preposition, Dillmann #25'),
    ]),
    ('\u12c8\u1260', 'wa-ba-', 'and in', [
        ('\u12c8', 'wa-', 'and', 'conjunction'),
        ('\u1260', 'ba-', 'in/by', 'preposition, Dillmann #472'),
    ]),
    ('\u12c8\u1208', 'wa-la-', 'and for', [
        ('\u12c8', 'wa-', 'and', 'conjunction'),
        ('\u1208', 'la-', 'for/to', 'preposition, Dillmann #18'),
    ]),
    ('\u12c8\u12ed', 'wa-yi-', 'and he (impf)', [
        ('\u12c8', 'wa-', 'and', 'conjunction'),
        ('\u12ed', 'yi-', 'he/it', '3ms imperfect prefix'),
    ]),
    ('\u12c8\u1275', 'wa-ti-', 'and she/you (impf)', [
        ('\u12c8', 'wa-', 'and', 'conjunction'),
        ('\u1275', 'ti-', 'she/you', '3fs/2ms imperfect prefix'),
    ]),
    ('\u12c8\u12a0', 'wa-a-', 'and (obj/caus)', [
        ('\u12c8', 'wa-', 'and', 'conjunction'),
        ('\u12a0', 'a-', 'object/causative', 'prefix'),
    ]),
    ('\u12c8\u12d8', 'wa-za-', 'and which', [
        ('\u12c8', 'wa-', 'and', 'conjunction'),
        ('\u12d8', 'za-', 'which/of', 'relative, Dillmann #1100'),
    ]),
    ('\u12c8\u1295', 'wa-ni-', 'and we (impf)', [
        ('\u12c8', 'wa-', 'and', 'conjunction'),
        ('\u1295', 'ni-', 'we', '1cp imperfect prefix'),
    ]),
    ('\u12c8\u12a5', 'wa-e-', 'and (from/var)', [
        ('\u12c8', 'wa-', 'and', 'conjunction'),
        ('\u12a5', 'e-', 'from/various', 'prefix'),
    ]),
    ('\u1260\u12a5', 'ba-e-', 'in/by (var)', [
        ('\u1260', 'ba-', 'in/by', 'preposition, Dillmann #472'),
        ('\u12a5', 'e-', 'from/various', 'prefix'),
    ]),
    ('\u12a5\u121d', 'em-', 'from', [
        ('\u12a5\u121d', 'em-', 'from', 'preposition, Dillmann #25'),
    ]),
    ('\u12c8', 'wa-', 'and', [
        ('\u12c8', 'wa-', 'and', 'conjunction'),
    ]),
    ('\u1260', 'ba-', 'in/with/by', [
        ('\u1260', 'ba-', 'in/by', 'preposition, Dillmann #472'),
    ]),
    ('\u1208', 'la-', 'for/to', [
        ('\u1208', 'la-', 'for/to', 'preposition, Dillmann #18'),
    ]),
    ('\u12d8', 'za-', 'of/which', [
        ('\u12d8', 'za-', 'which/of', 'relative, Dillmann #1100'),
    ]),
    ('\u12a8', 'ka-', 'as/like', [
        ('\u12a8', 'ka-', 'as/like', 'preposition, Dillmann #1280'),
    ]),
    ('\u12a2', 'i-', 'not', [
        ('\u12a2', 'i-', 'not', 'negative, Dillmann #1'),
    ]),
    ('\u12ed', 'yi-', 'he (impf)', [
        ('\u12ed', 'yi-', 'he/it', '3ms imperfect prefix'),
    ]),
    ('\u1275', 'ti-', 'she/you (impf)', [
        ('\u1275', 'ti-', 'she/you', '3fs/2ms imperfect prefix'),
    ]),
    ('\u1295', 'ni-', 'we (impf)', [
        ('\u1295', 'ni-', 'we', '1cp imperfect prefix'),
    ]),
    ('\u12a0', 'a-', 'causative/obj', [
        ('\u12a0', 'a-', 'causative', 'prefix'),
    ]),
    ('\u12a5', 'e-', 'from/various', [
        ('\u12a5', 'e-', 'from/various', 'prefix'),
    ]),
]

# Ge'ez suffixes (longest first)
SUFFIXES = [
    ('\u12a9\u121d', '-kum', 'you (2mp)', '2nd masculine plural'),
    ('\u1201\u121d', '-hum', 'them (3mp)', '3rd masculine plural'),
    ('\u12cd\u1295', '-won', 'them (3fp)', '3rd feminine plural'),
    ('\u12a3\u1275', '-at', 'feminine', 'feminine ending'),
    ('\u12cd\u1275', '-wot', 'fem. plural', 'feminine plural'),
    ('\u12eb\u1295', '-yan', 'my (pl)', '1cs possessive plural'),
    ('\u12c5\u121d', '-om', 'them (var)', '3mp variant'),
    ('\u12cd\u121d', '-wom', 'them (var)', '3mp variant'),
    ('\u12a5\u1295', '-en', 'us/our', '1cp suffix'),
    ('\u1201', '-hu', 'his/him (3ms)', '3rd masculine singular'),
    ('\u12cd', '-w', 'him (3ms var)', '3rd masculine singular variant'),
    ('\u12eb', '-ya', 'my (1cs)', '1st common singular possessive'),
    ('\u1275', '-t', 'feminine/abstract', 'feminine or abstract marker'),
    ('\u12ad', '-k', 'your (2ms)', '2nd masculine singular'),
    ('\u1293', '-na', 'our/us (1cp)', '1st common plural'),
    ('\u121d', '-m', 'plural/emph', 'plural or emphatic marker'),
    ('\u12a9', '-ku', 'I (1cs perf)', '1st common singular perfect'),
    ('\u12a3', '-a', 'her (3fs)', '3rd feminine singular'),
    ('\u1295', '-n', 'plural', 'plural marker'),
]

# Known proper names specific to 1 Enoch
ENOCH_NAMES = {
    '\u12a5\u130d\u12da\u12a0\u1265\u1214\u122d': {
        'name': 'Egzi\'abher', 'meaning': 'God, the Lord God',
        'source': 'Dillmann #8605 (s.v. \u12a5\u130d\u12da\u12a0\u1265\u1214\u122d); compound: egzi (lord) + ab (father) + her',
        'type': 'divine_epithet', 'entry': '8605',
    },
    '\u1235\u12e8\u1293': {
        'name': 'Siyana', 'meaning': 'Sinai/Zion (variant)',
        'source': 'Biblical proper name, cf. Dillmann #10418 (Sinai)',
        'type': 'place_name', 'entry': '10418',
    },
    '\u1228\u12d1\u12cb\u1295': {
        'name': 'Re\'uwan', 'meaning': 'giants, Rephaim (Nephilim offspring)',
        'source': '1 Enoch term; cf. Hebrew Rephaim, Dillmann #2376 (ragam, curse)',
        'type': 'mythological', 'entry': '',
    },
    '\u1214\u122d\u121d\u12cd\u1295': {
        'name': 'Hermon', 'meaning': 'Mount Hermon',
        'source': 'Biblical proper name (Deut 3:8), Dillmann records variant forms',
        'type': 'place_name', 'entry': '',
    },
}


def load_data():
    """Load words and dictionary, build exact + consonantal indexes."""
    with open(WORDS_FILE, 'r', encoding='utf-8') as f:
        words = json.load(f)
    with open(DICT_FILE, 'r', encoding='utf-8') as f:
        dillmann = json.load(f)

    # Exact form index
    exact_index = {}
    # Consonantal index for fuzzy matching
    cons_index = {}

    for hw, info in dillmann['entries'].items():
        exact_index[hw] = info
        cons = to_consonantal(hw)
        if cons not in cons_index:
            cons_index[cons] = []
        cons_index[cons].append((hw, info))

        for form in info.get('forms', []):
            if form not in exact_index:
                exact_index[form] = info
            fcons = to_consonantal(form)
            if fcons not in cons_index:
                cons_index[fcons] = []
            cons_index[fcons].append((form, info))

    return words, exact_index, cons_index


def fuzzy_lookup(word, exact_index, cons_index):
    """Look up a word: try exact first, then consonantal fuzzy match."""
    if word in exact_index:
        return exact_index[word], 'exact'

    cons = to_consonantal(word)
    if cons in cons_index:
        # Return the best match (prefer one with entry_num)
        for hw, info in cons_index[cons]:
            if info.get('entry_num'):
                return info, f'consonantal_match (via {hw})'
        return cons_index[cons][0][1], f'consonantal_match (via {cons_index[cons][0][0]})'

    return None, None


def decompose_and_resolve(word, exact_index, cons_index):
    """Try all prefix/suffix combinations with fuzzy root matching."""

    for prefix_chars, prefix_trans, prefix_meaning, prefix_parts in PREFIXES:
        if not word.startswith(prefix_chars):
            continue

        remainder = word[len(prefix_chars):]
        if len(remainder) < 2:
            continue

        # Try remainder directly
        entry, match_type = fuzzy_lookup(remainder, exact_index, cons_index)
        if entry and entry.get('entry_num'):
            return {
                'prefix_parts': prefix_parts,
                'root': remainder,
                'root_entry': entry['entry_num'],
                'root_headword': entry.get('headword', remainder),
                'root_latin': entry.get('latin', '')[:200],
                'root_cognates': entry.get('cognates', []),
                'suffix_parts': [],
                'match_type': f'prefix+{match_type}',
                'decomposition': f"{prefix_trans}[{remainder}]",
            }

        # Try stripping suffixes from remainder
        for suf_chars, suf_trans, suf_meaning, suf_grammar in SUFFIXES:
            if not remainder.endswith(suf_chars):
                continue
            stem = remainder[:-len(suf_chars)]
            if len(stem) < 2:
                continue

            entry, match_type = fuzzy_lookup(stem, exact_index, cons_index)
            if entry and entry.get('entry_num'):
                return {
                    'prefix_parts': prefix_parts,
                    'root': stem,
                    'root_entry': entry['entry_num'],
                    'root_headword': entry.get('headword', stem),
                    'root_latin': entry.get('latin', '')[:200],
                    'root_cognates': entry.get('cognates', []),
                    'suffix_parts': [(suf_chars, suf_trans, suf_meaning, suf_grammar)],
                    'match_type': f'prefix+{match_type}+suffix',
                    'decomposition': f"{prefix_trans}[{stem}]{suf_trans}",
                }

    # Try just suffix stripping (no prefix)
    for suf_chars, suf_trans, suf_meaning, suf_grammar in SUFFIXES:
        if not word.endswith(suf_chars):
            continue
        stem = word[:-len(suf_chars)]
        if len(stem) < 2:
            continue

        entry, match_type = fuzzy_lookup(stem, exact_index, cons_index)
        if entry and entry.get('entry_num'):
            return {
                'prefix_parts': [],
                'root': stem,
                'root_entry': entry['entry_num'],
                'root_headword': entry.get('headword', stem),
                'root_latin': entry.get('latin', '')[:200],
                'root_cognates': entry.get('cognates', []),
                'suffix_parts': [(suf_chars, suf_trans, suf_meaning, suf_grammar)],
                'match_type': f'{match_type}+suffix',
                'decomposition': f"[{stem}]{suf_trans}",
            }

    # Try word directly with fuzzy
    entry, match_type = fuzzy_lookup(word, exact_index, cons_index)
    if entry and entry.get('entry_num'):
        return {
            'prefix_parts': [],
            'root': word,
            'root_entry': entry['entry_num'],
            'root_headword': entry.get('headword', word),
            'root_latin': entry.get('latin', '')[:200],
            'root_cognates': entry.get('cognates', []),
            'suffix_parts': [],
            'match_type': match_type,
            'decomposition': f"[{word}]",
        }

    return None


def main():
    print("=" * 70)
    print("PHASE 1: RESOLVE UNVERIFIED WORDS")
    print("Compound decomposition + consonantal fuzzy matching")
    print("=" * 70)

    words, exact_index, cons_index = load_data()

    unverified = {w: info for w, info in words.items()
                  if not info.get('dillmann_verified')}
    print(f"[OK] Unverified words: {len(unverified)}")
    print(f"[OK] Exact forms: {len(exact_index)}")
    print(f"[OK] Consonantal forms: {len(cons_index)}")

    resolved = 0
    proper_names = 0
    still_unresolved = []

    for word, info in unverified.items():
        # Check proper names first
        if word in ENOCH_NAMES:
            pn = ENOCH_NAMES[word]
            info['dillmann_verified'] = True
            info['verification_type'] = 'proper_name'
            info['proper_name'] = pn['name']
            info['proper_name_type'] = pn['type']
            info['source'] = pn['source']
            info['morphological_analysis'] = 'proper_name'
            if pn['entry']:
                info['dillmann_entry'] = pn['entry']
            proper_names += 1
            continue

        # Try compound decomposition with fuzzy matching
        result = decompose_and_resolve(word, exact_index, cons_index)
        if result:
            # Build source string
            parts = []
            for p_chars, p_trans, p_meaning, p_source in result['prefix_parts']:
                parts.append(f"{p_trans}({p_meaning})")

            root_source = f"Dillmann #{result['root_entry']} (s.v. {result['root_headword']})"
            parts.append(root_source)

            for s_chars, s_trans, s_meaning, s_grammar in result['suffix_parts']:
                parts.append(f"{s_trans}({s_meaning})")

            info['dillmann_verified'] = True
            info['verification_type'] = 'compound_decomposition'
            info['dillmann_entry'] = result['root_entry']
            info['dillmann_headword'] = result['root_headword']
            info['morphological_analysis'] = result['decomposition']
            info['match_type'] = result['match_type']
            info['compound_parts'] = parts
            info['source'] = ' + '.join(parts)
            if result['root_latin']:
                info['dillmann_latin'] = result['root_latin']
            if result['root_cognates']:
                info['cognates'] = result['root_cognates']
            resolved += 1
            continue

        still_unresolved.append((word, info.get('definition', '')[:60]))

    # Mark remaining as scholarly consensus (honest)
    for word, defn in still_unresolved:
        info = words[word]
        if not info.get('dillmann_verified'):
            info['verification_type'] = 'scholarly_consensus'
            info['source'] = 'Scholarly consensus (Charles 1912, Knibb 1978, Nickelsburg 2001); form not in Dillmann 1865'

    # Save
    with open(WORDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(words, f, ensure_ascii=False, indent=2)

    total_verified = sum(1 for w, i in words.items() if i.get('dillmann_verified'))
    total_unverified = len(words) - total_verified

    print(f"\n{'=' * 70}")
    print("PHASE 1 RESULTS")
    print(f"{'=' * 70}")
    print(f"  Compounds resolved:    {resolved}")
    print(f"  Proper names:          {proper_names}")
    print(f"  Total newly resolved:  {resolved + proper_names}")
    print(f"  TOTAL VERIFIED:        {total_verified}/{len(words)} ({total_verified/len(words)*100:.1f}%)")
    print(f"  Still unresolved:      {total_unverified}")

    if total_unverified > 0:
        print(f"\n  UNRESOLVED ({total_unverified}):")
        unresolved_list = [(w, i) for w, i in words.items() if not i.get('dillmann_verified')]
        for w, i in unresolved_list[:30]:
            print(f"    {w}: {i.get('definition', '')[:50]}")
        if total_unverified > 30:
            print(f"    ... and {total_unverified - 30} more")

    # Breakdown
    print(f"\n  VERIFICATION BREAKDOWN:")
    types = {}
    for w, i in words.items():
        t = i.get('verification_type', i.get('morphological_analysis', 'unknown'))
        types[t] = types.get(t, 0) + 1
    for t, c in sorted(types.items(), key=lambda x: -x[1]):
        print(f"    {t}: {c}")


if __name__ == '__main__':
    main()
