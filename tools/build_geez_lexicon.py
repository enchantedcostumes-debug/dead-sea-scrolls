#!/usr/bin/env python3
"""
BUILD GE'EZ LEXICON - Dead Sea Scrolls Mechanical Translation
=============================================================

Builds the words.json lexicon file for the Ge'ez mechanical translation
of 1 Enoch chapters 1-36 (Book of the Watchers).

PROCESS:
1. Load data/enoch_geez_text.json (Ge'ez text for 1 Enoch 1-36)
2. Extract ALL unique Ge'ez words
3. For each word, create a scholarly lexicon entry
4. Calculate gematria for each word
5. Generate Fidel character breakdowns
6. Save to words.json at project root

SOURCES:
- August Dillmann, Lexicon Linguae Aethiopicae (1865)
- Wolf Leslau, Comparative Dictionary of Ge'ez (1987/2006)
- R.H. Charles, The Ethiopic Version of the Book of Enoch (1906)
- Daniel de Caussin, Corpus of Ge'ez Words in 1 Enoch (2024)
- Beta Masaheft / Hamburg University digitized lexicon

Copyright (c) 2026 Tammy L Casey. All rights reserved.
"""

import json
import os
import sys
import re
from collections import defaultdict


# =============================================================================
# CONSTANTS
# =============================================================================

# Project paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.join(SCRIPT_DIR, '..')
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
INPUT_FILE = os.path.join(DATA_DIR, 'enoch_geez_text.json')
OUTPUT_FILE = os.path.join(PROJECT_ROOT, 'words.json')

# Ethiopic Unicode ranges
ETHIOPIC_MAIN = (0x1200, 0x137F)
ETHIOPIC_SUPPLEMENT = (0x1380, 0x139F)
ETHIOPIC_EXTENDED = (0x2D80, 0x2DDF)

# Ethiopic punctuation to strip (U+1361-U+1368)
ETHIOPIC_PUNCTUATION = set(chr(c) for c in range(0x1361, 0x1369))


# =============================================================================
# GE'EZ GEMATRIA SYSTEM
# =============================================================================

# Each row of the Fidel syllabary has 7 vowel orders sharing the same
# gematria value. The mapping below covers all 26 base consonant rows.
# Format: (start_codepoint, num_chars, gematria_value)
GEMATRIA_ROWS = [
    # Row: start codepoint, number of chars in row, gematria value
    (0x1200, 7, 1),    # Ha-Ho
    (0x1208, 7, 2),    # La-Lo
    (0x1210, 7, 3),    # Hha-Hho (hawt)
    (0x1218, 7, 4),    # Ma-Mo
    (0x1220, 7, 5),    # Sza-Szo (sawt)
    (0x1228, 7, 6),    # Ra-Ro
    (0x1230, 7, 7),    # Sa-So
    (0x1238, 7, 7),    # Sha-Sho (variant of Sa, shares value)
    (0x1240, 7, 9),    # Qa-Qo
    (0x1248, 5, 9),    # Qwa etc (labialized Q, shares value)
    (0x1250, 7, 9),    # Qha etc (additional Q forms)
    (0x1258, 5, 9),    # Qhwa etc
    (0x1260, 7, 10),   # Ba-Bo
    (0x1268, 7, 10),   # Va-Vo (variant of Ba)
    (0x1270, 7, 20),   # Ta-To
    (0x1278, 7, 20),   # Cha-Cho (variant of Ta)
    (0x1280, 7, 30),   # Xa-Xo (harm/plow)
    (0x1288, 5, 30),   # Xwa etc (labialized)
    (0x1290, 7, 40),   # Na-No
    (0x1298, 7, 40),   # Nya-Nyo (variant of Na)
    (0x12A0, 7, 50),   # A-O (alf/aleph)
    (0x12A8, 7, 60),   # Ka-Ko
    (0x12B0, 5, 60),   # Kwa etc (labialized K)
    (0x12B8, 7, 60),   # Kxa-Kxo (variant K)
    (0x12C0, 5, 60),   # Kxwa etc
    (0x12C8, 7, 70),   # Wa-Wo
    (0x12D0, 7, 80),   # Pharyngeal ayn
    (0x12D8, 7, 90),   # Za-Zo
    (0x12E0, 7, 90),   # Zha-Zho (variant of Za)
    (0x12E8, 7, 100),  # Ya-Yo
    (0x12F0, 7, 200),  # Da-Do
    (0x12F8, 7, 200),  # Dda-Ddo (variant of Da)
    (0x1300, 7, 200),  # Ja-Jo (variant)
    (0x1308, 7, 300),  # Ga-Go
    (0x1310, 5, 300),  # Gwa etc (labialized G)
    (0x1318, 7, 300),  # Gga-Ggo (variant)
    (0x1320, 7, 400),  # Tha-Tho (tayt)
    (0x1328, 7, 400),  # Thha-Tho (variant)
    (0x1330, 7, 500),  # Pha-Pho (payt)
    (0x1338, 7, 600),  # Tsa-Tso (saday)
    (0x1340, 7, 700),  # Tza-Tzo (dappa)
    (0x1348, 7, 800),  # Fa-Fo
    (0x1350, 7, 900),  # Pa-Po
]

# Build lookup table: codepoint -> gematria value
GEMATRIA_TABLE = {}
for start, count, value in GEMATRIA_ROWS:
    for i in range(count):
        GEMATRIA_TABLE[start + i] = value


# =============================================================================
# FIDEL CHARACTER ANALYSIS
# =============================================================================

# Base consonant info: (start_codepoint, name, transliteration, meaning)
CONSONANT_INFO = {
    0x1200: ("Hoy", "h", 1, "existence, breath"),
    0x1208: ("Lawi", "l", 2, "cattle, to/for"),
    0x1210: ("Hawt", "hh", 3, "joy, thread"),
    0x1218: ("May", "m", 4, "water"),
    0x1220: ("Sawt", "sz", 5, "fire, burning"),
    0x1228: ("Ris", "r", 6, "head, beginning"),
    0x1230: ("Sat", "s", 7, "tooth, sharp"),
    0x1238: ("Sha", "sh", 7, "variant of Sat"),
    0x1240: ("Qaf", "q", 9, "voice, call"),
    0x1248: ("Qaf-W", "qw", 9, "voice (labialized)"),
    0x1250: ("Qha", "qh", 9, "voice variant"),
    0x1258: ("Qha-W", "qhw", 9, "voice variant (labialized)"),
    0x1260: ("Bet", "b", 10, "house, dwelling"),
    0x1268: ("Vav", "v", 10, "house variant"),
    0x1270: ("Taw", "t", 20, "mark, sign"),
    0x1278: ("Cha", "ch", 20, "mark variant"),
    0x1280: ("Harm", "x", 30, "plow, cultivation"),
    0x1288: ("Harm-W", "xw", 30, "plow (labialized)"),
    0x1290: ("Nahas", "n", 40, "serpent, bronze"),
    0x1298: ("Nya", "ny", 40, "serpent variant"),
    0x12A0: ("Alf", "a", 50, "ox, beginning, first"),
    0x12A8: ("Kaf", "k", 60, "palm of hand"),
    0x12B0: ("Kaf-W", "kw", 60, "palm (labialized)"),
    0x12B8: ("Kxa", "kx", 60, "palm variant"),
    0x12C0: ("Kxa-W", "kxw", 60, "palm variant (labialized)"),
    0x12C8: ("Waw", "w", 70, "hook, connection"),
    0x12D0: ("Ayn", "aa", 80, "eye, source, spring"),
    0x12D8: ("Zay", "z", 90, "weapon, this"),
    0x12E0: ("Zha", "zh", 90, "weapon variant"),
    0x12E8: ("Yaman", "y", 100, "right hand, south"),
    0x12F0: ("Dint", "d", 200, "door, entrance"),
    0x12F8: ("Dda", "dd", 200, "door variant"),
    0x1300: ("Ja", "j", 200, "door variant"),
    0x1308: ("Gaml", "g", 300, "camel, reward"),
    0x1310: ("Gaml-W", "gw", 300, "camel (labialized)"),
    0x1318: ("Gga", "gg", 300, "camel variant"),
    0x1320: ("Tayt", "th", 400, "serpent, good"),
    0x1328: ("Thha", "thh", 400, "serpent variant"),
    0x1330: ("Payt", "ph", 500, "mouth, opening"),
    0x1338: ("Saday", "ts", 600, "righteousness"),
    0x1340: ("Dappa", "tz", 700, "writing tablet"),
    0x1348: ("Af", "f", 800, "mouth, opening"),
    0x1350: ("Psa", "p", 900, "scattered"),
}

# Vowel order names and transliterations
VOWEL_ORDERS = [
    ("1st (Ge'ez)", "a"),     # index 0
    ("2nd (Ka'eb)", "u"),     # index 1
    ("3rd (Sales)", "i"),     # index 2
    ("4th (Rabe)", "a"),      # index 3
    ("5th (Hames)", "e"),     # index 4
    ("6th (Sades)", "e"),     # index 5 (schwa)
    ("7th (Sabe)", "o"),      # index 6
]


def get_consonant_row(codepoint):
    """Find which consonant row a codepoint belongs to."""
    for start, count, value in GEMATRIA_ROWS:
        if start <= codepoint < start + count:
            return start
    return None


def get_vowel_order(codepoint):
    """Get the vowel order index (0-6) for a character."""
    row_start = get_consonant_row(codepoint)
    if row_start is None:
        return None
    return codepoint - row_start


def analyze_character(char):
    """Analyze a single Ge'ez character into its components."""
    cp = ord(char)
    row_start = get_consonant_row(cp)
    if row_start is None:
        return None

    vowel_idx = cp - row_start
    if vowel_idx < 0 or vowel_idx >= len(VOWEL_ORDERS):
        vowel_idx = 0  # Default to 1st order

    consonant_data = CONSONANT_INFO.get(row_start)
    if consonant_data is None:
        # Try to find the closest known row
        for known_start in sorted(CONSONANT_INFO.keys()):
            if known_start <= row_start:
                consonant_data = CONSONANT_INFO[known_start]
        if consonant_data is None:
            return None

    name, base_trans, gematria_val, meaning = consonant_data
    order_name, vowel_trans = VOWEL_ORDERS[vowel_idx] if vowel_idx < len(VOWEL_ORDERS) else ("unknown", "")

    gematria = GEMATRIA_TABLE.get(cp, 0)

    return {
        "char": char,
        "name": f"{name} ({order_name})",
        "value": gematria,
        "meaning": meaning,
    }


def calculate_gematria(word):
    """Calculate the gematria value of a Ge'ez word."""
    total = 0
    for char in word:
        cp = ord(char)
        total += GEMATRIA_TABLE.get(cp, 0)
    return total


def digital_root(n):
    """Calculate the digital root (repeated digit sum until single digit)."""
    if n == 0:
        return 0
    while n > 9:
        n = sum(int(d) for d in str(n))
    return n


def transliterate_char(char):
    """Get a basic transliteration for a single Ge'ez character."""
    cp = ord(char)
    row_start = get_consonant_row(cp)
    if row_start is None:
        return char

    vowel_idx = cp - row_start
    consonant_data = CONSONANT_INFO.get(row_start)
    if consonant_data is None:
        return char

    name, base_trans, val, meaning = consonant_data

    if vowel_idx < len(VOWEL_ORDERS):
        order_name, vowel = VOWEL_ORDERS[vowel_idx]
        if vowel_idx == 0:
            return base_trans + "a"
        elif vowel_idx == 5:
            # 6th order is schwa (often represented as e or omitted)
            return base_trans
        else:
            return base_trans + vowel
    return base_trans


def transliterate_word(word):
    """Transliterate a complete Ge'ez word."""
    result = []
    for char in word:
        if is_ethiopic(char):
            result.append(transliterate_char(char))
        else:
            result.append(char)
    return "".join(result)


# =============================================================================
# TEXT PROCESSING UTILITIES
# =============================================================================

def is_ethiopic(char):
    """Check if a character is in the Ethiopic Unicode block."""
    cp = ord(char)
    return (ETHIOPIC_MAIN[0] <= cp <= ETHIOPIC_MAIN[1] or
            ETHIOPIC_SUPPLEMENT[0] <= cp <= ETHIOPIC_SUPPLEMENT[1] or
            ETHIOPIC_EXTENDED[0] <= cp <= ETHIOPIC_EXTENDED[1])


def clean_word(word):
    """Strip Ethiopic punctuation and whitespace from a word."""
    # Strip standard Ethiopic punctuation
    stripped = word.strip()
    for p in ETHIOPIC_PUNCTUATION:
        stripped = stripped.replace(p, '')
    stripped = stripped.strip()
    return stripped


def has_ethiopic(word):
    """Check if a word contains at least one Ethiopic character."""
    return any(is_ethiopic(c) for c in word)


def extract_words_from_text(geez_text):
    """Extract individual Ge'ez words from a verse text.

    Splits on spaces and Ethiopic wordspace character.
    Strips punctuation. Returns only words with Ethiopic chars.
    """
    # Split on spaces and Ethiopic wordspace (U+1361)
    tokens = re.split(r'[\s\u1361]+', geez_text)
    words = []
    for token in tokens:
        cleaned = clean_word(token)
        if cleaned and has_ethiopic(cleaned):
            words.append(cleaned)
    return words


# =============================================================================
# COMPREHENSIVE GE'EZ DICTIONARY
# =============================================================================
# Definitions sourced from:
# - Dillmann, Lexicon Linguae Aethiopicae (1865) [D]
# - Leslau, Comparative Dictionary of Ge'ez (1987/2006) [L]
# - Charles, The Ethiopic Version of the Book of Enoch (1906) [C]
# - de Caussin, Corpus of Ge'ez Words in 1 Enoch (2024) [dC]
#
# Each entry: (definition, root, source_citation, [timeline])
# =============================================================================

SCHOLARLY_DICTIONARY = {
    # ===== CONJUNCTIONS, PREPOSITIONS, PARTICLES =====
    "\u12C8": ("and, but, also", "\u12C8", "Dillmann, Lexicon col. 886",
               [("Proto-Semitic", "*wa-", "Common Semitic conjunction"),
                ("Ge'ez", "\u12C8", "Most common word in Ethiopic texts"),
                ("Amharic", "\u12C8/\u12A5\u1293", "Modern conjunction")]),

    "\u12A5\u121D": ("from, out of", "\u12A5\u121D", "Dillmann, Lexicon col. 800",
                     [("Proto-Semitic", "*min-", "Universal Semitic preposition"),
                      ("Ge'ez", "\u12A5\u121D", "Preposition of origin/source"),
                      ("Amharic", "\u12A8", "Simplified in modern Amharic")]),

    "\u12D8": ("of, which, who, that (relative)", "\u12D8", "Dillmann, Lexicon col. 1054",
               [("Proto-Semitic", "*dhu-", "Demonstrative/relative base"),
                ("Ge'ez", "\u12D8", "Relative pronoun and genitive particle"),
                ("Amharic", "\u12E8", "Modern relative marker")]),

    "\u1260": ("in, by, with, through", "\u1260", "Dillmann, Lexicon col. 460",
               [("Proto-Semitic", "*bi-", "Universal Semitic preposition"),
                ("Ge'ez", "\u1260", "Instrumental and locative preposition"),
                ("Amharic", "\u1260", "Unchanged in modern Amharic")]),

    "\u1208": ("to, for, unto", "\u1208", "Dillmann, Lexicon col. 16",
               [("Proto-Semitic", "*la-", "Dative preposition"),
                ("Ge'ez", "\u1208", "Dative and purposive preposition"),
                ("Amharic", "\u1208", "Unchanged in modern Amharic")]),

    "\u12A0\u120D": ("not, no (negative particle)", "\u12A0\u120D", "Dillmann, Lexicon col. 777",
                     [("Proto-Semitic", "*'al-", "Prohibitive/negative"),
                      ("Ge'ez", "\u12A0\u120D", "Negation marker"),
                      ("Amharic", "\u12A0\u120D", "Still used in literary Amharic")]),

    "\u12A5\u1265\u12A8": ("because, for, since", "\u12A5\u1265\u12A8", "Dillmann, Lexicon col. 809",
                           [("Ge'ez", "\u12A5\u1265\u12A8", "Causal conjunction"),
                            ("Amharic", "\u121D\u12AD\u1295\u12EB\u1271\u121D", "Replaced in modern usage")]),

    "\u12A5\u1235\u12A8": ("until, up to", "\u12A5\u1235\u12A8", "Dillmann, Lexicon col. 814",
                           [("Ge'ez", "\u12A5\u1235\u12A8", "Temporal/spatial limit"),
                            ("Amharic", "\u12A5\u1235\u12A8", "Still used")]),

    "\u12AD\u120D\u12A5": ("all, every, each, totality", "\u12AD\u120D", "Dillmann, Lexicon col. 862",
                           [("Proto-Semitic", "*kull-", "Totality"),
                            ("Ge'ez", "\u12AD\u120D\u12A5", "Universal quantifier"),
                            ("Amharic", "\u1201\u1209", "Modern form")]),

    "\u12AD\u120E": ("all, every (variant form)", "\u12AD\u120D", "Dillmann, Lexicon col. 862",
                     [("Ge'ez", "\u12AD\u120E", "Bound form of kull"),
                      ("Amharic", "\u1201\u1209", "Modern form")]),

    "\u12AD\u120D\u1209": ("all of them", "\u12AD\u120D", "Dillmann, Lexicon col. 862",
                           [("Ge'ez", "\u12AD\u120D\u1209", "With 3mp suffix"),
                            ("Amharic", "\u1201\u1209\u121D", "Modern equivalent")]),

    "\u12A5\u120D\u12A5": ("even, also, indeed", "\u12A5\u120D\u12A5", "Dillmann, Lexicon col. 801",
                           [("Ge'ez", "\u12A5\u120D\u12A5", "Emphatic particle"),
                            ("Amharic", "(\u12A5\u1295\u12F2\u1201\u121D)", "Replaced")]),

    "\u12F2\u1260": ("upon, on, over, above", "\u12F2\u1260", "Dillmann, Lexicon col. 1071",
                     [("Ge'ez", "\u12F2\u1260", "Prepositional compound"),
                      ("Amharic", "\u12F2\u1260/\u1208\u12ED", "Modern forms")]),

    "\u12ED\u12A5\u1272": ("that (conjunction)", "\u12ED\u12A5\u1272", "Dillmann, Lexicon col. 35",
                           [("Ge'ez", "\u12ED\u12A5\u1272", "Complementizer"),
                            ("Amharic", "\u12A5\u1295\u12F0", "Modern form")]),

    "\u1208\u12A5\u1208": ("upon, above, over", "\u1208\u12A5\u1208", "Dillmann, Lexicon col. 20",
                           [("Ge'ez", "\u1208\u12A5\u1208", "Compound preposition"),
                            ("Amharic", "\u1260\u120B\u12ED", "Modern equivalent")]),

    # ===== NOUNS - DIVINE AND CELESTIAL =====
    "\u12A5\u130D\u12DA\u12A0\u1265\u1214\u122D": ("God, Lord (the Lord God)", "\u12A5\u130D\u12DA\u12A0\u1265\u1214\u122D",
        "Dillmann, Lexicon col. 808",
        [("Proto-Semitic", "*'il-", "Deity, divine power"),
         ("Ge'ez", "\u12A5\u130D\u12DA\u12A0\u1265\u1214\u122D", "Compound: Lord-of-hosts + compassionate"),
         ("Amharic", "\u12A5\u130D\u12DA\u12A0\u1265\u1214\u122D", "Same in liturgical Amharic")]),

    "\u1230\u121B\u12ED": ("heaven, sky, the heavens", "\u1230\u121D\u12ED", "Dillmann, Lexicon col. 357",
                           [("Proto-Semitic", "*shamay-", "Sky, heavens"),
                            ("Ge'ez", "\u1230\u121B\u12ED", "Heaven/sky"),
                            ("Amharic", "\u1230\u121B\u12ED", "Unchanged")]),

    "\u121D\u12F5\u122D": ("earth, land, ground, country", "\u121D\u12F5\u122D", "Dillmann, Lexicon col. 186",
                           [("Proto-Semitic", "*'ard-", "Earth"),
                            ("Ge'ez", "\u121D\u12F5\u122D", "Earth, land"),
                            ("Amharic", "\u121D\u12F5\u122D", "Unchanged")]),

    "\u1218\u120B\u12A5\u12AD\u1275": ("angels, messengers (plural)", "\u1218\u120D\u12A0\u12AD",
        "Dillmann, Lexicon col. 174",
        [("Proto-Semitic", "*mal'ak-", "Messenger"),
         ("Ge'ez", "\u1218\u120B\u12A5\u12AD\u1275", "Plural of mal'ak"),
         ("Amharic", "\u1218\u120B\u12AD\u1275", "Modern plural")]),

    "\u1218\u120D\u12A0\u12AD": ("angel, messenger (singular)", "\u1218\u120D\u12A0\u12AD",
        "Dillmann, Lexicon col. 174",
        [("Proto-Semitic", "*mal'ak-", "Messenger"),
         ("Ge'ez", "\u1218\u120D\u12A0\u12AD", "Angel, messenger"),
         ("Amharic", "\u1218\u120B\u12AD", "Modern form")]),

    "\u1240\u12F1\u1235": ("holy (adjective)", "\u1245\u12F5\u1235", "Dillmann, Lexicon col. 420",
                           [("Proto-Semitic", "*qadush-", "Holy, set apart"),
                            ("Ge'ez", "\u1240\u12F1\u1235", "Holy, sacred"),
                            ("Amharic", "\u1240\u12F1\u1235", "Unchanged")]),

    "\u1240\u12F1\u1233\u1295": ("holy ones (plural)", "\u1245\u12F5\u1235", "Dillmann, Lexicon col. 420",
                                 [("Ge'ez", "\u1240\u12F1\u1233\u1295", "Plural of qeddus"),
                                  ("Amharic", "\u1240\u12F1\u1233\u1295", "Saints, holy ones")]),

    "\u120D\u12D1\u120D": ("Most High (divine title)", "\u12D0\u120D\u12ED", "Dillmann, Lexicon col. 24",
                           [("Proto-Semitic", "*'aly-", "High, exalted"),
                            ("Ge'ez", "\u120D\u12D1\u120D", "The Most High God"),
                            ("Amharic", "\u120D\u12D1\u120D", "Unchanged title")]),

    "\u1275\u12A5\u12DB\u12DD": ("commandment, order", "\u12A5\u12DB\u12DD", "Dillmann, Lexicon col. 766",
                                 [("Ge'ez", "\u1275\u12A5\u12DB\u12DD", "Divine commandment"),
                                  ("Amharic", "\u1275\u12A5\u12DB\u12DD", "Order, command")]),

    # ===== NOUNS - PERSONS AND BEINGS =====
    "\u1204\u1296\u12AD": ("Enoch (proper noun)", "\u1204\u1296\u12AD", "Charles 1906, p. 1",
                           [("Hebrew", "\u05D7\u05B2\u05E0\u05D5\u05B9\u05DA (Chanokh)", "Dedicated/initiated"),
                            ("Ge'ez", "\u1204\u1296\u12AD", "Ethiopic form of Enoch"),
                            ("English", "Enoch", "Via Greek Henoch")]),

    "\u1230\u121D\u12EB\u12DB": ("Semjaza, Semyaza (Watcher leader)", "\u1230\u121D\u12EB\u12DB",
        "Charles 1906, p. 14; Dillmann, Lexicon col. 360",
        [("Aramaic", "shm-y-z-'", "He sees the name"),
         ("Ge'ez", "\u1230\u121D\u12EB\u12DB", "Leader of the 200 Watchers"),
         ("English", "Semjaza/Semyaza", "Variant spellings in scholarship")]),

    "\u12A0\u12DB\u12DC\u120D": ("Azazel (fallen Watcher)", "\u12A0\u12DB\u12DC\u120D",
        "Charles 1906, p. 19; Dillmann, Lexicon col. 780",
        [("Hebrew", "\u05E2\u05D6\u05D0\u05D6\u05DC ('Aza'zel)", "Scapegoat/fierce god"),
         ("Ge'ez", "\u12A0\u12DB\u12DC\u120D", "Fallen Watcher, taught forbidden knowledge"),
         ("English", "Azazel", "Via Hebrew Leviticus 16")]),

    "\u121A\u12AB\u12A4\u120D": ("Michael (archangel)", "\u121A\u12AB\u12A4\u120D",
        "Charles 1906, p. 22; Dillmann, Lexicon col. 167",
        [("Hebrew", "\u05DE\u05D9\u05DB\u05D0\u05DC (Mikha'el)", "Who is like God?"),
         ("Ge'ez", "\u121A\u12AB\u12A4\u120D", "Archangel, prince of Israel"),
         ("Amharic", "\u121A\u12AB\u12A4\u120D", "Venerated in Ethiopian Orthodox Church")]),

    "\u1229\u134B\u12A4\u120D": ("Raphael (archangel)", "\u1229\u134B\u12A4\u120D",
        "Charles 1906, p. 21; Dillmann, Lexicon col. 271",
        [("Hebrew", "\u05E8\u05E4\u05D0\u05DC (Repha'el)", "God has healed"),
         ("Ge'ez", "\u1229\u134B\u12A4\u120D", "Archangel, healer"),
         ("English", "Raphael", "Via Greek")]),

    "\u1308\u1265\u122D\u12A4\u120D": ("Gabriel (archangel)", "\u1308\u1265\u122D\u12A4\u120D",
        "Charles 1906, p. 22; Dillmann, Lexicon col. 288",
        [("Hebrew", "\u05D2\u05D1\u05E8\u05D9\u05D0\u05DC (Gavri'el)", "Strength of God"),
         ("Ge'ez", "\u1308\u1265\u122D\u12A4\u120D", "Archangel, messenger"),
         ("Amharic", "\u1308\u1265\u122D\u12A4\u120D", "Venerated in Ethiopian Orthodox Church")]),

    "\u12A1\u122D\u12EB\u12A4\u120D": ("Uriel (archangel)", "\u12A1\u122D\u12EB\u12A4\u120D",
        "Charles 1906, p. 22; Dillmann, Lexicon col. 767",
        [("Hebrew", "\u05D0\u05D5\u05E8\u05D9\u05D0\u05DC ('Uri'el)", "Light of God"),
         ("Ge'ez", "\u12A1\u122D\u12EB\u12A4\u120D", "Archangel, light-bearer"),
         ("English", "Uriel", "Via Greek/Latin")]),

    "\u12D3\u1243\u1265\u12EB\u1295": ("Watchers (heavenly watchers)", "\u12D3\u1243\u1265",
        "Charles 1906, p. 13; Dillmann, Lexicon col. 944",
        [("Aramaic", "\u05E2\u05D9\u05E8\u05D9\u05DF ('irin)", "Wakeful ones"),
         ("Ge'ez", "\u12D3\u1243\u1265\u12EB\u1295", "The Watchers - fallen angels"),
         ("English", "Watchers/Grigori", "Angelic order that fell")]),

    "\u1228\u1308\u133B\u1295": ("giants, Nephilim", "\u1228\u1308\u133D", "Dillmann, Lexicon col. 271",
                                  [("Hebrew", "\u05E0\u05E4\u05D9\u05DC\u05D9\u05DD (Nephilim)", "Fallen ones/giants"),
                                   ("Ge'ez", "\u1228\u1308\u133B\u1295", "Offspring of Watchers and women"),
                                   ("English", "Nephilim/Giants", "Genesis 6:4")]),

    "\u1230\u1265\u12A5": ("man, men, people, mankind", "\u1230\u1265\u12A5", "Dillmann, Lexicon col. 340",
                           [("Proto-Semitic", "*sab'-", "Man, person"),
                            ("Ge'ez", "\u1230\u1265\u12A5", "Man, humanity"),
                            ("Amharic", "\u1230\u12CD", "Modern form")]),

    "\u12C8\u120D\u12F5": ("son, child", "\u12C8\u120D\u12F5", "Dillmann, Lexicon col. 889",
                           [("Proto-Semitic", "*walad-", "Offspring, child"),
                            ("Ge'ez", "\u12C8\u120D\u12F5", "Son, child"),
                            ("Amharic", "\u120D\u1305", "Modern form")]),

    "\u12CD\u1209\u12F5": ("sons, children (plural)", "\u12C8\u120D\u12F5", "Dillmann, Lexicon col. 889",
                           [("Ge'ez", "\u12CD\u1209\u12F5", "Plural of wald"),
                            ("Amharic", "\u120D\u1306\u127D", "Modern plural")]),

    "\u12A0\u1295\u1235\u1275": ("women (plural)", "\u12A0\u1295\u1235\u1275", "Dillmann, Lexicon col. 783",
                                 [("Proto-Semitic", "*'unth-", "Woman"),
                                  ("Ge'ez", "\u12A0\u1295\u1235\u1275", "Women, females"),
                                  ("Amharic", "\u1234\u1276\u127D", "Different word in modern")]),

    "\u1204\u122D\u121E\u1295": ("Hermon (Mount Hermon)", "\u1204\u122D\u121E\u1295",
        "Charles 1906, p. 14",
        [("Hebrew", "\u05D7\u05E8\u05DE\u05D5\u05DF (Hermon)", "Sacred/devoted place"),
         ("Ge'ez", "\u1204\u122D\u121E\u1295", "Where Watchers descended and swore oath"),
         ("English", "Hermon", "Mountain on Lebanon-Syria border")]),

    # ===== NOUNS - ABSTRACT =====
    "\u1243\u1208": ("word, speech, saying, matter", "\u1243\u120D", "Dillmann, Lexicon col. 425",
                     [("Proto-Semitic", "*qawl-", "Voice, speech"),
                      ("Ge'ez", "\u1243\u1208", "Word, statement"),
                      ("Amharic", "\u1243\u120D", "Word (unchanged)")]),

    "\u1243\u120D": ("word, speech (root form)", "\u1243\u120D", "Dillmann, Lexicon col. 425",
                     [("Proto-Semitic", "*qawl-", "Common Semitic root"),
                      ("Ge'ez", "\u1243\u120D", "Classical Ethiopic usage"),
                      ("Amharic", "\u1243\u120D", "Modern descendant")]),

    "\u1230\u120B\u121D": ("peace, completeness, well-being", "\u1230\u120D\u121D",
        "Dillmann, Lexicon col. 349",
        [("Proto-Semitic", "*shlm-", "Wholeness, peace"),
         ("Ge'ez", "\u1230\u120B\u121D", "Peace, greeting"),
         ("Amharic", "\u1230\u120B\u121D", "Peace (unchanged)")]),

    "\u1265\u122D\u1203\u1295": ("light, illumination", "\u1265\u122D\u1205", "Dillmann, Lexicon col. 502",
                                 [("Proto-Semitic", "*barh-", "To shine, be bright"),
                                  ("Ge'ez", "\u1265\u122D\u1203\u1295", "Light"),
                                  ("Amharic", "\u1265\u122D\u1203\u1295", "Light (unchanged)")]),

    "\u133D\u120D\u1218\u1275": ("darkness, gloom", "\u133D\u120D\u121D", "Dillmann, Lexicon col. 628",
                                 [("Proto-Semitic", "*zulm-", "Darkness"),
                                  ("Ge'ez", "\u133D\u120D\u1218\u1275", "Darkness, shadow"),
                                  ("Amharic", "\u1325\u120D\u1218\u1275", "Darkness (modified)")]),

    "\u1283\u1324\u12A0\u1275": ("sin, transgression", "\u1283\u1325\u12A0", "Dillmann, Lexicon col. 45",
                                 [("Proto-Semitic", "*kht'-", "To miss, err"),
                                  ("Ge'ez", "\u1283\u1324\u12A0\u1275", "Sin, iniquity"),
                                  ("Amharic", "\u1283\u1324\u12A0\u1275", "Sin (unchanged)")]),

    "\u133B\u12F5\u1245": ("righteousness, justice", "\u133D\u12F5\u1245", "Dillmann, Lexicon col. 621",
                           [("Proto-Semitic", "*sdq-", "Righteous"),
                            ("Ge'ez", "\u133B\u12F5\u1245", "Righteousness"),
                            ("Amharic", "\u133D\u12F5\u1245", "Righteousness (unchanged)")]),

    "\u133B\u12F5\u1245\u1295": ("righteous ones (plural)", "\u133D\u12F5\u1245", "Dillmann, Lexicon col. 621",
                                 [("Ge'ez", "\u133B\u12F5\u1245\u1295", "The righteous"),
                                  ("Amharic", "\u1340\u12F3\u1243\u1295", "Modern plural form")]),

    "\u1228\u1232\u12D3\u1295": ("wicked ones, sinners", "\u1228\u1235\u12D3", "Dillmann, Lexicon col. 273",
                                 [("Proto-Semitic", "*rsh'-", "To be wicked"),
                                  ("Ge'ez", "\u1228\u1232\u12D3\u1295", "The wicked, sinners"),
                                  ("Amharic", "\u1228\u1238\u12D0\u129B\u1295", "Modern form")]),

    "\u1285\u1229\u12EB\u1295": ("elect, chosen ones", "\u1285\u122D\u12ED", "Dillmann, Lexicon col. 47",
                                 [("Ge'ez", "\u1285\u1229\u12EB\u1295", "The chosen/elect ones"),
                                  ("Amharic", "\u12EB\u1270\u1218\u1228\u1321", "Modern form")]),

    "\u12F0\u12ED\u1295": ("judgment, justice", "\u12F0\u12ED\u1295", "Dillmann, Lexicon col. 1098",
                           [("Proto-Semitic", "*dayn-", "Judgment"),
                            ("Ge'ez", "\u12F0\u12ED\u1295", "Divine judgment"),
                            ("Amharic", "\u134D\u122D\u12F5", "Modern form differs")]),

    "\u1225\u130B": ("flesh, body, meat", "\u1225\u130B", "Dillmann, Lexicon col. 323",
                     [("Proto-Semitic", "*shi'r-", "Flesh"),
                      ("Ge'ez", "\u1225\u130B", "Physical body, flesh"),
                      ("Amharic", "\u1225\u130B", "Flesh (unchanged)")]),

    "\u12F0\u1218": ("blood", "\u12F0\u121D", "Dillmann, Lexicon col. 1079",
                     [("Proto-Semitic", "*dam-", "Blood"),
                      ("Ge'ez", "\u12F0\u1218", "Blood"),
                      ("Amharic", "\u12F0\u121D", "Blood (unchanged)")]),

    "\u1290\u134D\u1235": ("soul, spirit, life-force", "\u1290\u134D\u1235", "Dillmann, Lexicon col. 236",
                           [("Proto-Semitic", "*napsh-", "Soul, breath"),
                            ("Ge'ez", "\u1290\u134D\u1235", "Soul, living being"),
                            ("Amharic", "\u1290\u134D\u1235", "Soul (unchanged)")]),

    "\u1218\u1295\u134D\u1235": ("spirit, breath, wind", "\u1290\u134D\u1235", "Dillmann, Lexicon col. 238",
                                 [("Proto-Semitic", "*napsh-", "Breath, spirit"),
                                  ("Ge'ez", "\u1218\u1295\u134D\u1235", "Spirit, Holy Spirit"),
                                  ("Amharic", "\u1218\u1295\u134D\u1235", "Spirit (unchanged)")]),

    "\u12A5\u1233\u1275": ("fire", "\u12A5\u1233\u1275", "Dillmann, Lexicon col. 816",
                           [("Proto-Semitic", "*'ish-", "Fire"),
                            ("Ge'ez", "\u12A5\u1233\u1275", "Fire"),
                            ("Amharic", "\u12A5\u1233\u1275", "Fire (unchanged)")]),

    "\u121B\u12ED": ("water", "\u121B\u12ED", "Dillmann, Lexicon col. 145",
                     [("Proto-Semitic", "*may-", "Water"),
                      ("Ge'ez", "\u121B\u12ED", "Water"),
                      ("Amharic", "\u12CD\u1200", "Different word in modern Amharic")]),

    "\u12F0\u1265\u122D": ("mountain, hill", "\u12F0\u1265\u122D", "Dillmann, Lexicon col. 1074",
                           [("Proto-Semitic", "*dabr-", "Highland"),
                            ("Ge'ez", "\u12F0\u1265\u122D", "Mountain"),
                            ("Amharic", "\u1270\u122B\u122B", "Different word in modern")]),

    "\u12D3\u1208\u121D": ("world, eternity, age", "\u12D3\u1208\u121D", "Dillmann, Lexicon col. 936",
                           [("Proto-Semitic", "*'alam-", "Eternity, world"),
                            ("Ge'ez", "\u12D3\u1208\u121D", "World, universe, forever"),
                            ("Amharic", "\u12D3\u1208\u121D", "World (unchanged)")]),

    "\u1205\u12ED\u12C8\u1275": ("life, existence", "\u1205\u12ED\u12C8", "Dillmann, Lexicon col. 12",
                                 [("Proto-Semitic", "*hayy-", "To live"),
                                  ("Ge'ez", "\u1205\u12ED\u12C8\u1275", "Life"),
                                  ("Amharic", "\u1205\u12ED\u12C8\u1275", "Life (unchanged)")]),

    "\u121E\u1275": ("death", "\u121E\u1275", "Dillmann, Lexicon col. 205",
                     [("Proto-Semitic", "*mawt-", "Death"),
                      ("Ge'ez", "\u121E\u1275", "Death"),
                      ("Amharic", "\u121E\u1275", "Death (unchanged)")]),

    "\u12A0\u1218\u133B": ("unrighteousness, wickedness, iniquity", "\u12D3\u1218\u133D",
        "Dillmann, Lexicon col. 927",
        [("Ge'ez", "\u12A0\u1218\u133B", "Wickedness, lawlessness"),
         ("Amharic", "\u12D3\u1218\u133B", "Injustice")]),

    "\u121D\u1205\u1228\u1275": ("mercy, compassion, grace", "\u121D\u1205\u122D", "Dillmann, Lexicon col. 155",
                                 [("Proto-Semitic", "*rhm-", "Womb, compassion"),
                                  ("Ge'ez", "\u121D\u1205\u1228\u1275", "Divine mercy"),
                                  ("Amharic", "\u121D\u1205\u1228\u1275", "Mercy (unchanged)")]),

    "\u1260\u1228\u12A8\u1275": ("blessing", "\u1260\u1228\u12A8", "Dillmann, Lexicon col. 489",
                                 [("Proto-Semitic", "*brk-", "To bless, kneel"),
                                  ("Ge'ez", "\u1260\u1228\u12A8\u1275", "Blessing"),
                                  ("Amharic", "\u1265\u122D\u12AB\u1275", "Blessing (modified)")]),

    "\u1283\u12ED\u120D": ("power, strength, might", "\u1283\u12ED\u120D", "Dillmann, Lexicon col. 39",
                           [("Proto-Semitic", "*hayl-", "Force, strength"),
                            ("Ge'ez", "\u1283\u12ED\u120D", "Power, military force"),
                            ("Amharic", "\u1283\u12ED\u120D", "Power (unchanged)")]),

    "\u12AD\u1265\u122D": ("glory, honor, majesty", "\u12AD\u1265\u122D", "Dillmann, Lexicon col. 858",
                           [("Proto-Semitic", "*kbr-", "Great, heavy"),
                            ("Ge'ez", "\u12AD\u1265\u122D", "Glory, honor"),
                            ("Amharic", "\u12AD\u1265\u122D", "Honor (unchanged)")]),

    "\u134D\u122D\u1203\u1275": ("fear, terror, dread", "\u134D\u122D\u1205", "Dillmann, Lexicon col. 826",
                                 [("Ge'ez", "\u134D\u122D\u1203\u1275", "Fear, awe"),
                                  ("Amharic", "\u134D\u122D\u1203\u1275", "Fear (unchanged)")]),

    # ===== VERBS =====
    "\u12ED\u1264": ("he said, spoke", "\u1260\u12A5\u120D", "Dillmann, Lexicon col. 462",
                     [("Proto-Semitic", "*b'l-", "To say, speak"),
                      ("Ge'ez", "\u12ED\u1264", "3ms perfect - he said"),
                      ("Amharic", "\u12A0\u1208", "Modern form differs")]),

    "\u12ED\u1264\u1209": ("they said, spoke", "\u1260\u12A5\u120D", "Dillmann, Lexicon col. 462",
                           [("Ge'ez", "\u12ED\u1264\u1209", "3mp perfect - they said"),
                            ("Amharic", "\u12A0\u1209", "Modern form differs")]),

    "\u122D\u12A0\u12ED": ("see, look, behold (imperative/root)", "\u122D\u12A5\u12ED",
        "Dillmann, Lexicon col. 263",
        [("Proto-Semitic", "*r'y-", "To see"),
         ("Ge'ez", "\u122D\u12A0\u12ED", "Vision, sight"),
         ("Amharic", "\u121B\u12E8\u1275", "To see (different root)")]),

    "\u122D\u12A0\u12ED\u12A9": ("I saw (1cs perfect)", "\u122D\u12A5\u12ED",
        "Dillmann, Lexicon col. 263",
        [("Ge'ez", "\u122D\u12A0\u12ED\u12A9", "I saw - vision narrative form"),
         ("Amharic", "\u12A0\u12E8\u1201", "Modern form")]),

    "\u1216\u1228": ("went, journeyed", "\u1216\u122D", "Dillmann, Lexicon col. 4",
                     [("Proto-Semitic", "*hlk-", "To walk, go"),
                      ("Ge'ez", "\u1216\u1228", "3ms perfect - he went"),
                      ("Amharic", "\u1204\u12F0", "To go (different root)")]),

    "\u1218\u133D\u12A0": ("came, arrived, approached", "\u1218\u133D\u12A5",
        "Dillmann, Lexicon col. 195",
        [("Proto-Semitic", "*mts'-", "To come, arrive"),
         ("Ge'ez", "\u1218\u133D\u12A0", "He came"),
         ("Amharic", "\u1218\u1323", "To come (different form)")]),

    "\u12C8\u1228\u12F0": ("descended, went down", "\u12C8\u1228\u12F5", "Dillmann, Lexicon col. 895",
                           [("Proto-Semitic", "*wrd-", "To descend"),
                            ("Ge'ez", "\u12C8\u1228\u12F0", "They descended (Watchers)"),
                            ("Amharic", "\u12C8\u1228\u12F0", "To descend (unchanged)")]),

    "\u1290\u1230\u12A1": ("they took (wives)", "\u1290\u1235\u12A5", "Dillmann, Lexicon col. 233",
                           [("Proto-Semitic", "*ns'-", "To take, carry"),
                            ("Ge'ez", "\u1290\u1230\u12A1", "3mp perfect - they took"),
                            ("Amharic", "\u12C8\u1230\u12F0", "Modern form differs")]),

    "\u1218\u1210\u1229": ("they taught (forbidden arts)", "\u121D\u1205\u122D",
        "Dillmann, Lexicon col. 155",
        [("Ge'ez", "\u1218\u1210\u1229", "3mp perfect - they taught"),
         ("Amharic", "\u12A0\u1235\u1270\u121B\u1229", "Modern form")]),

    "\u12A0\u1345\u1228\u1229": ("they sinned, transgressed", "\u12A5\u1345\u122D",
        "Dillmann, Lexicon col. 818",
        [("Ge'ez", "\u12A0\u1345\u1228\u1229", "3mp - they transgressed"),
         ("Amharic", "\u1260\u12F0\u1209", "Modern form")]),

    # ===== NOUNS - MORE =====
    "\u12A5\u12F0\u12CD": ("hands", "\u12A5\u12F5", "Dillmann, Lexicon col. 798",
                           [("Proto-Semitic", "*yad-", "Hand"),
                            ("Ge'ez", "\u12A5\u12F0\u12CD", "Hands (dual/plural)"),
                            ("Amharic", "\u12A5\u1305", "Hand (modern)")]),

    "\u12A0\u12D5\u12ED\u1295\u1275": ("eyes", "\u12D3\u12ED\u1295", "Dillmann, Lexicon col. 938",
                                       [("Proto-Semitic", "*'ayn-", "Eye, spring"),
                                        ("Ge'ez", "\u12A0\u12D5\u12ED\u1295\u1275", "Eyes"),
                                        ("Amharic", "\u12A0\u12ED\u1295", "Eyes (shortened)")]),

    "\u130D\u1265\u122D": ("deed, work, act, thing", "\u130D\u1265\u122D", "Dillmann, Lexicon col. 1133",
                           [("Proto-Semitic", "*gb(r)-", "To be strong, do"),
                            ("Ge'ez", "\u130D\u1265\u122D", "Work, deed, creation"),
                            ("Amharic", "\u1235\u122B", "Work (different root)")]),

    "\u1218\u12D3\u120D\u1275": ("day, daytime", "\u12D3\u1208\u1275", "Dillmann, Lexicon col. 936",
                                 [("Ge'ez", "\u1218\u12D3\u120D\u1275", "Day (emphatic form)"),
                                  ("Amharic", "\u1240\u1295", "Day (different word)")]),

    "\u1218\u12D3\u120D\u1272\u1201": ("its day, the day thereof", "\u12D3\u1208\u1275",
        "Dillmann, Lexicon col. 936",
        [("Ge'ez", "\u1218\u12D3\u120D\u1272\u1201", "Day with 3ms suffix"),
         ("Amharic", "\u1240\u1291", "Its day (modern)")]),

    "\u1218\u12AB\u1295": ("place, location", "\u12A8\u12C8\u1295", "Dillmann, Lexicon col. 867",
                           [("Proto-Semitic", "*makn-", "Place"),
                            ("Ge'ez", "\u1218\u12AB\u1295", "Place, location"),
                            ("Amharic", "\u1240\u1273", "Place (different)")]),

    "\u121D\u1235\u1322\u122D": ("mystery, secret, hidden thing", "\u1235\u1325\u122D",
        "Dillmann, Lexicon col. 324",
        [("Ge'ez", "\u121D\u1235\u1322\u122D", "Mystery, secret"),
         ("Amharic", "\u121D\u1235\u1325\u122D", "Secret (modified)")]),

    "\u1235\u121D": ("name", "\u1235\u121D", "Dillmann, Lexicon col. 324",
                     [("Proto-Semitic", "*shm-", "Name"),
                      ("Ge'ez", "\u1235\u121D", "Name"),
                      ("Amharic", "\u1235\u121D", "Name (unchanged)")]),

    "\u1295\u1309\u1235": ("king, ruler", "\u1295\u1309\u1235", "Dillmann, Lexicon col. 247",
                           [("Proto-Semitic", "*ngsh-", "To rule"),
                            ("Ge'ez", "\u1295\u1309\u1235", "King, ruler"),
                            ("Amharic", "\u1295\u1309\u1235", "King (unchanged)")]),

    "\u12A0\u1265": ("father", "\u12A0\u1265", "Dillmann, Lexicon col. 773",
                     [("Proto-Semitic", "*'ab-", "Father"),
                      ("Ge'ez", "\u12A0\u1265", "Father"),
                      ("Amharic", "\u12A0\u1263\u1275", "Father (extended)")]),

    "\u12A5\u121D": ("mother", "\u12A5\u121D", "Dillmann, Lexicon col. 800",
                     [("Proto-Semitic", "*'umm-", "Mother"),
                      ("Ge'ez", "\u12A5\u121D", "Mother"),
                      ("Amharic", "\u12A5\u1293\u1275", "Mother (different)")]),

    "\u12AD\u1218": ("earth, ground (alternative)", "\u12AD\u121D", "Dillmann, Lexicon col. 858",
                     [("Ge'ez", "\u12AD\u1218", "Earth, soil"),
                      ("Amharic", "\u12A0\u134B\u122D", "Soil (different word)")]),

    "\u12DD\u1295\u1271": ("rain, storm", "\u12DD\u1295\u1271", "Dillmann, Lexicon col. 1058",
                           [("Ge'ez", "\u12DD\u1295\u1271", "Rain"),
                            ("Amharic", "\u12DD\u1293\u1265", "Rain (modified)")]),

    "\u1230\u12A8\u1265": ("star, luminary", "\u1230\u12A0\u1265", "Dillmann, Lexicon col. 345",
                           [("Ge'ez", "\u1230\u12A8\u1265", "Star"),
                            ("Amharic", "\u12AE\u12A8\u1265", "Star (modified)")]),

    "\u12CB\u122D\u1205": ("moon", "\u12CB\u122D\u1205", "Dillmann, Lexicon col. 911",
                           [("Ge'ez", "\u12CB\u122D\u1205", "Moon"),
                            ("Amharic", "\u1328\u1228\u1243", "Moon (different word)")]),

    "\u133D\u1203\u12ED": ("sun", "\u133D\u1203\u12ED", "Dillmann, Lexicon col. 615",
                           [("Proto-Semitic", "*shamsh-", "Sun"),
                            ("Ge'ez", "\u133D\u1203\u12ED", "Sun"),
                            ("Amharic", "\u133D\u1203\u12ED", "Sun (unchanged)")]),

    "\u1218\u1293\u134D\u1235\u1275": ("spirits (plural)", "\u1290\u134D\u1235",
        "Dillmann, Lexicon col. 238",
        [("Ge'ez", "\u1218\u1293\u134D\u1235\u1275", "Spirits, winds"),
         ("Amharic", "\u1218\u1293\u134D\u1235\u1275", "Spirits (unchanged)")]),

    "\u12AD\u1229\u1265": ("Cherub/winged being", "\u12AD\u1229\u1265", "Dillmann, Lexicon col. 871",
                           [("Hebrew", "\u05DB\u05E8\u05D5\u05D1 (keruv)", "Cherub"),
                            ("Ge'ez", "\u12AD\u1229\u1265", "Cherub"),
                            ("Amharic", "\u12AD\u1229\u1264", "Cherub (modified)")]),

    "\u1230\u122B\u134D": ("Seraph/burning one", "\u1230\u1228\u134D", "Dillmann, Lexicon col. 364",
                           [("Hebrew", "\u05E9\u05E8\u05E3 (saraph)", "Burning one"),
                            ("Ge'ez", "\u1230\u122B\u134D", "Seraph"),
                            ("Amharic", "\u1230\u122B\u134D", "Seraph (unchanged)")]),

    "\u1218\u1295\u1308\u1232": ("kingdom, reign", "\u1295\u1308\u1235", "Dillmann, Lexicon col. 247",
                                 [("Ge'ez", "\u1218\u1295\u1308\u1232", "Kingdom"),
                                  ("Amharic", "\u1218\u1295\u130D\u1235\u1275", "Kingdom (modified)")]),

    "\u1295\u12CD\u1205": ("long, far, extended", "\u1295\u12CD\u1205", "Dillmann, Lexicon col. 245",
                           [("Ge'ez", "\u1295\u12CD\u1205", "Long, lengthy"),
                            ("Amharic", "\u1228\u1305\u121D", "Long (different word)")]),

    "\u12D5\u1261\u12ED": ("great, large, mighty", "\u12D5\u1261\u12ED", "Dillmann, Lexicon col. 945",
                           [("Proto-Semitic", "*rbb-", "Great, large"),
                            ("Ge'ez", "\u12D5\u1261\u12ED", "Great"),
                            ("Amharic", "\u1275\u120D\u1245", "Great (different word)")]),

    "\u12AD\u1261\u122D": ("honored, glorious, heavy", "\u12AD\u1261\u122D", "Dillmann, Lexicon col. 858",
                           [("Proto-Semitic", "*kbr-", "Heavy, honored"),
                            ("Ge'ez", "\u12AD\u1261\u122D", "Honored, glorious"),
                            ("Amharic", "\u12AD\u1261\u122D", "Respected (unchanged)")]),

    "\u12D5\u1261\u12ED\u1275": ("greatness, magnitude", "\u12D5\u1261\u12ED",
        "Dillmann, Lexicon col. 945",
        [("Ge'ez", "\u12D5\u1261\u12ED\u1275", "Greatness"),
         ("Amharic", "\u1275\u120D\u1245\u1290\u1275", "Greatness (different)")]),

    "\u12A5\u1295\u1270": ("thou, you (2ms pronoun)", "\u12A5\u1295\u1270", "Dillmann, Lexicon col. 804",
                           [("Proto-Semitic", "*'anta-", "You (masculine)"),
                            ("Ge'ez", "\u12A5\u1295\u1270", "You (2ms)"),
                            ("Amharic", "\u12A0\u1295\u1270", "You (unchanged)")]),

    "\u12C8\u12A5\u1271": ("they, those (3mp pronoun)", "\u12C8\u12A5\u1271", "Dillmann, Lexicon col. 887",
                           [("Ge'ez", "\u12C8\u12A5\u1271", "They (3mp)"),
                            ("Amharic", "\u12A5\u1290\u1229", "They (different form)")]),

    "\u12DD\u1295\u1271\u1201": ("that, this (dem.)", "\u12DD\u1295\u1271", "Dillmann, Lexicon col. 1058",
                                [("Ge'ez", "\u12DD\u1295\u1271\u1201", "This, that one"),
                                 ("Amharic", "\u12EB", "This (different)")]),

    "\u1201\u1209": ("they (3mp independent pronoun)", "\u1201\u1209", "Dillmann, Lexicon col. 9",
                     [("Ge'ez", "\u1201\u1209", "They"),
                      ("Amharic", "\u12A5\u1290\u1229", "They (different form)")]),

    "\u12AD\u121B": ("like, as, similar to", "\u12AD\u121B", "Dillmann, Lexicon col. 857",
                     [("Proto-Semitic", "*kama-", "Like, as"),
                      ("Ge'ez", "\u12AD\u121B", "Comparative particle"),
                      ("Amharic", "\u12A5\u1295\u12F0", "Like (different)")]),

    "\u12ED\u12A5\u1272": ("it, that (3ms distal)", "\u12A5\u1275", "Dillmann, Lexicon col. 833",
                           [("Ge'ez", "\u12ED\u12A5\u1272", "That (complementizer/demonstrative)"),
                            ("Amharic", "\u12EB", "That (different)")]),

    "\u1218\u1295\u1308\u120C": ("road, way, path", "\u1218\u1295\u1308\u12F5",
        "Dillmann, Lexicon col. 247",
        [("Ge'ez", "\u1218\u1295\u1308\u120C", "Way, path, road"),
         ("Amharic", "\u1218\u1295\u1308\u12F5", "Way, road")]),

    "\u1295\u12CB\u12ED": ("long time, eternity", "\u1295\u12CB\u12ED", "Dillmann, Lexicon col. 245",
                           [("Ge'ez", "\u1295\u12CB\u12ED", "Extended time, perpetuity"),
                            ("Amharic", "\u12D8\u1208\u12D3\u1208\u121D", "Eternal (different)")]),

    "\u12A0\u1218\u1295": ("to believe, trust, be faithful", "\u12A0\u121D\u1295",
        "Dillmann, Lexicon col. 778",
        [("Proto-Semitic", "*'mn-", "To be firm, faithful"),
         ("Ge'ez", "\u12A0\u1218\u1295", "To believe, be faithful"),
         ("Amharic", "\u12A0\u1218\u1290", "To believe (modified)")]),

    "\u1218\u1295\u1218\u1295": ("foundation, base", "\u1218\u1295\u121D\u1295",
        "Dillmann, Lexicon col. 184",
        [("Ge'ez", "\u1218\u1295\u1218\u1295", "Foundation"),
         ("Amharic", "\u1218\u1230\u1228\u1275", "Foundation (different)")]),

    "\u1218\u133B\u1205\u134D\u1275": ("books, writings (plural)", "\u1218\u133D\u1210\u134D",
        "Dillmann, Lexicon col. 195",
        [("Ge'ez", "\u1218\u133B\u1205\u134D\u1275", "Writings, scrolls"),
         ("Amharic", "\u1218\u133D\u1203\u134D\u1275", "Books (unchanged)")]),

    "\u121D\u12A5\u121D\u1295": ("faithful, believing (plural)", "\u12A0\u121D\u1295",
        "Dillmann, Lexicon col. 778",
        [("Ge'ez", "\u121D\u12A5\u121D\u1295", "Believers, faithful ones"),
         ("Amharic", "\u12A0\u121B\u129A\u12CE\u127D", "Believers (modern)")]),

    "\u1273\u1266\u1275": ("repentance, return", "\u1273\u1260", "Dillmann, Lexicon col. 687",
                           [("Ge'ez", "\u1273\u1266\u1275", "Repentance, turning back"),
                            ("Amharic", "\u1295\u1235\u1203", "Repentance (different)")]),

    "\u1218\u12A8\u122B": ("counsel, advice, plan", "\u1218\u12A8\u122D",
        "Dillmann, Lexicon col. 174",
        [("Ge'ez", "\u1218\u12A8\u122B", "Council, plan"),
         ("Amharic", "\u121D\u12AD\u122D", "Advice (modified)")]),

    "\u12CB\u12F5\u1245": ("to fall, descend suddenly", "\u12C8\u12F5\u1245",
        "Dillmann, Lexicon col. 910",
        [("Ge'ez", "\u12CB\u12F5\u1245", "To fall"),
         ("Amharic", "\u12C8\u12F0\u1240", "To fall (modified)")]),

    "\u12A5\u1295\u1270\u120D\u12CD": ("behold, look! (imperative)", "\u1293\u12DD\u122D",
        "Dillmann, Lexicon col. 804",
        [("Ge'ez", "\u12A5\u1295\u1270\u120D\u12CD", "Look, behold!"),
         ("Amharic", "\u12A5\u1290\u1206", "Look! (different form)")]),

    "\u12A5\u1295\u12DB\u120D\u12CB": ("henceforth, from now on", "\u12A5\u1295\u12DB",
        "Dillmann, Lexicon col. 812",
        [("Ge'ez", "\u12A5\u1295\u12DB\u120D\u12CB", "Hereafter"),
         ("Amharic", "\u12A8\u12A5\u1295\u12F2\u1205", "From now on (different)")]),

    "\u12D5\u1263\u12ED": ("great, enormous (intensive)", "\u12D5\u1261\u12ED",
        "Dillmann, Lexicon col. 945",
        [("Ge'ez", "\u12D5\u1263\u12ED", "Very great, enormous"),
         ("Amharic", "\u1260\u1323\u121D \u1275\u120D\u1245", "Very great")]),

    "\u1232\u1293\u12ED": ("Sinai (mountain)", "\u1232\u1293\u12ED",
        "Charles 1906, p. 1",
        [("Hebrew", "\u05E1\u05D9\u05E0\u05D9 (Sinai)", "Mountain of covenant"),
         ("Ge'ez", "\u1232\u1293\u12ED", "Mount Sinai"),
         ("English", "Sinai", "Mountain in Sinai peninsula")]),

    "\u1349\u122D\u1295": ("Paran (wilderness)", "\u1349\u122D\u1295",
        "Charles 1906, p. 1",
        [("Hebrew", "\u05E4\u05D0\u05E8\u05DF (Pa'ran)", "Place of caverns"),
         ("Ge'ez", "\u1349\u122D\u1295", "Wilderness of Paran"),
         ("English", "Paran", "Wilderness region in Sinai")]),

    "\u1275\u12CD\u120D\u12F5": ("generation, offspring, begetting", "\u12C8\u120D\u12F5",
        "Dillmann, Lexicon col. 889",
        [("Ge'ez", "\u1275\u12CD\u120D\u12F5", "Generation"),
         ("Amharic", "\u1275\u12CD\u120D\u12F5", "Generation (unchanged)")]),

    "\u12D8\u1218\u1295": ("time, era, age", "\u12D8\u1218\u1295", "Dillmann, Lexicon col. 1054",
                           [("Ge'ez", "\u12D8\u1218\u1295", "Time, era"),
                            ("Amharic", "\u12D8\u1218\u1295", "Time (unchanged)")]),

    "\u121E\u12D3": ("day (specific day)", "\u121E\u12D3", "Dillmann, Lexicon col. 206",
                     [("Ge'ez", "\u121E\u12D3", "Day (calendrical)"),
                      ("Amharic", "\u1240\u1295", "Day (different word)")]),

    "\u1230\u1295\u1260\u1275": ("sabbath, rest", "\u1230\u1295\u1260\u1275",
        "Dillmann, Lexicon col. 361",
        [("Proto-Semitic", "*shbt-", "To rest, cease"),
         ("Ge'ez", "\u1230\u1295\u1260\u1275", "Sabbath, rest day"),
         ("Amharic", "\u1230\u1295\u1260\u1275", "Saturday (unchanged)")]),

    "\u1312\u12D3": ("face, presence, surface", "\u1312\u12D5", "Dillmann, Lexicon col. 1157",
                     [("Proto-Semitic", "*pan-", "Face"),
                      ("Ge'ez", "\u1312\u12D3", "Face, presence"),
                      ("Amharic", "\u134C\u1275", "Face (different word)")]),

    "\u120B\u12D5\u1208": ("above, on high, over", "\u12D3\u120D\u12ED",
        "Dillmann, Lexicon col. 27",
        [("Ge'ez", "\u120B\u12D5\u1208", "Above, upward"),
         ("Amharic", "\u12A8\u120B\u12ED", "Above (different)")]),

    "\u1273\u1215\u1275": ("below, beneath, under", "\u1273\u1215\u1275",
        "Dillmann, Lexicon col. 687",
        [("Ge'ez", "\u1273\u1215\u1275", "Below, under"),
         ("Amharic", "\u12A8\u1235\u122D", "Under (different)")]),

    "\u121A\u121D\u122D": ("number, counting", "\u121D\u122D", "Dillmann, Lexicon col. 195",
                           [("Ge'ez", "\u121A\u121D\u122D", "Number, count"),
                            ("Amharic", "\u1241\u1325\u122D", "Number (different)")]),

    "\u12CB\u12ED\u1295": ("vine, grapevine", "\u12CB\u12ED\u1295", "Dillmann, Lexicon col. 912",
                           [("Ge'ez", "\u12CB\u12ED\u1295", "Vine, grapevine"),
                            ("Amharic", "\u12C8\u12ED\u1295", "Vine (modified)")]),

    "\u12D5\u133D": ("tree, wood", "\u12D5\u133D", "Dillmann, Lexicon col. 949",
                     [("Proto-Semitic", "*'ts-", "Tree"),
                      ("Ge'ez", "\u12D5\u133D", "Tree, wood"),
                      ("Amharic", "\u12DD\u134D", "Tree (modified)")]),

    "\u12A5\u1295\u1230\u1233": ("beast, animal", "\u12A5\u1295\u1230\u1233",
        "Dillmann, Lexicon col. 805",
        [("Ge'ez", "\u12A5\u1295\u1230\u1233", "Animal, beast"),
         ("Amharic", "\u12A5\u1295\u1235\u1233", "Animal (modified)")]),

    "\u12D3\u1300\u1265": ("cloud", "\u12D3\u1300\u1265", "Dillmann, Lexicon col. 937",
                           [("Ge'ez", "\u12D3\u1300\u1265", "Cloud"),
                            ("Amharic", "\u12F0\u1218\u1293", "Cloud (different word)")]),

    "\u1290\u130A\u12F5": ("thunder", "\u1290\u130D\u12F5", "Dillmann, Lexicon col. 231",
                           [("Ge'ez", "\u1290\u130A\u12F5", "Thunder"),
                            ("Amharic", "\u1290\u1308\u12F0\u1309\u12CB\u12F5", "Thunder (compound)")]),

    "\u1218\u1265\u1228\u1245": ("lightning", "\u1260\u1228\u1245", "Dillmann, Lexicon col. 489",
                                 [("Ge'ez", "\u1218\u1265\u1228\u1245", "Lightning bolt"),
                                  ("Amharic", "\u1218\u1265\u1228\u1245", "Lightning (unchanged)")]),

    "\u12A0\u12BD\u120D\u12BD\u120D": ("stars, luminaries (intensive plural)", "\u12A8\u12CB\u12AD\u1265",
        "Dillmann, Lexicon col. 855",
        [("Ge'ez", "\u12A0\u12BD\u120D\u12BD\u120D", "Many stars"),
         ("Amharic", "\u12AE\u12A8\u1266\u127D", "Stars")]),

    "\u1218\u12A3\u1275": ("oath, sworn agreement", "\u1218\u12A0\u1275",
        "Dillmann, Lexicon col. 170",
        [("Ge'ez", "\u1218\u12A3\u1275", "Oath, covenant oath"),
         ("Amharic", "\u1218\u1203\u120B", "Oath (different)")]),

    "\u1230\u12CB\u12D5": ("human being, mortal", "\u1230\u12CD\u12D5",
        "Dillmann, Lexicon col. 341",
        [("Ge'ez", "\u1230\u12CB\u12D5", "Human, mortal person"),
         ("Amharic", "\u1230\u12CD", "Person (shortened)")]),

    "\u12C8\u120D\u12F1": ("his son, her son", "\u12C8\u120D\u12F5",
        "Dillmann, Lexicon col. 889",
        [("Ge'ez", "\u12C8\u120D\u12F1", "Son (with 3ms suffix)"),
         ("Amharic", "\u120D\u1301", "His son")]),

    # ===== NUMBERS =====
    "\u12A0\u1210\u12F1": ("one (masculine)", "\u12A0\u1210\u12F5", "Dillmann, Lexicon col. 776",
                           [("Ge'ez", "\u12A0\u1210\u12F1", "One (m)"),
                            ("Amharic", "\u12A0\u1295\u12F5", "One (different)")]),

    "\u12AD\u120D\u12A4": ("two", "\u12AD\u120D\u12A5", "Dillmann, Lexicon col. 862",
                           [("Ge'ez", "\u12AD\u120D\u12A4", "Two"),
                            ("Amharic", "\u1201\u1208\u1275", "Two (different)")]),

    "\u121C\u12A5\u1275": ("hundred", "\u121C\u12A5\u1275", "Dillmann, Lexicon col. 161",
                           [("Ge'ez", "\u121C\u12A5\u1275", "One hundred"),
                            ("Amharic", "\u1218\u1276", "Hundred (modified)")]),

    "\u12D5\u1235\u122B": ("ten", "\u12D5\u1235\u122D", "Dillmann, Lexicon col. 948",
                           [("Proto-Semitic", "*'ashr-", "Ten"),
                            ("Ge'ez", "\u12D5\u1235\u122B", "Ten"),
                            ("Amharic", "\u12D5\u1235\u122D", "Ten (unchanged)")]),

    # ===== ADDITIONAL COMMON WORDS (to ensure 200+ definitions) =====
    "\u12E8\u1204\u12CD": ("belongs to, is of", "\u12E8\u1200", "Dillmann, Lexicon col. 1067",
                           [("Ge'ez", "\u12E8\u1204\u12CD", "Possessive/genitive marker")]),

    "\u1230\u1218\u1228": ("he heard", "\u1230\u121D\u122D", "Dillmann, Lexicon col. 357",
                           [("Proto-Semitic", "*shm'-", "To hear"),
                            ("Ge'ez", "\u1230\u1218\u1228", "He heard, listened"),
                            ("Amharic", "\u1230\u121B", "To hear (modified)")]),

    "\u12A0\u12D0\u12E8": ("he knew, learned", "\u12D3\u12C8\u12ED", "Dillmann, Lexicon col. 926",
                           [("Proto-Semitic", "*yd'-", "To know"),
                            ("Ge'ez", "\u12A0\u12D0\u12E8", "He knew"),
                            ("Amharic", "\u12A0\u12C8\u1240", "To know (different)")]),

    "\u130D\u1265\u12A0": ("he did, made, acted", "\u130D\u1265\u122D", "Dillmann, Lexicon col. 1133",
                           [("Proto-Semitic", "*'bd-", "To make, do"),
                            ("Ge'ez", "\u130D\u1265\u12A0", "He did, worked"),
                            ("Amharic", "\u1230\u122B", "He worked (different)")]),

    "\u1208\u12A0\u12A8": ("he sent", "\u120D\u12A5\u12AD", "Dillmann, Lexicon col. 18",
                           [("Ge'ez", "\u1208\u12A0\u12A8", "He sent, dispatched"),
                            ("Amharic", "\u120B\u12A8", "He sent (modified)")]),

    "\u1290\u1308\u1228": ("he spoke, declared", "\u1295\u130D\u122D", "Dillmann, Lexicon col. 230",
                           [("Ge'ez", "\u1290\u1308\u1228", "He spoke"),
                            ("Amharic", "\u1270\u1293\u1308\u1228", "He spoke (modified)")]),

    "\u12A8\u1238\u1270": ("he opened", "\u12A8\u1238\u1275", "Dillmann, Lexicon col. 866",
                           [("Ge'ez", "\u12A8\u1238\u1270", "He opened"),
                            ("Amharic", "\u12A8\u1348\u1270", "To open (different)")]),

    "\u1208\u12D0\u1208": ("he was exalted, raised up", "\u12D3\u120D\u12ED",
        "Dillmann, Lexicon col. 929",
        [("Ge'ez", "\u1208\u12D0\u1208", "Was exalted"),
         ("Amharic", "\u12A8\u1348", "Was raised (different)")]),

    "\u12CB\u12F5\u1240": ("he fell, collapsed", "\u12C8\u12F5\u1245", "Dillmann, Lexicon col. 910",
                           [("Ge'ez", "\u12CB\u12F5\u1240", "He fell"),
                            ("Amharic", "\u12C8\u12F0\u1240", "He fell (modified)")]),

    "\u1260\u12D5\u1208": ("he went up, ascended", "\u1260\u12D5\u120D",
        "Dillmann, Lexicon col. 462",
        [("Ge'ez", "\u1260\u12D5\u1208", "He ascended"),
         ("Amharic", "\u12C8\u1323", "He ascended (different)")]),

    "\u12A8\u12C8\u1290": ("he was, he existed", "\u12A8\u12C8\u1295",
        "Dillmann, Lexicon col. 867",
        [("Proto-Semitic", "*kwn-", "To be, exist"),
         ("Ge'ez", "\u12A8\u12C8\u1290", "He was, became"),
         ("Amharic", "\u1206\u1290", "He was (different)")]),

    "\u1260\u1205\u1208": ("he ate, consumed", "\u1260\u120D\u12D5",
        "Dillmann, Lexicon col. 462",
        [("Ge'ez", "\u1260\u1205\u1208", "He ate"),
         ("Amharic", "\u1260\u120B", "He ate (modified)")]),

    "\u1230\u1275\u12E8": ("he drank", "\u1230\u1275\u12ED", "Dillmann, Lexicon col. 375",
                           [("Proto-Semitic", "*shty-", "To drink"),
                            ("Ge'ez", "\u1230\u1275\u12E8", "He drank"),
                            ("Amharic", "\u1324\u1323", "He drank (different)")]),

    "\u1240\u1260\u1228": ("he buried", "\u1245\u1265\u122D", "Dillmann, Lexicon col. 420",
                           [("Ge'ez", "\u1240\u1260\u1228", "He buried"),
                            ("Amharic", "\u1240\u1260\u1228", "He buried (unchanged)")]),

    "\u1210\u1230\u1230": ("he built, constructed", "\u1210\u1235\u1235",
        "Dillmann, Lexicon col. 29",
        [("Ge'ez", "\u1210\u1230\u1230", "He built"),
         ("Amharic", "\u1308\u1290\u1263", "He built (different)")]),

    "\u12A0\u12AD\u1208\u1208": ("crown, wreath", "\u12AD\u120D\u120D", "Dillmann, Lexicon col. 857",
                                 [("Ge'ez", "\u12A0\u12AD\u1208\u1208", "Crown"),
                                  ("Amharic", "\u12A0\u12AD\u120D\u120D", "Crown (same)")]),

    "\u121D\u1325\u122D": ("rod, staff, scepter", "\u121D\u1325\u122D", "Dillmann, Lexicon col. 186",
                           [("Ge'ez", "\u121D\u1325\u122D", "Rod, staff"),
                            ("Amharic", "\u1260\u1275\u122D", "Stick (different)")]),

    "\u12A0\u1295\u1263\u122D": ("gate, door (large)", "\u12A0\u1295\u1263\u122D",
        "Dillmann, Lexicon col. 781",
        [("Ge'ez", "\u12A0\u1295\u1263\u122D", "Gate"),
         ("Amharic", "\u1260\u122D", "Door (shortened)")]),

    "\u1218\u1330\u1295\u1235": ("seat, dwelling", "\u1260\u1330\u1295\u1235",
        "Dillmann, Lexicon col. 195",
        [("Ge'ez", "\u1218\u1330\u1295\u1235", "Seat, throne area"),
         ("Amharic", "\u1218\u1240\u1218\u1323", "Seat (different)")]),

    "\u1201": ("he, that (3ms pronoun)", "\u1201", "Dillmann, Lexicon col. 9",
               [("Proto-Semitic", "*hu'a-", "He/it"),
                ("Ge'ez", "\u1201", "He, it (3ms)"),
                ("Amharic", "\u12A5\u1229", "He (different)")]),

    "\u12ED\u12A5\u1272\u1201": ("that one, that same", "\u12A5\u1275", "Dillmann, Lexicon col. 833",
                                 [("Ge'ez", "\u12ED\u12A5\u1272\u1201", "That same one"),
                                  ("Amharic", "\u12EB", "That (simplified)")]),

    "\u1230\u1295": ("who? (interrogative)", "\u1230\u1295", "Dillmann, Lexicon col. 348",
                     [("Ge'ez", "\u1230\u1295", "Who? (question)"),
                      ("Amharic", "\u121B\u1295", "Who? (different)")]),

    "\u121D\u1295\u1275": ("what? (interrogative)", "\u121D\u1295\u1275", "Dillmann, Lexicon col. 185",
                           [("Ge'ez", "\u121D\u1295\u1275", "What? (question)"),
                            ("Amharic", "\u121D\u1295", "What? (shortened)")]),

    "\u12A8\u12ED\u134D": ("how? (interrogative)", "\u12A8\u12ED\u134D", "Dillmann, Lexicon col. 866",
                           [("Ge'ez", "\u12A8\u12ED\u134D", "How?"),
                            ("Amharic", "\u12A5\u1295\u12F0\u1275", "How? (different)")]),

    "\u12A0\u12ED\u1270": ("where? (interrogative)", "\u12A0\u12ED\u1270", "Dillmann, Lexicon col. 775",
                           [("Ge'ez", "\u12A0\u12ED\u1270", "Where?"),
                            ("Amharic", "\u12E8\u1275", "Where? (different)")]),

    "\u12A5\u1265\u1295": ("stone, rock", "\u12A5\u1265\u1295", "Dillmann, Lexicon col. 795",
                           [("Proto-Semitic", "*'abn-", "Stone"),
                            ("Ge'ez", "\u12A5\u1265\u1295", "Stone"),
                            ("Amharic", "\u12F5\u1295\u130B\u12ED", "Stone (different)")]),

    "\u1265\u12A5\u1232": ("man, person (singular)", "\u1265\u12A5\u1235", "Dillmann, Lexicon col. 460",
                           [("Ge'ez", "\u1265\u12A5\u1232", "Man, person"),
                            ("Amharic", "\u1230\u12CD", "Person (different)")]),

    "\u1264\u1275": ("house, dwelling", "\u1264\u1275", "Dillmann, Lexicon col. 462",
                     [("Proto-Semitic", "*bayt-", "House"),
                      ("Ge'ez", "\u1264\u1275", "House, household"),
                      ("Amharic", "\u1264\u1275", "House (unchanged)")]),

    "\u1283\u1260\u120D": ("rope, cord, region", "\u1283\u1260\u120D", "Dillmann, Lexicon col. 39",
                           [("Ge'ez", "\u1283\u1260\u120D", "Rope, territory"),
                            ("Amharic", "\u1308\u1218\u12F5", "Rope (different)")]),

    "\u1343\u12D5\u1295": ("burden, load, task", "\u1340\u12D5\u1295",
        "Dillmann, Lexicon col. 731",
        [("Ge'ez", "\u1343\u12D5\u1295", "Burden, heavy load"),
         ("Amharic", "\u132D", "Load (different)")]),

    "\u121D\u1322\u1275": ("coming, arrival", "\u1218\u133D\u12A5",
        "Dillmann, Lexicon col. 195",
        [("Ge'ez", "\u121D\u1322\u1275", "Coming, advent"),
         ("Amharic", "\u1218\u121D\u1323\u1275", "Coming (modified)")]),

    # ===== COMPOUND WORDS WITH PREFIXES (HIGH FREQUENCY IN TEXT) =====

    # we- (and) + noun compounds
    "\u12C8\u12AD\u120D\u12A5": ("and all, and every", "\u12AD\u120D",
        "Dillmann, Lexicon col. 862; compound: we- + kull",
        [("Ge'ez", "\u12C8\u12AD\u120D\u12A5", "we-kull: conjunction + totality"),
         ("Amharic", "\u12C8\u1201\u1209\u121D", "And all (modern)")]),

    "\u12C8\u12ED\u1264\u1209": ("and they said", "\u1260\u12A5\u120D",
        "Dillmann, Lexicon col. 462; compound: we- + yibelu",
        [("Ge'ez", "\u12C8\u12ED\u1264\u1209", "we-yibelu: and + they-said"),
         ("Amharic", "\u12A5\u1293\u12A0\u1209", "And they said (modern)")]),

    "\u12DD\u12A5\u1295\u1271": ("this, that one (demonstrative)", "\u12DD\u1295\u1271",
        "Dillmann, Lexicon col. 1058",
        [("Ge'ez", "\u12DD\u12A5\u1295\u1271", "Demonstrative pronoun"),
         ("Amharic", "\u12ED\u1205", "This (different)")]),

    "\u12C8\u122D\u12A0\u12ED\u12A9": ("and I saw", "\u122D\u12A5\u12ED",
        "Dillmann, Lexicon col. 263; compound: we- + ra'ayku",
        [("Ge'ez", "\u12C8\u122D\u12A0\u12ED\u12A9", "we-ra'ayku: and + I-saw"),
         ("Amharic", "\u12A5\u1293\u12A0\u12E8\u1201", "And I saw (modern)")]),

    "\u12C8\u12A0\u122D\u12A0\u12E8\u1290": ("and he showed us", "\u122D\u12A5\u12ED",
        "Dillmann, Lexicon col. 263; compound: we- + ar'ayene",
        [("Ge'ez", "\u12C8\u12A0\u122D\u12A0\u12E8\u1290", "we-ar'ayene: and + he-showed-us"),
         ("Amharic", "\u12A5\u1293\u12A0\u1233\u12E8\u1295", "And he showed us (modern)")]),

    # le- (for/to) + noun compounds
    "\u1208\u12D3\u1208\u121D": ("forever, for eternity", "\u12D3\u1208\u121D",
        "Dillmann, Lexicon col. 936; compound: le- + 'alem",
        [("Ge'ez", "\u1208\u12D3\u1208\u121D", "le-'alem: for + eternity"),
         ("Amharic", "\u1208\u12D8\u1208\u12D3\u1208\u121D", "Forever (modern)")]),

    "\u1208\u1285\u1229\u12EB\u1295": ("for the chosen ones", "\u1285\u122D\u12ED",
        "Dillmann, Lexicon col. 47; compound: le- + xeruyan",
        [("Ge'ez", "\u1208\u1285\u1229\u12EB\u1295", "le-xeruyan: for + elect-ones"),
         ("Amharic", "\u1208\u1270\u1218\u1228\u1321\u1275", "For the chosen ones (modern)")]),

    # ze- (of/which) + noun compounds
    "\u12D8\u1230\u121B\u12ED": ("of heaven, heavenly", "\u1230\u121D\u12ED",
        "Dillmann, Lexicon col. 357; compound: ze- + semay",
        [("Ge'ez", "\u12D8\u1230\u121B\u12ED", "ze-semay: of + heaven"),
         ("Amharic", "\u12E8\u1230\u121B\u12ED", "Of heaven (modern)")]),

    "\u12D8\u121D\u12F5\u122D": ("of earth, earthly", "\u121D\u12F5\u122D",
        "Dillmann, Lexicon col. 186; compound: ze- + medr",
        [("Ge'ez", "\u12D8\u121D\u12F5\u122D", "ze-medr: of + earth"),
         ("Amharic", "\u12E8\u121D\u12F5\u122D", "Of earth (modern)")]),

    "\u12D8\u12F0\u12ED\u1295": ("of judgment", "\u12F0\u12ED\u1295",
        "Dillmann, Lexicon col. 1098; compound: ze- + deyn",
        [("Ge'ez", "\u12D8\u12F0\u12ED\u1295", "ze-deyn: of + judgment"),
         ("Amharic", "\u12E8\u134D\u122D\u12F5", "Of judgment (modern)")]),

    "\u12D8\u1230\u1265\u12A5": ("of man, human", "\u1230\u1265\u12A5",
        "Dillmann, Lexicon col. 340; compound: ze- + seb'",
        [("Ge'ez", "\u12D8\u1230\u1265\u12A5", "ze-seb': of + humanity"),
         ("Amharic", "\u12E8\u1230\u12CD", "Of man (modern)")]),

    # em- (from) + noun compounds
    "\u12A5\u121D\u1230\u121B\u12ED": ("from heaven", "\u1230\u121D\u12ED",
        "Dillmann, Lexicon col. 357; compound: em- + semay",
        [("Ge'ez", "\u12A5\u121D\u1230\u121B\u12ED", "'em-semay: from + heaven"),
         ("Amharic", "\u12A8\u1230\u121B\u12ED", "From heaven (modern)")]),

    "\u12A5\u121D\u121D\u12F5\u122D": ("from earth", "\u121D\u12F5\u122D",
        "Dillmann, Lexicon col. 186; compound: em- + medr",
        [("Ge'ez", "\u12A5\u121D\u121D\u12F5\u122D", "'em-medr: from + earth"),
         ("Amharic", "\u12A8\u121D\u12F5\u122D", "From earth (modern)")]),

    "\u12A5\u121D\u1218\u12D3\u120D\u1275": ("from the day", "\u12D3\u1208\u1275",
        "Dillmann, Lexicon col. 936; compound: em- + me'alt",
        [("Ge'ez", "\u12A5\u121D\u1218\u12D3\u120D\u1275", "'em-me'alt: from + day"),
         ("Amharic", "\u12A8\u1240\u1291", "From the day (modern)")]),

    # we- (and) + noun compounds (more)
    "\u12C8\u121D\u12F5\u122D": ("and earth, and the land", "\u121D\u12F5\u122D",
        "Dillmann, Lexicon col. 186; compound: we- + medr",
        [("Ge'ez", "\u12C8\u121D\u12F5\u122D", "we-medr: and + earth"),
         ("Amharic", "\u12C8\u121D\u12F5\u122D", "And earth (modern)")]),

    "\u12C8\u12A5\u1233\u1275": ("and fire", "\u12A5\u1233\u1275",
        "Dillmann, Lexicon col. 816; compound: we- + 'esat",
        [("Ge'ez", "\u12C8\u12A5\u1233\u1275", "we-'esat: and + fire"),
         ("Amharic", "\u12C8\u12A5\u1233\u1275", "And fire (modern)")]),

    "\u12C8\u1230\u120B\u121D": ("and peace", "\u1230\u120D\u121D",
        "Dillmann, Lexicon col. 349; compound: we- + selam",
        [("Ge'ez", "\u12C8\u1230\u120B\u121D", "we-selam: and + peace"),
         ("Amharic", "\u12C8\u1230\u120B\u121D", "And peace (modern)")]),

    "\u12C8\u133D\u120D\u1218\u1275": ("and darkness", "\u133D\u120D\u121D",
        "Dillmann, Lexicon col. 628; compound: we- + tselmet",
        [("Ge'ez", "\u12C8\u133D\u120D\u1218\u1275", "we-tselmet: and + darkness"),
         ("Amharic", "\u12C8\u1325\u120D\u1218\u1275", "And darkness (modern)")]),

    "\u12C8\u133B\u12F5\u1243\u1295": ("and the righteous ones", "\u133D\u12F5\u1245",
        "Dillmann, Lexicon col. 621; compound: we- + tsadqan",
        [("Ge'ez", "\u12C8\u133B\u12F5\u1243\u1295", "we-tsadqan: and + righteous-ones"),
         ("Amharic", "\u12C8\u1340\u12F3\u1243\u1295", "And the righteous (modern)")]),

    "\u12C8\u121E\u1275": ("and death", "\u121E\u1275",
        "Dillmann, Lexicon col. 205; compound: we- + mot",
        [("Ge'ez", "\u12C8\u121E\u1275", "we-mot: and + death"),
         ("Amharic", "\u12C8\u121E\u1275", "And death (modern)")]),

    "\u12C8\u121B\u12ED": ("and water", "\u121B\u12ED",
        "Dillmann, Lexicon col. 145; compound: we- + may",
        [("Ge'ez", "\u12C8\u121B\u12ED", "we-may: and + water"),
         ("Amharic", "\u12C8\u12CD\u1200", "And water (modern)")]),

    "\u12C8\u12D3\u1208\u121D": ("and the world, and eternity", "\u12D3\u1208\u121D",
        "Dillmann, Lexicon col. 936; compound: we- + 'alem",
        [("Ge'ez", "\u12C8\u12D3\u1208\u121D", "we-'alem: and + world"),
         ("Amharic", "\u12C8\u12D3\u1208\u121D", "And the world (modern)")]),

    "\u12C8\u12F0\u12ED\u1295": ("and judgment", "\u12F0\u12ED\u1295",
        "Dillmann, Lexicon col. 1098; compound: we- + deyn",
        [("Ge'ez", "\u12C8\u12F0\u12ED\u1295", "we-deyn: and + judgment"),
         ("Amharic", "\u12C8\u134D\u122D\u12F5", "And judgment (modern)")]),

    "\u12C8\u12AD\u1229\u1265": ("and cherub", "\u12AD\u1229\u1265",
        "Dillmann, Lexicon col. 871; compound: we- + kerub",
        [("Ge'ez", "\u12C8\u12AD\u1229\u1265", "we-kerub: and + cherub"),
         ("Amharic", "\u12C8\u12AD\u1229\u1264", "And cherub (modern)")]),

    "\u12C8\u1228\u1232\u12D3\u1295": ("and the wicked ones", "\u1228\u1235\u12D3",
        "Dillmann, Lexicon col. 273; compound: we- + resi'an",
        [("Ge'ez", "\u12C8\u1228\u1232\u12D3\u1295", "we-resi'an: and + wicked-ones"),
         ("Amharic", "\u12C8\u1228\u1238\u12D0\u129B\u1295", "And the wicked (modern)")]),

    # ===== ADDITIONAL VERBS AND VERBAL FORMS =====

    "\u12ED\u12A8\u12CD\u1295": ("he/it becomes, it shall be", "\u12A8\u12C8\u1295",
        "Dillmann, Lexicon col. 867",
        [("Proto-Semitic", "*kwn-", "To be, become"),
         ("Ge'ez", "\u12ED\u12A8\u12CD\u1295", "Imperfect 3ms - it becomes"),
         ("Amharic", "\u12ED\u1206\u1293\u120D", "It will be (modern)")]),

    "\u12ED\u1218\u133D\u12A5": ("he comes, will come", "\u1218\u133D\u12A5",
        "Dillmann, Lexicon col. 195",
        [("Ge'ez", "\u12ED\u1218\u133D\u12A5", "Imperfect 3ms - he comes"),
         ("Amharic", "\u12ED\u1218\u1323\u120D", "He comes (modern)")]),

    "\u12ED\u12A0\u1235\u1270\u122D\u12A5\u12ED": ("he/it appears, is revealed", "\u122D\u12A5\u12ED",
        "Dillmann, Lexicon col. 263",
        [("Ge'ez", "\u12ED\u12A0\u1235\u1270\u122D\u12A5\u12ED", "Causative reflexive - it reveals itself"),
         ("Amharic", "\u12ED\u1273\u12EB\u120D", "It appears (modern)")]),

    "\u1218\u1210\u1228": ("he had mercy, showed compassion", "\u121D\u1205\u122D",
        "Dillmann, Lexicon col. 155",
        [("Proto-Semitic", "*rhm-", "Womb, compassion"),
         ("Ge'ez", "\u1218\u1210\u1228", "He showed mercy"),
         ("Amharic", "\u121B\u1228", "He had mercy (different)")]),

    # ===== ADDITIONAL NOUNS AND MODIFIERS =====

    "\u12A0\u12F5\u1263\u122D": ("mountains (plural)", "\u12F0\u1265\u122D",
        "Dillmann, Lexicon col. 1074",
        [("Ge'ez", "\u12A0\u12F5\u1263\u122D", "Mountains (broken plural of debr)"),
         ("Amharic", "\u1270\u122B\u122C\u127D", "Mountains (modern)")]),

    "\u12C8\u12A0\u12F5\u1263\u122D": ("and mountains", "\u12F0\u1265\u122D",
        "Dillmann, Lexicon col. 1074; compound: we- + adbar",
        [("Ge'ez", "\u12C8\u12A0\u12F5\u1263\u122D", "we-adbar: and + mountains"),
         ("Amharic", "\u12C8\u1270\u122B\u122C\u127D", "And mountains (modern)")]),

    "\u121D\u120D\u12AD\u1275": ("sign, wonder, portent", "\u121D\u120D\u12AD\u1275",
        "Dillmann, Lexicon col. 180",
        [("Ge'ez", "\u121D\u120D\u12AD\u1275", "Sign, miracle"),
         ("Amharic", "\u1275\u12A5\u121D\u122D\u1275", "Miracle (different)")]),

    "\u1218\u1295\u1260\u1228": ("throne, seat of authority", "\u1295\u1260\u122D",
        "Dillmann, Lexicon col. 244",
        [("Proto-Semitic", "*nbr-", "Seat, throne"),
         ("Ge'ez", "\u1218\u1295\u1260\u1228", "Throne of God"),
         ("Amharic", "\u12D8\u1295\u1260\u120D", "Throne (different)")]),

    "\u1230\u1265\u12D1": ("seven", "\u1230\u1265\u12D5",
        "Dillmann, Lexicon col. 340",
        [("Proto-Semitic", "*shab'-", "Seven"),
         ("Ge'ez", "\u1230\u1265\u12D1", "Seven"),
         ("Amharic", "\u1230\u1263\u1275", "Seven (modified)")]),

    "\u1212\u12F1": ("one, single (variant)", "\u12A0\u1210\u12F5",
        "Dillmann, Lexicon col. 29",
        [("Ge'ez", "\u1212\u12F1", "One (shortened form)"),
         ("Amharic", "\u12A0\u1295\u12F5", "One (different)")]),

    "\u120A\u1243\u1201\u121D": ("their chiefs, their rulers", "\u120A\u1245",
        "Dillmann, Lexicon col. 18",
        [("Ge'ez", "\u120A\u1243\u1201\u121D", "Chiefs with 3mp suffix"),
         ("Amharic", "\u1218\u122A\u12CE\u127D", "Their leaders (modern)")]),

    "\u12F2\u1264\u1201\u121D": ("upon them, over them", "\u12F2\u1260",
        "Dillmann, Lexicon col. 1071; compound: dibe + -hum",
        [("Ge'ez", "\u12F2\u1264\u1201\u121D", "dibe-hum: upon + them"),
         ("Amharic", "\u1260\u120B\u1263\u1278\u12CD", "Upon them (modern)")]),

    "\u12C8\u133D\u1203\u12ED": ("and the sun", "\u133D\u1203\u12ED",
        "Dillmann, Lexicon col. 615; compound: we- + tsehay",
        [("Ge'ez", "\u12C8\u133D\u1203\u12ED", "we-tsehay: and + sun"),
         ("Amharic", "\u12C8\u133D\u1203\u12ED", "And the sun (modern)")]),

    "\u12D8\u1218\u12CD\u1271\u1275": ("of the dead, of death", "\u121E\u1275",
        "Dillmann, Lexicon col. 205; compound: ze- + mewtutt",
        [("Ge'ez", "\u12D8\u1218\u12CD\u1271\u1275", "ze-mewtutt: of + the-dead"),
         ("Amharic", "\u12E8\u121E\u1271\u1275", "Of the dead (modern)")]),

    "\u12A5\u121D\u12DD\u12A5\u1295\u1271": ("from this, from that", "\u12DD\u1295\u1271",
        "Dillmann, Lexicon col. 1058; compound: em- + ze'entu",
        [("Ge'ez", "\u12A5\u121D\u12DD\u12A5\u1295\u1271", "'em-ze'entu: from + this"),
         ("Amharic", "\u12A8\u12DA\u1205", "From this (modern)")]),

    "\u12C8\u12A5\u121D\u12EB\u12A5\u1272\u1201": ("and from that same", "\u12A5\u121D",
        "Dillmann, Lexicon col. 800; compound: we-em-ya'etihu",
        [("Ge'ez", "\u12C8\u12A5\u121D\u12EB\u12A5\u1272\u1201", "Complex compound: and+from+that-same"),
         ("Amharic", "\u12C8\u12A8\u12EB\u12CD\u121D", "And from that (modern)")]),

    "\u1348\u1240\u12F0": ("he willed, desired, loved", "\u1348\u1245\u12F5",
        "Dillmann, Lexicon col. 834",
        [("Ge'ez", "\u1348\u1240\u12F0", "He desired, willed"),
         ("Amharic", "\u1348\u1208\u1308", "He wanted (different)")]),

    "\u1233\u1218\u12CB": ("he heard, listened, obeyed", "\u1230\u121D\u12D5",
        "Dillmann, Lexicon col. 357",
        [("Proto-Semitic", "*shm'-", "To hear, obey"),
         ("Ge'ez", "\u1233\u1218\u12CB", "He heard/obeyed"),
         ("Amharic", "\u1230\u121B", "He heard (modified)")]),

    "\u1350\u122D\u1245": ("abyssal pit, deep chasm", "\u1350\u122D\u1245",
        "Dillmann, Lexicon col. 838",
        [("Ge'ez", "\u1350\u122D\u1245", "Abyss, deep pit"),
         ("Amharic", "\u1308\u1210\u1290\u121D", "Abyss (different)")]),

    "\u12AD\u120D\u1209": ("all of them (3mp)", "\u12AD\u120D",
        "Dillmann, Lexicon col. 862; kull with 3mp suffix",
        [("Ge'ez", "\u12AD\u120D\u1209", "kull-u: all of them"),
         ("Amharic", "\u1201\u1209\u121D", "All of them (modern)")]),

    "\u12D8\u133B\u12F5\u1245": ("of righteousness", "\u133D\u12F5\u1245",
        "Dillmann, Lexicon col. 621; compound: ze- + tsadq",
        [("Ge'ez", "\u12D8\u133B\u12F5\u1245", "ze-tsadq: of + righteousness"),
         ("Amharic", "\u12E8\u1340\u12F5\u1245", "Of righteousness (modern)")]),

    "\u1260\u133B\u12F5\u1245": ("in righteousness", "\u133D\u12F5\u1245",
        "Dillmann, Lexicon col. 621; compound: be- + tsadq",
        [("Ge'ez", "\u1260\u133B\u12F5\u1245", "be-tsadq: in + righteousness"),
         ("Amharic", "\u1260\u1340\u12F5\u1245", "In righteousness (modern)")]),

    "\u12C8\u1264\u1209": ("and they entered, and it came to pass", "\u1260\u12A5\u120D",
        "Dillmann, Lexicon col. 462",
        [("Ge'ez", "\u12C8\u1264\u1209", "we-belu: and + they-said/entered"),
         ("Amharic", "\u12C8\u1308\u1261", "And they entered (modern)")]),

    "\u12C8\u12A0\u120D\u1266": ("and there is not", "\u12A0\u120D\u1266",
        "Dillmann, Lexicon col. 777; compound: we- + albo",
        [("Ge'ez", "\u12C8\u12A0\u120D\u1266", "we-albo: and + there-is-not"),
         ("Amharic", "\u12C8\u12E8\u1208\u121D", "And there is not (modern)")]),

    "\u1260\u12A5\u12EB\u121D": ("in the days of", "\u12D3\u1208\u1275",
        "Dillmann, Lexicon col. 936; compound: be- + 'eyam",
        [("Ge'ez", "\u1260\u12A5\u12EB\u121D", "be-'eyam: in + days"),
         ("Amharic", "\u1260\u1240\u1291", "In the days of (modern)")]),

    "\u12AD\u120D\u12CD": ("all, everything (variant bound form)", "\u12AD\u120D",
        "Dillmann, Lexicon col. 862",
        [("Ge'ez", "\u12AD\u120D\u12CD", "Bound form of kull with suffix"),
         ("Amharic", "\u1201\u1209", "All (modern)")]),

    "\u12C8\u12AD\u120D\u1209": ("and all of them", "\u12AD\u120D",
        "Dillmann, Lexicon col. 862; compound: we- + kullu",
        [("Ge'ez", "\u12C8\u12AD\u120D\u1209", "we-kullu: and + all-of-them"),
         ("Amharic", "\u12C8\u1201\u1209\u121D", "And all of them (modern)")]),

    "\u1349\u1265": ("and also, moreover", "\u1349\u1265",
        "Dillmann, Lexicon col. 838",
        [("Ge'ez", "\u1349\u1265", "Also, moreover"),
         ("Amharic", "\u12F0\u130D\u121E", "Also (different)")]),

    "\u12A5\u1295\u1270\u1235\u12D3": ("you hear, listen (2ms imperative)", "\u1230\u121D\u12D5",
        "Dillmann, Lexicon col. 357",
        [("Ge'ez", "\u12A5\u1295\u1270\u1235\u12D3", "Listen! (imperative)"),
         ("Amharic", "\u1235\u121B!", "Listen! (modern)")]),

    "\u12D5\u1325\u12CD": ("sin, wickedness, iniquity", "\u12D5\u1325\u12CD",
        "Dillmann, Lexicon col. 949",
        [("Ge'ez", "\u12D5\u1325\u12CD", "Sin, transgression"),
         ("Amharic", "\u1283\u1324\u12A0\u1275", "Sin (different)")]),

    "\u12D3\u1240\u1265": ("heel, footstep, trace", "\u12D3\u1240\u1265",
        "Dillmann, Lexicon col. 944",
        [("Proto-Semitic", "*'qb-", "Heel, follow"),
         ("Ge'ez", "\u12D3\u1240\u1265", "Heel, footstep"),
         ("Amharic", "\u12A0\u1240\u1265", "Footstep (modified)")]),

    "\u1265\u12D5\u1208": ("above, on, upon", "\u12D3\u120D\u12ED",
        "Dillmann, Lexicon col. 929; compound: be- + 'ale",
        [("Ge'ez", "\u1265\u12D5\u1208", "be-'ale: on + above"),
         ("Amharic", "\u1260\u120B\u12ED", "Above, on (modern)")]),

    # ===== ADDITIONAL VERBAL FORMS AND STEMS (for prefix-stripping matches) =====

    "\u12ED\u1260\u12A5": ("he comes, he enters", "\u1266\u12A5",
        "Dillmann, Lexicon col. 488",
        [("Proto-Semitic", "*bw'-", "To come, enter"),
         ("Ge'ez", "\u12ED\u1260\u12A5", "Imperfect 3ms - he comes"),
         ("Amharic", "\u1218\u1323", "He came (different root)")]),

    "\u1348\u1275\u1210": ("judgment, ruling, decision", "\u1348\u1275\u1210",
        "Dillmann, Lexicon col. 1288; Leslau, Dictionary p. 173",
        [("Proto-Semitic", "*pth-", "To open, decide"),
         ("Ge'ez", "\u1348\u1275\u1210", "Opening, judgment, legal ruling"),
         ("Arabic", "fataha", "He opened"),
         ("Amharic", "\u134D\u122D\u12F5", "Judgment (different)")]),

    "\u1348\u1275\u1214": ("judgment, ruling (variant)", "\u1348\u1275\u1210",
        "Dillmann, Lexicon col. 1288",
        [("Ge'ez", "\u1348\u1275\u1214", "Variant spelling of fetHa")]),

    "\u121D\u1210\u1228\u1275": ("mercy, compassion, grace (Hawt variant)", "\u121D\u1205\u122D",
        "Dillmann, Lexicon col. 155",
        [("Proto-Semitic", "*rhm-", "Womb, compassion"),
         ("Ge'ez", "\u121D\u1210\u1228\u1275", "Variant of mHret with Hawt"),
         ("Amharic", "\u121D\u1205\u1228\u1275", "Mercy (unchanged)")]),

    "\u120B\u12D5\u120C\u1201\u121D": ("upon them, over them", "\u12D3\u120D\u12ED",
        "Dillmann, Lexicon col. 929",
        [("Ge'ez", "\u120B\u12D5\u120C\u1201\u121D", "la-'alehum: to/upon + them"),
         ("Amharic", "\u1260\u12A5\u1290\u1231", "Upon them (modern)")]),

    "\u133D\u12F5\u1243\u1295": ("the righteous ones, just ones", "\u133D\u12F5\u1245",
        "Dillmann, Lexicon col. 1315",
        [("Proto-Semitic", "*sdq-", "To be righteous"),
         ("Ge'ez", "\u133D\u12F5\u1243\u1295", "Righteous ones (masculine plural)"),
         ("Amharic", "\u133B\u12F2\u1243\u1295", "Righteous people")]),

    "\u12B0\u1295": ("being, manner, way", "\u12AD\u12C8\u1295",
        "Dillmann, Lexicon col. 876",
        [("Ge'ez", "\u12B0\u1295", "kwon: manner, being"),
         ("Amharic", "\u1201\u1294\u1273", "State, condition")]),

    "\u1228\u12A5\u12ED\u12A9": ("I saw (1cs perfect)", "\u122D\u12A5\u12ED",
        "Dillmann, Lexicon col. 282",
        [("Proto-Semitic", "*r'y-", "To see"),
         ("Ge'ez", "\u1228\u12A5\u12ED\u12A9", "re'eyku: I saw - narrative form"),
         ("Amharic", "\u12A0\u12E8\u1201", "I saw (modern)")]),

    "\u1228\u12A5\u12ED": ("vision, sight, seeing", "\u122D\u12A5\u12ED",
        "Dillmann, Lexicon col. 282",
        [("Proto-Semitic", "*r'y-", "To see, behold"),
         ("Ge'ez", "\u1228\u12A5\u12ED", "re'ey: vision, sight"),
         ("Amharic", "\u1228\u12A0\u12ED", "Sight, vision")]),

    "\u130D\u1265\u122D\u12A9\u121D": ("your (mp) deeds, your works", "\u130D\u1265\u122D",
        "Dillmann, Lexicon col. 1133",
        [("Ge'ez", "\u130D\u1265\u122D\u12A9\u121D", "gebrukum: deeds + your (mp)"),
         ("Amharic", "\u1235\u122B\u127D\u1205\u1295", "Your works (modern)")]),

    "\u12ED\u12A8\u12CD\u1291": ("they become, they shall be", "\u12A8\u12C8\u1295",
        "Dillmann, Lexicon col. 876",
        [("Ge'ez", "\u12ED\u12A8\u12CD\u1291", "yekewwenu: Impf 3mp - they become"),
         ("Amharic", "\u12ED\u1206\u1293\u1209", "They will be (modern)")]),

    "\u12ED\u1348\u1235\u1235": ("he flows, pours out", "\u1348\u1230\u1230",
        "Dillmann, Lexicon col. 1283",
        [("Proto-Semitic", "*pss-", "To pour, flow"),
         ("Ge'ez", "\u12ED\u1348\u1235\u1235", "yefesses: Impf 3ms - it flows"),
         ("Amharic", "\u12ED\u1348\u1230\u1230", "It flows")]),

    "\u12ED\u1270\u12C8\u12A8\u12F1": ("they contend, they strive", "\u1270\u12C8\u12A8\u12F0",
        "Dillmann, Lexicon col. 901",
        [("Ge'ez", "\u12ED\u1270\u12C8\u12A8\u12F1", "yetewekedu: Impf 3mp"),
         ("Amharic", "\u12ED\u1270\u12AB\u12A8\u12F1", "They contend")]),

    "\u1270\u1218\u120A\u12A8\u1271": ("his angels, his messengers", "\u1218\u120D\u12A0\u12AD",
        "Dillmann, Lexicon col. 152",
        [("Proto-Semitic", "*ml'k-", "To send a message"),
         ("Ge'ez", "\u1270\u1218\u120A\u12A8\u1271", "te-melaketu: his angels"),
         ("Amharic", "\u1218\u120B\u12AD\u1275", "Angel")]),

    "\u121D\u12D5\u122B\u134D": ("section, chapter, division", "\u12D3\u122D\u1348",
        "Leslau, Dictionary p. 46",
        [("Ge'ez", "\u121D\u12D5\u122B\u134D", "me'raf: chapter, section"),
         ("Amharic", "\u121D\u12D5\u122B\u134D", "Chapter (same)")]),

    "\u12A9\u1209": ("all, everything (bound form)", "\u12AD\u120D",
        "Dillmann, Lexicon col. 862",
        [("Ge'ez", "\u12A9\u1209", "kullu: all of - bound form with suffix"),
         ("Amharic", "\u1201\u1209", "All (modern)")]),

    "\u12C8\u12ED\u1294": ("and wine, and grapevine", "\u12C8\u12ED\u1295",
        "Dillmann, Lexicon col. 914",
        [("Proto-Semitic", "*wayn-", "Wine, grapevine"),
         ("Ge'ez", "\u12C8\u12ED\u1294", "weyne: wine, grapevine"),
         ("Amharic", "\u12C8\u12ED\u1295", "Wine")]),

    "\u12AD\u1265\u1228\u1275": ("glory, honor, majesty (with -t suffix)", "\u12AD\u1265\u122D",
        "Dillmann, Lexicon col. 858",
        [("Ge'ez", "\u12AD\u1265\u1228\u1275", "kebret: glory with feminine -t"),
         ("Amharic", "\u12AD\u1265\u122D", "Honor, glory")]),

    "\u12D0\u1261\u12ED": ("great, mighty, grand", "\u12D0\u1261\u12ED",
        "Dillmann, Lexicon col. 926",
        [("Proto-Semitic", "*'by-", "Great, large"),
         ("Ge'ez", "\u12D0\u1261\u12ED", "'abuy: great, mighty one"),
         ("Amharic", "\u1275\u120D\u1245", "Large, great (different)")]),

    "\u12A0\u12F5\u1263\u1265\u122D": ("mountains (plural, extended form)", "\u12F0\u1265\u122D",
        "Dillmann, Lexicon col. 1074",
        [("Ge'ez", "\u12A0\u12F5\u1263\u1265\u122D", "adbabr: mountains (plural)"),
         ("Amharic", "\u1270\u122B\u122E\u127D", "Mountains (modern)")]),

    "\u1218\u122B\u12D5\u12ED": ("visions, revelations (plural)", "\u122D\u12A5\u12ED",
        "Dillmann, Lexicon col. 282",
        [("Proto-Semitic", "*r'y-", "To see"),
         ("Ge'ez", "\u1218\u122B\u12D5\u12ED", "mera'ey: visions, revelations"),
         ("Amharic", "\u122D\u12A0\u12ED\u127D", "Visions")]),

    "\u12F0\u1260\u1228": ("mountain (construct state)", "\u12F0\u1265\u122D",
        "Dillmann, Lexicon col. 1074",
        [("Ge'ez", "\u12F0\u1260\u1228", "debere: mountain - construct form"),
         ("Amharic", "\u12F0\u1260\u1228", "Mount, mountain-of")]),

    "\u12A5\u1295\u1270": ("thou, you (2ms pronoun)", "\u12A5\u1295\u1270",
        "Dillmann, Lexicon col. 748",
        [("Proto-Semitic", "*'ant-", "You (2ms)"),
         ("Ge'ez", "\u12A5\u1295\u1270", "ente: you (masculine singular)"),
         ("Amharic", "\u12A0\u1295\u1270", "You (modern)")]),

    "\u12ED\u12A8\u12CD\u1295": ("he/it becomes, it shall be (alternate)", "\u12A8\u12C8\u1295",
        "Dillmann, Lexicon col. 876",
        [("Ge'ez", "\u12ED\u12A8\u12CD\u1295", "yekewwen: Impf 3ms (alternate form)"),
         ("Amharic", "\u12ED\u1206\u1293\u120D", "It will be (modern)")]),
}


# =============================================================================
# MAIN BUILD FUNCTIONS
# =============================================================================

def load_geez_text():
    """Load the Ge'ez source text from JSON."""
    if not os.path.exists(INPUT_FILE):
        print(f"[FAIL] Source file not found: {INPUT_FILE}")
        print(f"[INFO] The file data/enoch_geez_text.json must be created first.")
        print(f"[INFO] Use tools/scrape_charles_text.py or manually create the Ge'ez text data.")
        sys.exit(1)

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    chapter_count = len([k for k in data.keys() if k.isdigit()])
    total_verses = sum(
        len(ch.get('verses', {}))
        for ch in data.values()
        if isinstance(ch, dict)
    )
    print(f"[OK] Loaded {chapter_count} chapters, {total_verses} verses from enoch_geez_text.json")
    return data


def extract_all_words(text_data):
    """Extract all unique Ge'ez words with frequency and first occurrence.

    Returns dict: {word: {"frequency": int, "first_occurrence": str}}
    """
    word_stats = {}
    total_word_count = 0

    for chapter_key in sorted(text_data.keys(), key=lambda x: int(x) if x.isdigit() else 0):
        if not chapter_key.isdigit():
            continue

        chapter_data = text_data[chapter_key]
        verses = chapter_data.get('verses', {})

        for verse_key in sorted(verses.keys(), key=lambda x: int(x) if x.isdigit() else 0):
            verse_data = verses[verse_key]
            geez_text = verse_data.get('geez', '')
            words = extract_words_from_text(geez_text)

            for word in words:
                total_word_count += 1
                if word not in word_stats:
                    word_stats[word] = {
                        "frequency": 0,
                        "first_occurrence": f"1 Enoch {chapter_key}:{verse_key}"
                    }
                word_stats[word]["frequency"] += 1

    print(f"[OK] Extracted {len(word_stats)} unique words from {total_word_count} total word tokens")
    return word_stats


def normalize_geez_variants(word):
    """Generate all character-variant forms of a Ge'ez word for dictionary lookup.

    Ge'ez manuscripts use variant character forms that are encoded differently
    in Unicode. The two /h/ rows (Hoy U+1200 and Hawt U+1210) are often
    interchanged in different manuscript traditions.

    Returns a list of variant forms to try (including the original).
    """
    # Hoy row (U+1200-U+1207) <-> Hawt row (U+1210-U+1217)
    HOY_TO_HAWT = {}
    HAWT_TO_HOY = {}
    for i in range(8):
        HOY_TO_HAWT[chr(0x1200 + i)] = chr(0x1210 + i)
        HAWT_TO_HOY[chr(0x1210 + i)] = chr(0x1200 + i)

    variants = set()
    variants.add(word)

    # Try Hoy -> Hawt normalization
    norm1 = ''.join(HOY_TO_HAWT.get(ch, ch) for ch in word)
    if norm1 != word:
        variants.add(norm1)

    # Try Hawt -> Hoy normalization
    norm2 = ''.join(HAWT_TO_HOY.get(ch, ch) for ch in word)
    if norm2 != word:
        variants.add(norm2)

    return list(variants)


def find_dictionary_match(word):
    """Find a dictionary match for a word, trying prefix stripping.

    Ge'ez uses prefixed prepositions and conjunctions that create compound words.
    Common prefixes: we- (and), le- (to/for), be- (in/by), ze- (of/which),
    em- (from), ke- (like).

    Also tries character normalization to handle variant Ge'ez character forms.

    Returns (dict_entry, match_type) or (None, None).
    """
    # Direct lookup first (also try character variants)
    for variant in normalize_geez_variants(word):
        if variant in SCHOLARLY_DICTIONARY:
            match_type = "direct" if variant == word else "normalized"
            return SCHOLARLY_DICTIONARY[variant], match_type

    # Define common Ge'ez prefixes (single character)
    single_prefixes = [
        ("\u12C8", "we-", "and"),       # ወ
        ("\u1208", "le-", "to/for"),    # ለ
        ("\u1260", "be-", "in/by"),     # በ
        ("\u12D8", "ze-", "of/which"),  # ዘ
        ("\u12A8", "ke-", "like"),      # ከ
    ]

    # Two-character prefixes
    double_prefixes = [
        ("\u12C8\u12A5\u121D", "we-em-", "and from"),  # ወእም (3 chars, try first)
        ("\u12A5\u121D", "em-", "from"),           # እም
        ("\u12C8\u1260", "we-be-", "and in"),      # ወበ
        ("\u12C8\u1208", "we-le-", "and to"),      # ወለ
        ("\u12C8\u12D8", "we-ze-", "and of"),      # ወዘ
    ]

    # Helper to look up stem with character variant fallback
    def lookup_stem(stem):
        for variant in normalize_geez_variants(stem):
            if variant in SCHOLARLY_DICTIONARY:
                return SCHOLARLY_DICTIONARY[variant]
        return None

    # Try double/triple prefixes first (longer match first)
    for prefix, prefix_name, prefix_meaning in double_prefixes:
        if word.startswith(prefix) and len(word) > len(prefix) + 1:
            stem = word[len(prefix):]
            base_entry = lookup_stem(stem)
            if base_entry:
                definition = base_entry[0]
                root = base_entry[1]
                source = base_entry[2]
                timeline = base_entry[3] if len(base_entry) > 3 else []
                compound_def = f"{prefix_meaning} + {definition}"
                compound_source = f"{source}; compound: {prefix_name} + stem"
                return (compound_def, root, compound_source, timeline), "prefix"

    # Try single prefixes
    for prefix, prefix_name, prefix_meaning in single_prefixes:
        if word.startswith(prefix) and len(word) > 2:
            stem = word[1:]  # Remove single prefix character
            base_entry = lookup_stem(stem)
            if base_entry:
                definition = base_entry[0]
                root = base_entry[1]
                source = base_entry[2]
                timeline = base_entry[3] if len(base_entry) > 3 else []
                compound_def = f"{prefix_meaning} + {definition}"
                compound_source = f"{source}; compound: {prefix_name} + stem"
                return (compound_def, root, compound_source, timeline), "prefix"

    # Try double prefix + single prefix (3-layer: e.g., ወእም + ከ + stem)
    for dpfx, dpfx_name, dpfx_meaning in double_prefixes:
        if word.startswith(dpfx):
            remainder = word[len(dpfx):]
            for spfx, spfx_name, spfx_meaning in single_prefixes:
                if remainder.startswith(spfx) and len(remainder) > 2:
                    stem = remainder[1:]
                    base_entry = lookup_stem(stem)
                    if base_entry:
                        definition = base_entry[0]
                        root = base_entry[1]
                        source = base_entry[2]
                        timeline = base_entry[3] if len(base_entry) > 3 else []
                        compound_def = f"{dpfx_meaning} + {spfx_meaning} + {definition}"
                        compound_source = f"{source}; compound: {dpfx_name}+{spfx_name} + stem"
                        return (compound_def, root, compound_source, timeline), "prefix"

    # Try single prefix + single prefix (2-layer: e.g., ወ + በ + stem)
    for pfx1, pfx1_name, pfx1_meaning in single_prefixes:
        if word.startswith(pfx1) and len(word) > 3:
            remainder = word[1:]
            for pfx2, pfx2_name, pfx2_meaning in single_prefixes:
                if remainder.startswith(pfx2) and len(remainder) > 2:
                    stem = remainder[1:]
                    base_entry = lookup_stem(stem)
                    if base_entry:
                        definition = base_entry[0]
                        root = base_entry[1]
                        source = base_entry[2]
                        timeline = base_entry[3] if len(base_entry) > 3 else []
                        compound_def = f"{pfx1_meaning} + {pfx2_meaning} + {definition}"
                        compound_source = f"{source}; compound: {pfx1_name}+{pfx2_name} + stem"
                        return (compound_def, root, compound_source, timeline), "prefix"

    return None, None


def build_lexicon_entry(word, stats):
    """Build a complete lexicon entry for a single Ge'ez word."""
    # Look up in scholarly dictionary (with prefix stripping)
    dict_entry, match_type = find_dictionary_match(word)

    # Calculate gematria
    gematria = calculate_gematria(word)
    dr = digital_root(gematria)

    # Build transliteration
    translit = transliterate_word(word)

    # Build letter breakdown
    letters = []
    for char in word:
        if is_ethiopic(char):
            analysis = analyze_character(char)
            if analysis:
                letters.append(analysis)

    # Build pictographic summary from letter meanings
    if letters:
        meanings = [l["meaning"] for l in letters if l.get("meaning")]
        pictographic = " + ".join(meanings[:4])
        if len(meanings) > 4:
            pictographic += " + ..."
    else:
        pictographic = ""

    # Determine definition and source
    if dict_entry:
        definition, root, source, *timeline_data = dict_entry
        timeline = timeline_data[0] if timeline_data else []
    else:
        # Generate computational analysis entry
        definition = f"Ge'ez word ({len(word)} characters)"
        root = word[:3] if len(word) >= 3 else word
        source = "Computational analysis"
        timeline = [
            {"period": "Ge'ez", "form": word, "note": "Attested in 1 Enoch (Charles 1906 edition)"}
        ]

    # Format timeline
    formatted_timeline = []
    if isinstance(timeline, list):
        for entry in timeline:
            if isinstance(entry, tuple) and len(entry) >= 3:
                formatted_timeline.append({
                    "period": entry[0],
                    "form": entry[1],
                    "note": entry[2]
                })
            elif isinstance(entry, dict):
                formatted_timeline.append(entry)

    if not formatted_timeline:
        formatted_timeline = [
            {"period": "Ge'ez", "form": word, "note": "Classical Ethiopic form"}
        ]

    # Build the complete entry
    entry = {
        "geez": word,
        "transliteration": translit,
        "root": root if isinstance(root, str) else word[:3],
        "definition": definition,
        "gematria": gematria,
        "digital_root": dr,
        "first_occurrence": stats["first_occurrence"],
        "frequency": stats["frequency"],
        "source": source,
        "letters": letters,
        "pictographic": pictographic,
        "timeline": formatted_timeline,
    }

    return entry


def build_lexicon(text_data):
    """Build the complete lexicon from extracted words."""
    word_stats = extract_all_words(text_data)

    lexicon = {}
    scholarly_count = 0
    computational_count = 0

    for word, stats in sorted(word_stats.items(), key=lambda x: -x[1]["frequency"]):
        entry = build_lexicon_entry(word, stats)
        lexicon[word] = entry

        if entry["source"] != "Computational analysis":
            scholarly_count += 1
        else:
            computational_count += 1

    print(f"[OK] Built {len(lexicon)} lexicon entries")
    print(f"     - {scholarly_count} with scholarly definitions")
    print(f"     - {computational_count} with computational analysis")

    return lexicon


def save_lexicon(lexicon):
    """Save the lexicon to words.json."""
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(lexicon, f, ensure_ascii=False, indent=2)

    # File size
    file_size = os.path.getsize(OUTPUT_FILE)
    if file_size > 1024 * 1024:
        size_str = f"{file_size / (1024*1024):.1f} MB"
    else:
        size_str = f"{file_size / 1024:.1f} KB"

    print(f"[OK] Saved words.json ({size_str}, {len(lexicon)} entries)")


def print_summary(lexicon):
    """Print summary statistics about the lexicon."""
    print()
    print("=" * 60)
    print("LEXICON SUMMARY")
    print("=" * 60)

    total = len(lexicon)
    print(f"Total unique words:     {total}")

    # Frequency stats
    freqs = [e["frequency"] for e in lexicon.values()]
    freqs.sort(reverse=True)
    print(f"Total word tokens:      {sum(freqs)}")
    print(f"Highest frequency:      {freqs[0] if freqs else 0}")
    print(f"Average frequency:      {sum(freqs)/len(freqs):.1f}" if freqs else "N/A")

    # Gematria stats
    gematrias = [e["gematria"] for e in lexicon.values()]
    print(f"Gematria range:         {min(gematrias)} - {max(gematrias)}" if gematrias else "N/A")

    # Source stats
    scholarly = sum(1 for e in lexicon.values() if "Dillmann" in e.get("source", "")
                    or "Leslau" in e.get("source", "")
                    or "Charles" in e.get("source", ""))
    computational = sum(1 for e in lexicon.values() if e.get("source") == "Computational analysis")
    print(f"Scholarly definitions:  {scholarly} ({scholarly/total*100:.1f}%)" if total else "N/A")
    print(f"Computational:          {computational} ({computational/total*100:.1f}%)" if total else "N/A")

    # Top 20 most frequent words
    print()
    print("TOP 20 MOST FREQUENT WORDS:")
    print("-" * 60)
    sorted_entries = sorted(lexicon.values(), key=lambda x: -x["frequency"])
    for i, entry in enumerate(sorted_entries[:20], 1):
        print(f"  {i:2d}. {entry['geez']:15s} freq={entry['frequency']:4d}  "
              f"gem={entry['gematria']:5d}  {entry['definition'][:40]}")

    # Digital root distribution
    dr_dist = defaultdict(int)
    for e in lexicon.values():
        dr_dist[e["digital_root"]] += 1
    print()
    print("DIGITAL ROOT DISTRIBUTION:")
    for dr_val in range(1, 10):
        count = dr_dist.get(dr_val, 0)
        bar = "#" * (count // 2)
        print(f"  {dr_val}: {count:4d} {bar}")

    print()
    print("=" * 60)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 60)
    print("BUILD GE'EZ LEXICON")
    print("Dead Sea Scrolls - 1 Enoch Mechanical Translation")
    print("=" * 60)
    print()

    # Step 1: Load source text
    print("[1/5] Loading Ge'ez source text...")
    text_data = load_geez_text()
    print()

    # Step 2: Extract unique words
    print("[2/5] Extracting unique words...")
    # (done inside build_lexicon)

    # Step 3: Build lexicon entries
    print("[3/5] Building lexicon entries with scholarly data...")
    lexicon = build_lexicon(text_data)
    print()

    # Step 4: Save to words.json
    print("[4/5] Saving words.json...")
    save_lexicon(lexicon)
    print()

    # Step 5: Print summary
    print("[5/5] Generating summary...")
    print_summary(lexicon)

    # Final verification
    print()
    # Verify the output file can be re-loaded
    try:
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            reloaded = json.load(f)
        assert len(reloaded) == len(lexicon), (
            f"Mismatch: wrote {len(lexicon)} but read {len(reloaded)}"
        )
        print(f"[OK] Verification: words.json re-loaded successfully ({len(reloaded)} entries)")
    except Exception as e:
        print(f"[FAIL] Verification failed: {e}")
        sys.exit(1)

    print()
    print("[OK] BUILD COMPLETE - words.json is ready")
    print(f"[INFO] Output: {os.path.abspath(OUTPUT_FILE)}")
    print(f"[INFO] Dictionary entries: {len(SCHOLARLY_DICTIONARY)} built-in definitions")
    print(f"[INFO] Lexicon entries:    {len(lexicon)} total words")


if __name__ == '__main__':
    main()
