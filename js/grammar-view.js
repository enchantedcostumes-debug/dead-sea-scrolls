/**
 * Grammar View - Dead Sea Scrolls
 * Color-codes words by part of speech (POS) for grammatical analysis.
 *
 * Uses POS data from words.json loaded by word-modal.js.
 * Each word is highlighted with its grammatical category color.
 *
 * Copyright (c) 2026 Tammy L Casey. All rights reserved.
 */

// ============================================================================
// STATE
// ============================================================================

let grammarMode = false;

// ============================================================================
// POS COLOR MAPPING
// ============================================================================

const POS_COLORS = {
    'n':        { color: '#5bb8f0', label: 'Noun',        bg: 'rgba(91,184,240,0.15)' },
    'v':        { color: '#f06060', label: 'Verb',        bg: 'rgba(240,96,96,0.15)' },
    'adj':      { color: '#60d060', label: 'Adjective',   bg: 'rgba(96,208,96,0.15)' },
    'adv':      { color: '#d0a040', label: 'Adverb',      bg: 'rgba(208,160,64,0.15)' },
    'prep':     { color: '#c080e0', label: 'Preposition', bg: 'rgba(192,128,224,0.15)' },
    'conj':     { color: '#e0a060', label: 'Conjunction', bg: 'rgba(224,160,96,0.15)' },
    'pron':     { color: '#60c0c0', label: 'Pronoun',     bg: 'rgba(96,192,192,0.15)' },
    'prop':     { color: '#f0c040', label: 'Proper Noun', bg: 'rgba(240,192,64,0.15)' },
    'part':     { color: '#a0a0a0', label: 'Particle',    bg: 'rgba(160,160,160,0.15)' },
    'num':      { color: '#e070b0', label: 'Number',      bg: 'rgba(224,112,176,0.15)' },
    'compound': { color: '#80b0d0', label: 'Compound',    bg: 'rgba(128,176,208,0.15)' },
};

// ============================================================================
// GRAMMAR VIEW TOGGLE
// ============================================================================

function toggleGrammar() {
    grammarMode = !grammarMode;
    const btn = document.getElementById('grammar-toggle');
    if (btn) {
        btn.textContent = grammarMode ? 'Normal View' : 'Grammar View';
        btn.classList.toggle('active', grammarMode);
    }

    // Show/hide legend
    const legend = document.getElementById('grammar-legend');
    if (legend) {
        legend.style.display = grammarMode ? 'flex' : 'none';
    }

    const verseBlocks = document.querySelectorAll('.verse-block');
    verseBlocks.forEach(block => {
        if (grammarMode) {
            enableGrammar(block);
        } else {
            disableGrammar(block);
        }
    });
}


function getWordPOS(geezWord) {
    if (typeof wordData !== 'undefined' && wordData && wordData[geezWord]) {
        return wordData[geezWord].part_of_speech || '';
    }
    if (typeof geezDefs !== 'undefined' && geezDefs && geezDefs[geezWord]) {
        return geezDefs[geezWord].part_of_speech || '';
    }
    return '';
}


function enableGrammar(block) {
    const textDiv = block.querySelector('.original-text.geez');
    if (!textDiv) return;

    const words = textDiv.querySelectorAll('.word');
    words.forEach(wordSpan => {
        const geez = wordSpan.textContent.trim();
        const pos = getWordPOS(geez);
        const posInfo = POS_COLORS[pos];

        if (posInfo) {
            wordSpan.style.color = posInfo.color;
            wordSpan.style.backgroundColor = posInfo.bg;
            wordSpan.style.borderBottom = '2px solid ' + posInfo.color;
            wordSpan.title = posInfo.label + ': ' + geez;
        } else {
            // Unknown POS - dim slightly
            wordSpan.style.color = '#706090';
            wordSpan.title = 'Unknown POS: ' + geez;
        }
        wordSpan.dataset.grammarApplied = 'true';
    });
}


function disableGrammar(block) {
    const textDiv = block.querySelector('.original-text.geez');
    if (!textDiv) return;

    const words = textDiv.querySelectorAll('.word');
    words.forEach(wordSpan => {
        if (wordSpan.dataset.grammarApplied === 'true') {
            wordSpan.style.color = '';
            wordSpan.style.backgroundColor = '';
            wordSpan.style.borderBottom = '';
            wordSpan.title = '';
            wordSpan.dataset.grammarApplied = 'false';
        }
    });
}


// ============================================================================
// LEGEND - Build on page load
// ============================================================================

function buildGrammarLegend() {
    const toolbar = document.querySelector('.view-toolbar');
    if (!toolbar) return;

    const legend = document.createElement('div');
    legend.id = 'grammar-legend';
    legend.className = 'grammar-legend';
    legend.style.display = 'none';

    for (const [pos, info] of Object.entries(POS_COLORS)) {
        const item = document.createElement('span');
        item.className = 'grammar-legend-item';
        item.innerHTML = '<span class="grammar-legend-swatch" style="background:' +
            info.color + '"></span>' + info.label;
        legend.appendChild(item);
    }

    toolbar.parentNode.insertBefore(legend, toolbar.nextSibling);
}

// Build legend when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', buildGrammarLegend);
} else {
    buildGrammarLegend();
}
