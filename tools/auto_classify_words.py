#!/usr/bin/env python3
"""
Auto-classify remaining unclassified words using existing definitions.
=====================================================================
For compound words (prefix + root), we:
1. Extract the root definition from the compound definition
2. Look up the root in our enrichment table
3. Assign domain/POS from the root
4. For grammar-only words (just prefixes), classify as 'grammar'

Copyright (c) 2026 Tammy L Casey. All rights reserved.
"""

import json
import os
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.join(SCRIPT_DIR, '..')
WORDS_FILE = os.path.join(PROJECT_ROOT, 'words.json')

# Domain classification by definition keywords
DOMAIN_KEYWORDS = {
    'divine': [
        'god', 'lord', 'holy', 'sacred', 'bless', 'blessing', 'prayer',
        'righteous', 'righteousness', 'sin', 'transgress', 'curse', 'glory',
        'praise', 'mercy', 'compassion', 'covenant', 'judgment', 'judge',
        'wrath', 'salvation', 'elect', 'chosen', 'worship', 'temple',
        'altar', 'oath', 'swear', 'spirit', 'soul',
    ],
    'angelic': [
        'angel', 'watcher', 'messenger', 'archangel', 'seraph', 'cherubin',
        'semyaza', 'azazel', 'raphael', 'michael', 'gabriel', 'uriel',
        'sariel', 'rameel', 'kokabel', 'baraqiel', 'araqiel',
    ],
    'nature': [
        'heaven', 'sky', 'earth', 'mountain', 'water', 'sea', 'river',
        'tree', 'plant', 'star', 'sun', 'moon', 'wind', 'fire', 'light',
        'dark', 'rain', 'cloud', 'stone', 'rock', 'valley', 'spring',
        'fountain', 'garden', 'fruit', 'seed', 'flower', 'field',
        'desert', 'abyss', 'deep', 'snow', 'dew', 'thunder', 'lightning',
        'iron', 'silver', 'gold', 'bronze', 'metal', 'sword',
    ],
    'person': [
        'man', 'human', 'person', 'child', 'children', 'son', 'daughter',
        'father', 'mother', 'wife', 'husband', 'king', 'ruler', 'chief',
        'leader', 'people', 'nation', 'tribe', 'giant', 'mighty',
        'blood', 'flesh', 'body', 'face', 'hand', 'eye', 'mouth',
        'head', 'foot', 'bone', 'name',
    ],
    'action': [
        'come', 'go', 'see', 'hear', 'speak', 'say', 'tell', 'know',
        'make', 'do', 'give', 'take', 'send', 'bring', 'destroy',
        'kill', 'die', 'live', 'eat', 'drink', 'sleep', 'wake',
        'walk', 'run', 'fall', 'rise', 'sit', 'stand', 'open',
        'close', 'build', 'break', 'teach', 'learn', 'write', 'read',
        'call', 'answer', 'fight', 'pour', 'bind', 'loose', 'turn',
        'return', 'remember', 'forget', 'cry', 'weep', 'rejoice',
        'fear', 'tremble', 'love', 'hate', 'contend', 'strive',
        'dwell', 'enter', 'descend', 'ascend', 'reveal', 'hide',
        'punish', 'reward', 'forgive', 'multiply', 'divide',
    ],
    'temporal': [
        'day', 'night', 'time', 'year', 'month', 'hour', 'moment',
        'generation', 'age', 'eternal', 'forever', 'beginning', 'end',
        'first', 'last', 'until', 'before', 'after', 'when',
        'hundred', 'thousand', 'three', 'seven', 'ten', 'twelve',
        'two hundred', 'number', 'count',
    ],
    'abstract': [
        'word', 'speech', 'voice', 'secret', 'mystery', 'knowledge',
        'wisdom', 'truth', 'lie', 'peace', 'war', 'deed', 'work',
        'act', 'power', 'strength', 'sign', 'wonder', 'vision',
        'dream', 'thought', 'sorcery', 'enchantment', 'magic',
        'provision', 'sustenance', 'portion', 'section',
    ],
    'grammar': [
        'and', 'but', 'or', 'not', 'negation', 'from', 'in', 'to',
        'for', 'with', 'upon', 'above', 'below', 'which', 'who',
        'that', 'this', 'those', 'these', 'all', 'every', 'each',
        'you ', 'he ', 'she ', 'they ', 'we ', 'i ', 'them', 'him',
        'her', 'it ', 'my', 'your', 'his', 'their', 'our',
        'pronoun', 'prefix', 'conjunction', 'preposition', 'particle',
    ],
}

# POS inference from definition patterns
POS_PATTERNS = [
    (r'^(and |from |in/by |for/to |of/which |not )\+', 'compound'),
    (r'(pronoun|pronominal)', 'pron'),
    (r'(proper name|Sinai|Enoch|Hermon)', 'prop'),
    (r'^(he |she |they |I |we |you |it )(do|make|come|go|see|hear|speak|shall|will|become)', 'v'),
    (r'(imperfect|perfect|infinitive|imperative|subjunctive|jussive)', 'v'),
    (r'(deed|work|act|word|speech|peace|judgment|sin|glory|blessing)', 'n'),
    (r'(mountain|water|star|heaven|earth|tree|fire|light)', 'n'),
    (r'(angel|messenger|son|child|man|human|king|ruler)', 'n'),
    (r'(righteous|holy|sacred|great|mighty|good|evil)', 'adj'),
    (r'(all|every|each|many|few|much)', 'adj'),
    (r'(and|but|or|because|until|while|when)', 'conj'),
    (r'(in|from|to|for|with|upon|above|below|on)', 'prep'),
    (r'(not|no|never|without)', 'part'),
]


def classify_domain(definition):
    """Classify a word's domain based on definition keywords."""
    if not definition:
        return 'unclassified'

    defn_lower = definition.lower()

    # Strip prefix meanings to focus on root
    # "and + peace" -> "peace"
    # "from + judgment" -> "judgment"
    root_part = re.sub(r'^(and |from |in/by |for/to |of/which |not |in |on )\+ ', '', defn_lower)
    root_part = re.sub(r'^(and |from |in/by |for/to |of/which |not |in |on )\+ ', '', root_part)

    # Score each domain
    scores = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw in root_part:
                score += 1
        if score > 0:
            scores[domain] = score

    if not scores:
        return 'unclassified'

    # Return highest scoring domain
    return max(scores, key=scores.get)


def infer_pos(definition):
    """Infer part of speech from definition text."""
    if not definition:
        return ''

    defn_lower = definition.lower()

    for pattern, pos in POS_PATTERNS:
        if re.search(pattern, defn_lower):
            return pos

    return ''


def extract_english_definition(definition):
    """Extract a clean English definition from compound definitions.

    "and + peace, completeness, well-being" -> "peace, completeness, well-being"
    "from + judgment, ruling, decision" -> "judgment, ruling, decision"
    """
    if not definition:
        return ''

    # Strip prefix meanings
    clean = re.sub(
        r'^(and \+ |from \+ |in/by \+ |for/to \+ |of/which \+ |not \+ |'
        r'in \+ |on \+ |he/it |they |she/you |and |from )',
        '', definition
    )

    # Take first sentence/phrase
    clean = clean.split(';')[0].strip()
    clean = clean.split('(')[0].strip()

    # Remove trailing punctuation
    clean = clean.rstrip(',. ')

    # Capitalize first letter
    if clean:
        clean = clean[0].upper() + clean[1:]

    return clean


def main():
    print("=" * 60)
    print("AUTO-CLASSIFY: Remaining Unclassified Words")
    print("=" * 60)

    with open(WORDS_FILE, 'r', encoding='utf-8') as f:
        words = json.load(f)

    classified = 0
    pos_added = 0

    for word, info in words.items():
        domain = info.get('semantic_domain', '')
        defn = info.get('definition', '')

        # Classify domain if missing
        if not domain or domain == 'unclassified':
            new_domain = classify_domain(defn)
            if new_domain != 'unclassified':
                info['semantic_domain'] = new_domain
                classified += 1

        # Add POS if missing
        if not info.get('part_of_speech'):
            pos = infer_pos(defn)
            if pos:
                info['part_of_speech'] = pos
                pos_added += 1

        # Add clean english_definition if missing
        if not info.get('english_definition'):
            clean = extract_english_definition(defn)
            if clean:
                info['english_definition'] = clean

    # Save
    with open(WORDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(words, f, ensure_ascii=False, indent=2)

    # Stats
    total = len(words)
    domains = {}
    for w, i in words.items():
        d = i.get('semantic_domain', 'unclassified')
        domains[d] = domains.get(d, 0) + 1

    has_english = sum(1 for w, i in words.items() if i.get('english_definition'))
    has_pos = sum(1 for w, i in words.items() if i.get('part_of_speech'))
    has_domain = sum(1 for w, i in words.items()
                     if i.get('semantic_domain') and i.get('semantic_domain') != 'unclassified')

    print(f"\n  Newly classified domains: {classified}")
    print(f"  Newly added POS:         {pos_added}")
    print(f"\n  COVERAGE:")
    print(f"    English definitions: {has_english}/{total} ({has_english/total*100:.1f}%)")
    print(f"    Part of speech:      {has_pos}/{total} ({has_pos/total*100:.1f}%)")
    print(f"    Semantic domain:     {has_domain}/{total} ({has_domain/total*100:.1f}%)")

    print(f"\n  DOMAIN DISTRIBUTION:")
    for d, c in sorted(domains.items(), key=lambda x: -x[1]):
        print(f"    {d:15s}: {c:3d} ({c/total*100:.1f}%)")


if __name__ == '__main__':
    main()
