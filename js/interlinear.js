/**
 * Interlinear View Toggle - Dead Sea Scrolls
 * Shows word-by-word: Ge'ez / transliteration / English gloss
 *
 * Uses word data already loaded by word-modal.js
 * Toggle between normal text flow and interlinear word-by-word view.
 *
 * Copyright (c) 2026 Tammy L Casey. All rights reserved.
 */

// ============================================================================
// STATE
// ============================================================================

let interlinearMode = false;

// ============================================================================
// TRANSLITERATION ENGINE
// ============================================================================

// Full Ge'ez transliteration table
// Each consonant base (first order) maps to its transliteration
// Vowel order (1-7) adds: a, u, i, a, e, (none), o
const TRANSLIT_BASES = {};

// Build from GEEZ_CONSONANTS if available (from word-modal.js)
function buildTranslitTable() {
    // Known Ge'ez consonant rows with standard academic transliteration
    const rows = [
        [0x1200, 'h'],   // hoy
        [0x1208, 'l'],   // lawe
        [0x1210, 'H'],   // Hawt (pharyngeal h)
        [0x1218, 'm'],   // may
        [0x1220, 's\''], // sewt (sharp s)
        [0x1228, 'r'],   // rees
        [0x1230, 's'],   // sat
        [0x1238, 'sh'],  // shawt
        [0x1240, 'q'],   // qaf
        [0x1248, 'qw'],  // qwa (labiovelar)
        [0x1250, 'b'],   // bet (some list separately)
        [0x1258, 'bw'],  // bwa
        [0x1260, 'b'],   // bet
        [0x1268, 'v'],   // taw variant
        [0x1270, 't'],   // taw
        [0x1278, 'ch'],  // cha
        [0x1280, 'kh'],  // pharyngeal
        [0x1288, 'khw'], // pharyngeal labiovelar
        [0x1290, 'n'],   // nahas
        [0x1298, 'ny'],  // nyahas
        [0x12A0, '\''],  // alef (glottal)
        [0x12A8, 'k'],   // kaf
        [0x12B0, 'kw'],  // kwa
        [0x12B8, 'kx'],  // kxa
        [0x12C0, 'kx'],  // kxa variant
        [0x12C8, 'w'],   // wawe
        [0x12D0, '`'],   // ayin (voiced pharyngeal)
        [0x12D8, 'z'],   // zay
        [0x12E0, 'zh'],  // zhe
        [0x12E8, 'y'],   // yaman
        [0x12F0, 'd'],   // dent
        [0x12F8, 'dd'],  // dda
        [0x1300, 'j'],   // jee
        [0x1308, 'g'],   // gemel
        [0x1310, 'gw'],  // gwa
        [0x1318, 'ggw'], // ggwa
        [0x1320, 'T'],   // Teyt (emphatic t)
        [0x1328, 'P'],   // emphatic p
        [0x1330, 'ts'],  // tsa
        [0x1338, 'ts\''],// ts' (another emphatic)
        [0x1340, 'f'],   // fa
        [0x1348, 'p'],   // pa
    ];

    const vowels = ['a', 'u', 'i', 'a', 'e', '', 'o'];

    for (const [base, cons] of rows) {
        for (let v = 0; v < 7; v++) {
            TRANSLIT_BASES[base + v] = cons + vowels[v];
        }
        // 8th form (labialized) - add 'wa'
        TRANSLIT_BASES[base + 7] = cons + 'wa';
    }
}

buildTranslitTable();


function transliterate(geezWord) {
    let result = '';
    for (const ch of geezWord) {
        const cp = ch.codePointAt(0);
        if (TRANSLIT_BASES[cp]) {
            result += TRANSLIT_BASES[cp];
        } else if (cp >= 0x1200 && cp <= 0x137F) {
            // Unknown Ge'ez char - use placeholder
            result += '?';
        } else {
            result += ch; // Non-Ge'ez char (space, punct)
        }
    }
    return result;
}


function getWordGloss(geezWord) {
    // Try the loaded word data from word-modal.js
    if (typeof geezDefs !== 'undefined' && geezDefs && geezDefs[geezWord]) {
        const def = geezDefs[geezWord].definition || geezDefs[geezWord].english || '';
        // Return first few words of the definition as a gloss
        return truncateGloss(def);
    }
    if (typeof wordData !== 'undefined' && wordData && wordData[geezWord]) {
        const wd = wordData[geezWord];
        const def = wd.definition || wd.english || '';
        return truncateGloss(def);
    }
    return '---';
}


function truncateGloss(def) {
    if (!def) return '---';
    // Strip prefix markers like "and + ", "from + " etc.
    let clean = def.replace(/^(and \+ |from \+ |in\/by \+ |for\/to \+ |of\/which \+ |not \+ )+/g, '');
    // Take first meaningful phrase (before comma or semicolon)
    clean = clean.split(/[,;]/)[0].trim();
    // Limit length
    if (clean.length > 25) {
        clean = clean.substring(0, 22) + '...';
    }
    return clean || '---';
}


function getWordTranslit(geezWord) {
    // Check if word-modal.js has transliteration data
    if (typeof geezDefs !== 'undefined' && geezDefs && geezDefs[geezWord]) {
        const translit = geezDefs[geezWord].transliteration;
        if (translit) return translit;
    }
    if (typeof wordData !== 'undefined' && wordData && wordData[geezWord]) {
        const translit = wordData[geezWord].transliteration;
        if (translit) return translit;
    }
    // Fall back to algorithmic transliteration
    return transliterate(geezWord);
}


// ============================================================================
// INTERLINEAR TOGGLE
// ============================================================================

function toggleInterlinear() {
    interlinearMode = !interlinearMode;
    const btn = document.getElementById('interlinear-toggle');
    if (btn) {
        btn.textContent = interlinearMode ? 'Normal View' : 'Interlinear View';
        btn.classList.toggle('active', interlinearMode);
    }

    const verseBlocks = document.querySelectorAll('.verse-block');
    verseBlocks.forEach(block => {
        if (interlinearMode) {
            enableInterlinear(block);
        } else {
            disableInterlinear(block);
        }
    });
}


function enableInterlinear(block) {
    const textDiv = block.querySelector('.original-text.geez');
    if (!textDiv || textDiv.dataset.interlinearApplied === 'true') return;

    // Save original HTML
    textDiv.dataset.originalHtml = textDiv.innerHTML;
    textDiv.dataset.interlinearApplied = 'true';

    // Get all word spans
    const words = textDiv.querySelectorAll('.word');
    if (words.length === 0) return;

    // Build interlinear HTML
    let interlinearHtml = '<div class="interlinear-line">';

    words.forEach(wordSpan => {
        const geez = wordSpan.textContent.trim();
        const onclickVal = wordSpan.getAttribute('onclick') || '';
        const translit = getWordTranslit(geez);
        const gloss = getWordGloss(geez);

        interlinearHtml += `
            <div class="interlinear-word" onclick="${onclickVal}">
                <span class="il-geez" lang="gez" translate="no">${geez}</span>
                <span class="il-translit">${translit}</span>
                <span class="il-gloss">${gloss}</span>
            </div>`;
    });

    interlinearHtml += '</div>';
    textDiv.innerHTML = interlinearHtml;
    textDiv.classList.add('interlinear-active');
}


function disableInterlinear(block) {
    const textDiv = block.querySelector('.original-text.geez');
    if (!textDiv || textDiv.dataset.interlinearApplied !== 'true') return;

    // Restore original HTML
    if (textDiv.dataset.originalHtml) {
        textDiv.innerHTML = textDiv.dataset.originalHtml;
    }
    textDiv.dataset.interlinearApplied = 'false';
    textDiv.classList.remove('interlinear-active');
}
