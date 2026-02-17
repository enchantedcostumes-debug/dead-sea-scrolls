/**
 * Search - Dead Sea Scrolls
 * Full-text search across all 36 chapters of 1 Enoch.
 *
 * Searches Ge'ez words, English definitions, transliterations,
 * roots, and verse translations. Results link directly to
 * the matching chapter and verse.
 *
 * Copyright (c) 2026 Tammy L Casey. All rights reserved.
 */

// ============================================================================
// STATE
// ============================================================================

let searchIndex = null;
let searchModal = null;
let searchOpen = false;

// ============================================================================
// SEARCH INDEX LOADING
// ============================================================================

/**
 * Load search index (words.json + search_index.json).
 * Uses cached wordData from word-modal.js if available.
 */
async function loadSearchIndex() {
    if (searchIndex) return searchIndex;

    try {
        // Determine base path (works from chapter pages and index)
        const isChapter = window.location.pathname.includes('/1_enoch/');
        const base = isChapter ? '..' : '.';

        // Load search index (verse-to-word mapping)
        const indexResp = await fetch(base + '/data/search_index.json');
        const indexData = await indexResp.json();

        // Load word data (definitions, transliterations)
        let words = {};
        if (typeof wordData !== 'undefined' && wordData) {
            words = wordData;
        } else {
            const wordsResp = await fetch(base + '/words.json');
            words = await wordsResp.json();
        }

        searchIndex = {
            verses: indexData.verses,
            words: words,
            stats: {
                verses: indexData.verse_count,
                words: indexData.word_count,
                chapters: indexData.chapter_count,
            }
        };

        return searchIndex;
    } catch (err) {
        console.error('Search index load failed:', err);
        return null;
    }
}


// ============================================================================
// SEARCH MODAL
// ============================================================================

function buildSearchModal() {
    if (document.getElementById('search-modal')) return;

    const modal = document.createElement('div');
    modal.id = 'search-modal';
    modal.className = 'search-modal';
    modal.innerHTML =
        '<div class="search-modal-content">' +
            '<div class="search-header">' +
                '<h2 class="search-title">Search 1 Enoch</h2>' +
                '<button class="search-close" onclick="closeSearch()">&times;</button>' +
            '</div>' +
            '<div class="search-input-wrap">' +
                '<input type="text" id="search-input" class="search-input" ' +
                    'placeholder="Search Ge\'ez, English, transliteration, root..." ' +
                    'autocomplete="off" spellcheck="false">' +
                '<div class="search-hint">Search across all 36 chapters - ' +
                    'Ge\'ez words, definitions, transliterations, verse text</div>' +
            '</div>' +
            '<div id="search-results" class="search-results"></div>' +
        '</div>';

    document.body.appendChild(modal);
    searchModal = modal;

    // Bind input event
    const input = document.getElementById('search-input');
    let debounce = null;
    input.addEventListener('input', function() {
        clearTimeout(debounce);
        debounce = setTimeout(function() {
            performSearch(input.value.trim());
        }, 200);
    });

    // Close on backdrop click
    modal.addEventListener('click', function(e) {
        if (e.target === modal) closeSearch();
    });

    // Close on Escape
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && searchOpen) closeSearch();
    });
}


function openSearch() {
    buildSearchModal();
    searchModal.style.display = 'flex';
    searchOpen = true;
    document.body.style.overflow = 'hidden';

    // Focus input
    setTimeout(function() {
        var input = document.getElementById('search-input');
        if (input) {
            input.value = '';
            input.focus();
        }
        document.getElementById('search-results').innerHTML = '';
    }, 100);

    // Preload index
    loadSearchIndex();
}


function closeSearch() {
    if (searchModal) {
        searchModal.style.display = 'none';
    }
    searchOpen = false;
    document.body.style.overflow = '';
}


// ============================================================================
// SEARCH ENGINE
// ============================================================================

async function performSearch(query) {
    const resultsDiv = document.getElementById('search-results');
    if (!query || query.length < 2) {
        resultsDiv.innerHTML = '<div class="search-empty">Type at least 2 characters to search</div>';
        return;
    }

    const index = await loadSearchIndex();
    if (!index) {
        resultsDiv.innerHTML = '<div class="search-empty">Search index not available</div>';
        return;
    }

    const results = [];
    const q = query.toLowerCase();
    const isGeez = /[\u1200-\u137F]/.test(query);  // Detect Ge'ez input

    // 1. Search word definitions and transliterations
    const wordMatches = [];
    for (const [geez, data] of Object.entries(index.words)) {
        let matched = false;
        let matchType = '';

        if (isGeez && geez.includes(query)) {
            matched = true;
            matchType = 'Ge\'ez match';
        } else if (!isGeez) {
            const def = (data.definition || '').toLowerCase();
            const engDef = (data.english_definition || '').toLowerCase();
            const trans = (data.transliteration || '').toLowerCase();
            const root = (data.root || '').toLowerCase();

            if (def.includes(q)) {
                matched = true;
                matchType = 'Definition';
            } else if (engDef.includes(q)) {
                matched = true;
                matchType = 'Modern definition';
            } else if (trans.includes(q)) {
                matched = true;
                matchType = 'Transliteration';
            } else if (root.includes(q)) {
                matched = true;
                matchType = 'Root';
            }
        }

        if (matched) {
            wordMatches.push({
                geez: geez,
                data: data,
                matchType: matchType,
            });
        }
    }

    // 2. Search verse translations (English text)
    const verseMatches = [];
    if (!isGeez) {
        for (const verse of index.verses) {
            if (verse.english.toLowerCase().includes(q)) {
                verseMatches.push(verse);
            }
        }
    }

    // 3. Search by gematria value (numeric)
    const gematriaMatches = [];
    if (/^\d+$/.test(query)) {
        const num = parseInt(query);
        for (const [geez, data] of Object.entries(index.words)) {
            if (data.gematria === num) {
                gematriaMatches.push({ geez: geez, data: data });
            }
        }
    }

    // Build results HTML
    let html = '';
    const isChapter = window.location.pathname.includes('/1_enoch/');
    const chapterBase = isChapter ? '' : '1_enoch/';

    // Word matches
    if (wordMatches.length > 0) {
        html += '<div class="search-section-label">Words (' + wordMatches.length + ')</div>';
        const shown = wordMatches.slice(0, 50);
        for (const wm of shown) {
            const d = wm.data;
            const def = d.definition || d.english_definition || '';
            const trans = d.transliteration || '';
            const occ = d.first_occurrence || '';
            const freq = d.frequency || 0;

            // Find all verse locations for this word
            const locations = [];
            for (const verse of index.verses) {
                if (verse.words.includes(wm.geez)) {
                    locations.push(verse.ref);
                }
            }

            html += '<div class="search-result-item">' +
                '<div class="search-result-word">' +
                    '<span class="search-geez">' + wm.geez + '</span>' +
                    '<span class="search-trans">' + trans + '</span>' +
                    '<span class="search-match-type">' + wm.matchType + '</span>' +
                '</div>' +
                '<div class="search-result-def">' + escapeHtml(def) + '</div>' +
                '<div class="search-result-locations">';

            if (locations.length > 0) {
                for (const loc of locations) {
                    const ch = loc.split(':')[0];
                    html += '<a href="' + chapterBase + ch + '.html#v' + loc.replace(':', '-') +
                        '" class="search-verse-link">' + loc + '</a>';
                }
            }
            html += '</div></div>';
        }
        if (wordMatches.length > 50) {
            html += '<div class="search-more">... and ' +
                (wordMatches.length - 50) + ' more word matches</div>';
        }
    }

    // Verse matches
    if (verseMatches.length > 0) {
        html += '<div class="search-section-label">Verses (' + verseMatches.length + ')</div>';
        const shown = verseMatches.slice(0, 30);
        for (const vm of shown) {
            const ch = vm.ref.split(':')[0];
            const highlighted = highlightMatch(escapeHtml(vm.english), q);
            html += '<div class="search-result-item">' +
                '<a href="' + chapterBase + ch + '.html#v' + vm.ref.replace(':', '-') +
                '" class="search-verse-ref">' + vm.ref + '</a>' +
                '<div class="search-verse-text">' + highlighted + '</div>' +
            '</div>';
        }
        if (verseMatches.length > 30) {
            html += '<div class="search-more">... and ' +
                (verseMatches.length - 30) + ' more verse matches</div>';
        }
    }

    // Gematria matches
    if (gematriaMatches.length > 0) {
        html += '<div class="search-section-label">Gematria = ' + query +
            ' (' + gematriaMatches.length + ')</div>';
        for (const gm of gematriaMatches) {
            const def = gm.data.definition || gm.data.english_definition || '';
            html += '<div class="search-result-item">' +
                '<span class="search-geez">' + gm.geez + '</span> ' +
                '<span class="search-trans">' + (gm.data.transliteration || '') + '</span> ' +
                '<span class="search-gematria-val">G: ' + gm.data.gematria + '</span>' +
                '<div class="search-result-def">' + escapeHtml(def) + '</div>' +
            '</div>';
        }
    }

    // No results
    if (wordMatches.length === 0 && verseMatches.length === 0 && gematriaMatches.length === 0) {
        html = '<div class="search-empty">No results for "' + escapeHtml(query) + '"</div>';
    }

    // Summary
    const total = wordMatches.length + verseMatches.length + gematriaMatches.length;
    if (total > 0) {
        html = '<div class="search-summary">' + total + ' result' +
            (total !== 1 ? 's' : '') + ' found</div>' + html;
    }

    resultsDiv.innerHTML = html;
}


// ============================================================================
// UTILITIES
// ============================================================================

function escapeHtml(text) {
    var div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}


function highlightMatch(text, query) {
    if (!query) return text;
    var regex = new RegExp('(' + query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'gi');
    return text.replace(regex, '<mark class="search-highlight">$1</mark>');
}


// ============================================================================
// KEYBOARD SHORTCUT
// ============================================================================

document.addEventListener('keydown', function(e) {
    // Ctrl+F or Cmd+F to open search (only if not in an input)
    if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
        if (document.activeElement &&
            (document.activeElement.tagName === 'INPUT' ||
             document.activeElement.tagName === 'TEXTAREA')) {
            return;  // Don't override native find in inputs
        }
        e.preventDefault();
        openSearch();
    }
});
