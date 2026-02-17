#!/usr/bin/env python3
"""
Enrich words.json with modern English definitions and semantic domains.
=====================================================================
Dillmann's 1865 dictionary has Latin definitions. This script adds:
1. Clear modern English definitions for each root
2. Semantic domain classification (body, nature, divine, etc.)
3. Part of speech information
4. Usage notes from 1 Enoch context

Sources: Standard Ge'ez lexicographic data (Leslau CDG 2006 framework,
Kidane 1955/56, Dillmann 1865 via BetaMasaheft), cross-referenced with
the Dillmann entry numbers already verified in words.json.

Copyright (c) 2026 Tammy L Casey. All rights reserved.
"""

import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.join(SCRIPT_DIR, '..')
WORDS_FILE = os.path.join(PROJECT_ROOT, 'words.json')

# ============================================================================
# MODERN ENGLISH DEFINITIONS BY ROOT
# ============================================================================
# Keyed by Ge'ez root or headword. Each entry provides:
#   english: Clear English definition
#   pos: Part of speech (n=noun, v=verb, adj=adjective, adv=adverb,
#         prep=preposition, conj=conjunction, pron=pronoun, num=numeral,
#         part=particle, prop=proper noun)
#   domain: Semantic domain
#   usage: How it's used in 1 Enoch specifically
#   cognates_en: English-readable cognate info

ROOT_DEFINITIONS = {
    # === DIVINE / THEOLOGICAL ===
    '\u12a5\u130d\u12da\u12a0\u1265\u1214\u122d': {
        'english': 'God, the Lord',
        'pos': 'n',
        'domain': 'divine',
        'usage': 'The supreme deity; compound of egzi (lord) + ab (father) + her (people)',
        'cognates_en': 'Compound: lord-father-of-people',
    },
    '\u1245\u12f1\u1235': {
        'english': 'holy, sacred',
        'pos': 'adj',
        'domain': 'divine',
        'usage': 'Describes God, angels, and sacred places in Enoch',
        'cognates_en': 'Heb: qadosh; Ar: quddus',
    },
    '\u1260\u1228\u12a8': {
        'english': 'to bless',
        'pos': 'v',
        'domain': 'divine',
        'usage': 'Opening word concept of 1 Enoch: "words of blessing"',
        'cognates_en': 'Heb: barakh; Ar: baraka',
    },
    '\u1265\u1229\u12ad': {
        'english': 'blessed',
        'pos': 'adj',
        'domain': 'divine',
        'usage': 'Participle of baraka; describes the righteous',
    },
    '\u1260\u1228\u12a8\u1275': {
        'english': 'blessing',
        'pos': 'n',
        'domain': 'divine',
        'usage': 'Opening concept: "The words of the blessing of Enoch"',
        'cognates_en': 'Heb: berakha; Ar: baraka',
    },
    '\u1345\u12f5\u1245': {
        'english': 'righteousness, justice',
        'pos': 'n',
        'domain': 'divine',
        'usage': 'Central theme: the righteous vs the wicked',
        'cognates_en': 'Heb: tsedeq; Ar: sidq',
    },
    '\u1280\u1324\u12a0': {
        'english': 'sin, transgression',
        'pos': 'n',
        'domain': 'divine',
        'usage': 'The sin of the Watchers; transgression against divine order',
    },
    '\u1215\u1229\u12ed': {
        'english': 'chosen, elect',
        'pos': 'adj',
        'domain': 'divine',
        'usage': 'The elect/chosen ones who will be saved',
    },
    '\u1228\u130d\u121d': {
        'english': 'curse, imprecation',
        'pos': 'n',
        'domain': 'divine',
        'usage': 'The curse upon the Watchers and sinners',
    },
    '\u1235\u1265\u1213\u1275': {
        'english': 'glory, praise, splendor',
        'pos': 'n',
        'domain': 'divine',
        'usage': 'The glory of God; praise offered to the Most High',
        'cognates_en': 'Heb: shevakh; Ar: subhan',
    },
    '\u12ad\u1265\u122d': {
        'english': 'glory, honor, dignity',
        'pos': 'n',
        'domain': 'divine',
        'usage': 'Divine glory; the honor of the righteous',
    },
    '\u121d\u1215\u1228\u1275': {
        'english': 'mercy, compassion',
        'pos': 'n',
        'domain': 'divine',
        'usage': 'Gods mercy toward the righteous',
    },
    '\u1218\u1225\u122b\u1275': {
        'english': 'foundation',
        'pos': 'n',
        'domain': 'divine',
        'usage': 'Foundation of heaven and earth',
    },

    # === BEINGS / PERSONS ===
    '\u1220\u121d\u12eb\u12db': {
        'english': 'Semyaza',
        'pos': 'prop',
        'domain': 'angelic',
        'usage': 'Leader of the fallen Watchers (200 angels)',
    },
    '\u1218\u120b\u12a5\u12ad\u1275': {
        'english': 'angel, messenger',
        'pos': 'n',
        'domain': 'angelic',
        'usage': 'Heavenly messengers; both faithful and fallen',
        'cognates_en': 'From malaka (to send); Heb: malakh; Ar: malak',
    },
    '\u1204\u1296\u12ad': {
        'english': 'Enoch',
        'pos': 'prop',
        'domain': 'person',
        'usage': 'The patriarch, seventh from Adam; visionary author',
        'cognates_en': 'Heb: Khanokh (initiated/dedicated)',
    },
    '\u1235\u1265\u12a5': {
        'english': 'human being, person',
        'pos': 'n',
        'domain': 'person',
        'usage': 'Humanity collectively; "children of men"',
    },
    '\u12a5\u1295\u1235': {
        'english': 'man, human being',
        'pos': 'n',
        'domain': 'person',
        'usage': 'Individual human; mankind',
    },
    '\u12c8\u120d\u12f5': {
        'english': 'child, son, offspring',
        'pos': 'n',
        'domain': 'person',
        'usage': 'Children of men; children of righteousness',
    },
    '\u12d0\u1261\u12ed': {
        'english': 'great, mighty',
        'pos': 'adj',
        'domain': 'person',
        'usage': 'The great ones; the mighty of earth',
    },
    '\u1345\u12f5\u1243\u1295': {
        'english': 'righteous ones',
        'pos': 'n',
        'domain': 'person',
        'usage': 'The righteous who will inherit eternal life',
    },
    '\u1232\u130b': {
        'english': 'flesh, meat, body',
        'pos': 'n',
        'domain': 'person',
        'usage': 'Physical body; the flesh that the giants devour',
        'cognates_en': 'Ar: shiga; related to Heb: she-er',
    },

    # === NATURE / COSMIC ===
    '\u1230\u121b\u12ed': {
        'english': 'heaven, sky',
        'pos': 'n',
        'domain': 'nature',
        'usage': 'The heavens where God dwells; celestial realm',
        'cognates_en': 'Heb: shamayim; Ar: sama',
    },
    '\u121d\u12f5\u122d': {
        'english': 'earth, land, ground',
        'pos': 'n',
        'domain': 'nature',
        'usage': 'The earth that trembles at Gods coming',
        'cognates_en': 'Ar: madar (round); related to circling',
    },
    '\u12a8\u12c8\u12ad\u1265': {
        'english': 'star',
        'pos': 'n',
        'domain': 'nature',
        'usage': 'Stars of heaven; stars as symbols for angels',
        'cognates_en': 'Heb: kokhav; Ar: kawkab',
    },
    '\u12f0\u1265\u122d': {
        'english': 'mountain',
        'pos': 'n',
        'domain': 'nature',
        'usage': 'Mountains tremble; Mount Sinai; seven mountains',
        'cognates_en': 'Related to Ar: dabr (back, ridge)',
    },
    '\u121b\u12ed': {
        'english': 'water',
        'pos': 'n',
        'domain': 'nature',
        'usage': 'Waters of judgment; the great flood',
        'cognates_en': 'Heb: mayim; Ar: ma',
    },
    '\u12d3\u12ed\u1295': {
        'english': 'eye, spring, fountain',
        'pos': 'n',
        'domain': 'nature',
        'usage': 'Eyes opened by God; springs of water',
        'cognates_en': 'Heb: ayin; Ar: ayn',
    },
    '\u12d3\u12c8\u12f5': {
        'english': 'tree, wood',
        'pos': 'n',
        'domain': 'nature',
        'usage': 'Trees of knowledge; the aromatic trees of paradise',
    },

    # === VERBS OF ACTION ===
    '\u12a8\u12c8\u1290': {
        'english': 'to be, to become, to exist',
        'pos': 'v',
        'domain': 'action',
        'usage': 'Existential verb; "they shall be"; "it will become"',
        'cognates_en': 'Heb: kun (to be established); Ar: kana',
    },
    '\u1260\u12a5': {
        'english': 'to come, to enter, to arrive',
        'pos': 'v',
        'domain': 'action',
        'usage': 'Coming of God in judgment; entering the holy place',
        'cognates_en': 'Heb: bo; Ar: ba-a',
    },
    '\u1260\u12d8\u1210': {
        'english': 'to be many, to multiply, to be abundant',
        'pos': 'v',
        'domain': 'action',
        'usage': 'The many sins; the multitude of the wicked',
    },
    '\u1348\u1240\u12f0': {
        'english': 'to judge, to decree, to punish',
        'pos': 'v',
        'domain': 'action',
        'usage': 'Gods judgment on the Watchers and sinners',
    },
    '\u121d\u1215\u122d': {
        'english': 'to have mercy, to be compassionate',
        'pos': 'v',
        'domain': 'action',
        'usage': 'Gods compassion toward the righteous',
    },
    '\u1218\u1345\u12a5': {
        'english': 'to come, to arrive, to approach',
        'pos': 'v',
        'domain': 'action',
        'usage': 'The coming day of judgment',
    },
    '\u1228\u12a5\u12ed': {
        'english': 'to see, to behold, to perceive',
        'pos': 'v',
        'domain': 'action',
        'usage': 'Enochs visions; "I saw"; beholding the Holy One',
        'cognates_en': 'Heb: raah; Ar: ra-a',
    },
    '\u1230\u121d\u12d0': {
        'english': 'to hear, to listen, to obey',
        'pos': 'v',
        'domain': 'action',
        'usage': '"I heard all things"; heeding divine instruction',
        'cognates_en': 'Heb: shama; Ar: samia',
    },
    '\u134d\u1230\u1235': {
        'english': 'to pour out, to flow, to overflow',
        'pos': 'v',
        'domain': 'action',
        'usage': 'Pouring out of wrath; flowing waters',
    },
    '\u1208\u12a0\u12a8': {
        'english': 'to send, to dispatch',
        'pos': 'v',
        'domain': 'action',
        'usage': 'God sending angels; dispatching messengers',
        'cognates_en': 'Heb: lakh (to go); related to malakh',
    },
    '\u1218\u1228\u1228': {
        'english': 'to choose, to select, to elect',
        'pos': 'v',
        'domain': 'action',
        'usage': 'Choosing the elect; the chosen ones',
    },

    # === GRAMMAR WORDS ===
    '\u12c8': {
        'english': 'and',
        'pos': 'conj',
        'domain': 'grammar',
        'usage': 'Most common conjunction; connects words and clauses',
        'cognates_en': 'Heb: ve/va; Ar: wa',
    },
    '\u1260': {
        'english': 'in, by, with, at',
        'pos': 'prep',
        'domain': 'grammar',
        'usage': 'Locative/instrumental preposition',
        'cognates_en': 'Heb: be; Ar: bi',
    },
    '\u1208': {
        'english': 'for, to, unto',
        'pos': 'prep',
        'domain': 'grammar',
        'usage': 'Dative/purpose preposition',
        'cognates_en': 'Heb: le; Ar: li',
    },
    '\u12d8': {
        'english': 'of, which, who, that',
        'pos': 'pron',
        'domain': 'grammar',
        'usage': 'Relative pronoun; genitive marker',
        'cognates_en': 'Heb: ze/zeh; Ar: dha/dhu',
    },
    '\u12a5\u121d': {
        'english': 'from, out of',
        'pos': 'prep',
        'domain': 'grammar',
        'usage': 'Ablative preposition: separation, origin',
    },
    '\u12a5\u120d': {
        'english': 'those who, they who',
        'pos': 'pron',
        'domain': 'grammar',
        'usage': 'Relative pronoun plural: "those who will be living"',
    },
    '\u12a5\u1295\u12d8': {
        'english': 'while, when, as',
        'pos': 'conj',
        'domain': 'grammar',
        'usage': 'Temporal conjunction: "while he spoke"',
    },
    '\u12a9\u120d': {
        'english': 'all, every, each',
        'pos': 'adj',
        'domain': 'grammar',
        'usage': 'Universal quantifier: "all the righteous"',
        'cognates_en': 'Heb: kol; Ar: kull',
    },
    '\u12a0\u120d\u1266': {
        'english': 'there is not, without',
        'pos': 'part',
        'domain': 'grammar',
        'usage': 'Negation of existence',
    },
    '\u12a2': {
        'english': 'not (negation)',
        'pos': 'part',
        'domain': 'grammar',
        'usage': 'Verbal negation particle',
    },

    # === TEMPORAL / ABSTRACT ===
    '\u12ed\u12d0\u1234\u1275': {
        'english': 'day of tribulation, time of distress',
        'pos': 'n',
        'domain': 'temporal',
        'usage': 'The eschatological day of judgment and tribulation',
    },
    '\u1275\u12cd\u120d\u12f5': {
        'english': 'generation, offspring, lineage',
        'pos': 'n',
        'domain': 'temporal',
        'usage': 'Future generations; "not for this generation but for a remote one"',
        'cognates_en': 'Heb: toledot; Ar: walad',
    },
    '\u1230\u12a0\u1275': {
        'english': 'hour, time, moment',
        'pos': 'n',
        'domain': 'temporal',
        'usage': 'Appointed times; hours of the day',
    },
    '\u121b\u12a5\u1270\u12ed': {
        'english': 'two hundred',
        'pos': 'num',
        'domain': 'temporal',
        'usage': 'The 200 Watchers who descended on Mount Hermon',
    },
    '\u1230\u1208\u1235': {
        'english': 'three',
        'pos': 'num',
        'domain': 'temporal',
    },
    '\u121d\u1235\u1320\u122d': {
        'english': 'secret, mystery, hidden thing',
        'pos': 'n',
        'domain': 'abstract',
        'usage': 'The forbidden secrets the Watchers taught humanity',
    },
    '\u1243\u120d': {
        'english': 'word, speech, matter, thing',
        'pos': 'n',
        'domain': 'abstract',
        'usage': '"The words of the blessing" - opening of 1 Enoch',
        'cognates_en': 'Heb: qol (voice); Ar: qawl',
    },
    '\u134d\u132d\u12c8\u1275': {
        'english': 'sorcery, enchantment, magic arts',
        'pos': 'n',
        'domain': 'abstract',
        'usage': 'The forbidden arts taught by the Watchers to women',
    },
}


def get_base_consonant(char):
    """Get the base consonant (1st order) of a Ge'ez character."""
    cp = ord(char)
    if 0x1200 <= cp <= 0x137F:
        return chr(cp - ((cp - 0x1200) % 8))
    return char


def to_consonantal(word):
    """Convert word to consonantal skeleton."""
    return ''.join(get_base_consonant(c) for c in word)


def find_root_match(word, root_defs):
    """Try to find a matching root definition for a word."""
    # Direct match
    if word in root_defs:
        return root_defs[word]

    # Check the 'root' field if available
    # Try consonantal match
    word_cons = to_consonantal(word)
    for root, defn in root_defs.items():
        if to_consonantal(root) == word_cons:
            return defn

    return None


def main():
    print("=" * 60)
    print("ENRICH: Modern English Definitions")
    print("=" * 60)

    with open(WORDS_FILE, 'r', encoding='utf-8') as f:
        words = json.load(f)

    enriched = 0
    already_had = 0
    no_match = 0

    for word, info in words.items():
        # Try to find root definition
        defn = find_root_match(word, ROOT_DEFINITIONS)

        # Also try the stored root
        if not defn and info.get('root'):
            defn = find_root_match(info['root'], ROOT_DEFINITIONS)

        # Try stripping common prefixes to find root
        if not defn:
            prefixes = [
                '\u12c8', '\u1260', '\u1208', '\u12d8',
                '\u12a5\u121d', '\u12c8\u12a5\u121d',
                '\u12c8\u1260', '\u12c8\u1208',
                '\u12ed', '\u1275', '\u12a5',
            ]
            for p in prefixes:
                if word.startswith(p) and len(word) > len(p) + 1:
                    remainder = word[len(p):]
                    defn = find_root_match(remainder, ROOT_DEFINITIONS)
                    if defn:
                        break
                    # Try stripping a second prefix
                    for p2 in prefixes:
                        if remainder.startswith(p2) and len(remainder) > len(p2) + 1:
                            inner = remainder[len(p2):]
                            defn = find_root_match(inner, ROOT_DEFINITIONS)
                            if defn:
                                break
                    if defn:
                        break

        if defn:
            # Add enrichment data
            info['english_definition'] = defn['english']
            info['part_of_speech'] = defn['pos']
            info['semantic_domain'] = defn['domain']
            if 'usage' in defn:
                info['enoch_usage'] = defn['usage']
            if 'cognates_en' in defn:
                info['cognates_english'] = defn['cognates_en']
            enriched += 1
        else:
            no_match += 1

    # Save
    with open(WORDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(words, f, ensure_ascii=False, indent=2)

    print(f"\n  Words enriched:   {enriched}/{len(words)} ({enriched/len(words)*100:.1f}%)")
    print(f"  No match found:   {no_match}")
    print(f"  Total words:      {len(words)}")

    # Show domain distribution
    domains = {}
    for w, i in words.items():
        d = i.get('semantic_domain', 'unclassified')
        domains[d] = domains.get(d, 0) + 1

    print(f"\n  SEMANTIC DOMAINS:")
    for d, c in sorted(domains.items(), key=lambda x: -x[1]):
        print(f"    {d}: {c}")


if __name__ == '__main__':
    main()
