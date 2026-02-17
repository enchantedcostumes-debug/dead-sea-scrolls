/**
 * Word Evolution Modal - Dead Sea Scrolls (Ge'ez/Ethiopic)
 * Priority Loading + IndexedDB Caching
 *
 * Loading Strategy:
 * 1. Check IndexedDB for cached full lexicon (instant)
 * 2. If not cached, load priority words first (~1MB)
 * 3. Background load full lexicon
 * 4. Store in IndexedDB for future visits
 *
 * Ge'ez Fidel System:
 * Each character = base consonant + vowel order (1-7)
 * Orders: 1st (a/ae), 2nd (u), 3rd (i), 4th (a), 5th (e), 6th (schwa/none), 7th (o)
 *
 * Copyright (c) 2026 Tammy L Casey. All rights reserved.
 */

// ============================================================================
// STATE
// ============================================================================

// Detect base path - works whether loaded from root or subdirectory
const SCRIPT_EL = document.querySelector('script[src*="word-modal.js"]');
const BASE_PATH = SCRIPT_EL ? SCRIPT_EL.src.replace(/js\/word-modal\.js.*$/, '') : '../';

let wordData = null;
let geezDefs = null;  // Ge'ez definitions keyed by Ge'ez word
let timelineData = null; // Separate timeline data
let priorityLoaded = false;
let fullLoaded = false;
let defsLoaded = false;
let timelinesLoaded = false;
let loadingStatus = 'idle'; // 'idle', 'priority', 'full', 'cached'

const DB_NAME = 'DeadSeaScrollsDB';
const DB_VERSION = 7;  // v7: Load timelines immediately with words (parallel loading)
const STORE_NAME = 'wordData';

// Ge'ez Fidel vowel orders
const GEEZ_VOWEL_ORDERS = {
    1: { name: '1st order', vowel: '\u00e4', label: 'ae' },   // ae
    2: { name: '2nd order', vowel: 'u', label: 'u' },         // u
    3: { name: '3rd order', vowel: 'i', label: 'i' },         // i
    4: { name: '4th order', vowel: 'a', label: 'a' },         // a
    5: { name: '5th order', vowel: 'e', label: 'e' },         // e (long)
    6: { name: '6th order', vowel: '\u0259', label: 'schwa' },// schwa / no vowel
    7: { name: '7th order', vowel: 'o', label: 'o' }          // o
};

// Ge'ez base consonant rows (1st order forms) with Unicode code points
// Each row starts at a base and increments by 1 for each vowel order
const GEEZ_CONSONANTS = {
    '\u1200': { name: 'Hoy',   translit: 'h',  base: 0x1200 },  // ha row
    '\u1208': { name: 'Lawe',  translit: 'l',  base: 0x1208 },  // la row
    '\u1210': { name: 'Hawt',  translit: 'H',  base: 0x1210 },  // Ha row (pharyngeal)
    '\u1218': { name: 'May',   translit: 'm',  base: 0x1218 },  // ma row
    '\u1220': { name: 'Sewt',  translit: 's',  base: 0x1220 },  // sa row (sharp)
    '\u1228': { name: 'Rees',  translit: 'r',  base: 0x1228 },  // ra row
    '\u1230': { name: 'Sat',   translit: 's',  base: 0x1230 },  // sa row
    '\u1238': { name: 'Shawt', translit: 'sh', base: 0x1238 },  // sha row
    '\u1240': { name: 'Qaf',   translit: 'q',  base: 0x1240 },  // qa row
    '\u1260': { name: 'Bet',   translit: 'b',  base: 0x1260 },  // ba row
    '\u1268': { name: 'Taw',   translit: 't',  base: 0x1268 },  // ta row
    '\u1270': { name: 'Harm',  translit: 'x',  base: 0x1270 },  // xa row
    '\u1278': { name: 'Nahas', translit: 'n',  base: 0x1278 },  // na row (this is actually cha row)
    '\u1280': { name: 'Ayn',   translit: "'",  base: 0x1280 },  // 'a row (pharyngeal)
    '\u1290': { name: 'Nahas', translit: 'n',  base: 0x1290 },  // na row
    '\u1298': { name: 'Nyahas',translit: 'ny', base: 0x1298 },  // nya row
    '\u12A0': { name: 'Alef',  translit: "'",  base: 0x12A0 },  // 'a row (glottal)
    '\u12A8': { name: 'Kaf',   translit: 'k',  base: 0x12A8 },  // ka row
    '\u12C8': { name: 'Wawe',  translit: 'w',  base: 0x12C8 },  // wa row
    '\u12D0': { name: 'Ayin',  translit: "'",  base: 0x12D0 },  // 'a row (voiced pharyngeal)
    '\u12D8': { name: 'Zay',   translit: 'z',  base: 0x12D8 },  // za row
    '\u12E0': { name: 'Zhe',   translit: 'zh', base: 0x12E0 },  // zha row
    '\u12E8': { name: 'Yaman', translit: 'y',  base: 0x12E8 },  // ya row
    '\u12F0': { name: 'Dent',  translit: 'd',  base: 0x12F0 },  // da row
    '\u12F8': { name: 'Dhi',   translit: 'dd', base: 0x12F8 },  // dda row
    '\u1300': { name: 'Jee',   translit: 'j',  base: 0x1300 },  // ja row
    '\u1308': { name: 'Gemel', translit: 'g',  base: 0x1308 },  // ga row
    '\u1320': { name: 'Teyt',  translit: 'T',  base: 0x1320 },  // Ta row (emphatic)
    '\u1328': { name: 'Cheha', translit: 'ch', base: 0x1328 },  // cha row
    '\u1330': { name: 'Pharyngeal T', translit: 'P', base: 0x1330 }, // Pa row
    '\u1338': { name: 'Tsadey',translit: 'ts', base: 0x1338 },  // tsa row
    '\u1340': { name: 'Tsappa',translit: "ts'",base: 0x1340 },  // ts'a row (emphatic)
    '\u1348': { name: 'Af',    translit: 'f',  base: 0x1348 },  // fa row
    '\u1350': { name: 'Psa',   translit: 'p',  base: 0x1350 }   // pa row
};

// ============================================================================
// INDEXEDDB FUNCTIONS
// ============================================================================

function openDatabase() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_NAME, DB_VERSION);

        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);

        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            if (!db.objectStoreNames.contains(STORE_NAME)) {
                db.createObjectStore(STORE_NAME);
            }
        };
    });
}

async function getFromIndexedDB(key) {
    try {
        const db = await openDatabase();
        return new Promise((resolve, reject) => {
            const tx = db.transaction(STORE_NAME, 'readonly');
            const store = tx.objectStore(STORE_NAME);
            const request = store.get(key);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    } catch (e) {
        console.warn('[WARN] IndexedDB not available:', e.message);
        return null;
    }
}

async function saveToIndexedDB(key, value) {
    try {
        const db = await openDatabase();
        return new Promise((resolve, reject) => {
            const tx = db.transaction(STORE_NAME, 'readwrite');
            const store = tx.objectStore(STORE_NAME);
            const request = store.put(value, key);
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    } catch (e) {
        console.warn('[WARN] Could not save to IndexedDB:', e.message);
    }
}

// ============================================================================
// GE'EZ FIDEL CHARACTER ANALYSIS
// ============================================================================

/**
 * Analyze a Ge'ez character to determine its base consonant and vowel order.
 * Ge'ez Fidel characters are organized in rows of 7 (one per vowel order).
 * The code point offset from the row base determines the vowel order.
 */
function analyzeGeezChar(char) {
    const codePoint = char.codePointAt(0);

    // Search through consonant rows to find which row this character belongs to
    for (const [baseChar, info] of Object.entries(GEEZ_CONSONANTS)) {
        const base = info.base;
        const offset = codePoint - base;

        // Each consonant row spans 7 characters (orders 1-7), some have 8 (with labiovelar)
        if (offset >= 0 && offset < 8) {
            const order = offset + 1; // 1-based order
            const vowelInfo = GEEZ_VOWEL_ORDERS[Math.min(order, 7)] || { name: 'labiovelar', vowel: 'wa', label: 'wa' };

            return {
                char: char,
                consonant: info.name,
                translit: info.translit,
                order: Math.min(order, 7),
                orderName: order <= 7 ? GEEZ_VOWEL_ORDERS[order].name : 'labiovelar',
                vowel: order <= 7 ? GEEZ_VOWEL_ORDERS[order].vowel : 'wa',
                fullTranslit: info.translit + (order <= 7 ? GEEZ_VOWEL_ORDERS[order].label : 'wa')
            };
        }
    }

    // Character not found in our consonant table - return basic info
    return {
        char: char,
        consonant: 'Unknown',
        translit: '?',
        order: 0,
        orderName: 'unknown',
        vowel: '',
        fullTranslit: '?'
    };
}

// ============================================================================
// LOADING FUNCTIONS
// ============================================================================

async function loadGeezDefinitions() {
    if (defsLoaded && geezDefs) return geezDefs;

    try {
        const response = await fetch(BASE_PATH + 'data/geez_definitions.json');
        if (response.ok) {
            geezDefs = await response.json();
            defsLoaded = true;
            console.log('[OK] Ge\'ez definitions loaded: ' + Object.keys(geezDefs).length + ' entries');
        }
    } catch (e) {
        console.warn('[WARN] Could not load Ge\'ez definitions:', e.message);
    }
    return geezDefs;
}

async function loadWordData() {
    // Already have full data
    if (fullLoaded && wordData) {
        // Make sure timelines are also loading
        if (!timelinesLoaded) loadTimelinesInBackground();
        return wordData;
    }

    // Check IndexedDB first (instant if cached)
    if (loadingStatus === 'idle') {
        loadingStatus = 'checking';

        // Load cached words and timelines in parallel
        const [cachedWords, cachedTimelines] = await Promise.all([
            getFromIndexedDB('fullLexicon'),
            getFromIndexedDB('timelines')
        ]);

        if (cachedWords && Object.keys(cachedWords).length > 100) {
            wordData = cachedWords;
            fullLoaded = true;
            priorityLoaded = true;
            loadingStatus = 'cached';
            console.log('[OK] Loaded ' + Object.keys(cachedWords).length + ' words from IndexedDB cache');
        }

        if (cachedTimelines && Object.keys(cachedTimelines).length > 100) {
            timelineData = cachedTimelines;
            timelinesLoaded = true;
            console.log('[OK] Loaded ' + Object.keys(cachedTimelines).length + ' timelines from IndexedDB cache');
        }

        if (wordData) {
            // Start background loading for anything not cached
            if (!timelinesLoaded) loadTimelinesInBackground();
            return wordData;
        }
    }

    // Load priority words first (fast)
    if (!priorityLoaded) {
        loadingStatus = 'priority';
        try {
            const response = await fetch(BASE_PATH + 'words-priority.json');
            if (response.ok) {
                const priority = await response.json();
                wordData = priority;
                priorityLoaded = true;
                console.log('[OK] Priority words loaded: ' + Object.keys(priority).length + ' words (modal ready)');

                // Start background load of full lexicon AND timelines
                loadFullLexiconInBackground();
                loadTimelinesInBackground();
            }
        } catch (e) {
            console.warn('[WARN] Priority words failed, loading full lexicon:', e.message);
        }
    }

    // If priority failed, fall back to full load
    if (!wordData) {
        return loadFullLexicon();
    }

    return wordData;
}

async function loadFullLexicon() {
    loadingStatus = 'full';
    updateLoadingIndicator('Loading complete Ge\'ez lexicon...');

    const response = await fetch(BASE_PATH + 'words.json');
    if (!response.ok) {
        throw new Error('Failed to load word data');
    }

    const data = await response.json();
    wordData = data;
    fullLoaded = true;
    loadingStatus = 'cached';

    console.log('[OK] Full lexicon loaded: ' + Object.keys(data).length + ' words');

    // Save to IndexedDB for future visits
    saveToIndexedDB('fullLexicon', data)
        .then(() => console.log('[OK] Lexicon cached in IndexedDB'))
        .catch(e => console.warn('[WARN] IndexedDB save failed:', e.message));

    return data;
}

function loadFullLexiconInBackground() {
    // Don't block - load in background after priority is ready
    setTimeout(async () => {
        if (fullLoaded) return;

        console.log('[INFO] Background loading full lexicon...');
        loadingStatus = 'full';

        try {
            const response = await fetch(BASE_PATH + 'words.json');
            if (response.ok) {
                const data = await response.json();
                wordData = data;
                fullLoaded = true;
                loadingStatus = 'cached';

                console.log('[OK] Full lexicon loaded in background: ' + Object.keys(data).length + ' words');

                // Save to IndexedDB
                saveToIndexedDB('fullLexicon', data)
                    .then(() => console.log('[OK] Lexicon cached in IndexedDB'))
                    .catch(e => console.warn('[WARN] IndexedDB save failed:', e.message));
            }
        } catch (e) {
            console.warn('[WARN] Background load failed:', e.message);
        }

        // Also load timelines in background
        loadTimelinesInBackground();
    }, 2000); // Start after 2 seconds
}

async function loadTimelinesInBackground() {
    if (timelinesLoaded) return;

    // Check IndexedDB first
    const cached = await getFromIndexedDB('timelines');
    if (cached && Object.keys(cached).length > 100) {
        timelineData = cached;
        timelinesLoaded = true;
        console.log('[OK] Loaded ' + Object.keys(cached).length + ' timelines from IndexedDB cache');
        return;
    }

    console.log('[INFO] Background loading timelines...');

    try {
        const response = await fetch(BASE_PATH + 'timelines.json');
        if (response.ok) {
            const data = await response.json();
            timelineData = data;
            timelinesLoaded = true;

            console.log('[OK] Timelines loaded: ' + Object.keys(data).length + ' timelines');

            // Save to IndexedDB
            saveToIndexedDB('timelines', data)
                .then(() => console.log('[OK] Timelines cached in IndexedDB'))
                .catch(e => console.warn('[WARN] Timelines IndexedDB save failed:', e.message));
        }
    } catch (e) {
        console.warn('[WARN] Timelines load failed:', e.message);
    }
}

function getTimelineForWord(geez) {
    // First check if word has embedded timeline
    const word = wordData?.[geez];
    if (word?.timeline && Array.isArray(word.timeline) && word.timeline.length > 0) {
        return word.timeline;
    }

    // Then check separate timelines data
    if (timelineData?.[geez]) {
        return timelineData[geez];
    }

    return null;
}

function updateLoadingIndicator(message) {
    const body = document.querySelector('.word-modal-body');
    if (body) {
        body.innerHTML = `
            <div class="word-modal-loading">
                ${message}<br>
                <small>This only happens once - data is cached for instant access.</small>
            </div>
        `;
    }
}

// ============================================================================
// DEFINITION LOOKUP FUNCTIONS
// ============================================================================

/**
 * Look up definition for a Ge'ez word.
 * Ge'ez does not use the same prefix system as Hebrew,
 * so we do exact match and root-based lookup only.
 */
function lookupDefinition(geez) {
    if (!geezDefs) return null;

    // Try exact match first
    if (geezDefs[geez]) {
        return geezDefs[geez];
    }

    // Try without final vowel variation (Ge'ez words can vary in final form)
    // Check if a 3-consonant root match exists
    if (geez.length > 1) {
        // Try trimming last character (may be a suffix like -t feminine marker)
        const trimmed = geez.substring(0, geez.length - 1);
        if (geezDefs[trimmed]) {
            const def = { ...geezDefs[trimmed] };
            def.hasVariant = true;
            def.variantNote = '(variant form)';
            return def;
        }
    }

    return null;
}

// ============================================================================
// TIMELINE BUILDER
// ============================================================================

function buildTimelineStages(word, definition) {
    // Get timeline from the word data or separate timelines.json
    const geezKey = word.geez;
    const timeline = getTimelineForWord(geezKey);

    if (timeline && Array.isArray(timeline) && timeline.length > 0) {
        // Timeline is an array of stages from words.json
        let stagesHTML = '';
        for (let i = 0; i < timeline.length; i++) {
            const stage = timeline[i];
            stagesHTML += `
                <div class="word-timeline-stage">
                    <div class="word-timeline-num">${i + 1}</div>
                    <div class="word-timeline-content">
                        <strong>${stage.period || 'Unknown Period'}</strong>
                        <span class="word-timeline-period">${stage.form ? '' : ''}</span><br>
                        ${stage.form ? `<span class="word-timeline-geez">${stage.form}</span><br>` : ''}
                        ${stage.note ? `<em>${stage.note}</em>` : ''}
                    </div>
                </div>
            `;
        }
        return stagesHTML;
    }

    // Default timeline for Ge'ez words when no detailed timeline exists
    const root = word.root || geezKey;
    const transliteration = word.transliteration || '';

    return `
        <div class="word-timeline-stage">
            <div class="word-timeline-num">1</div>
            <div class="word-timeline-content">
                <strong>Proto-Semitic Root</strong>
                <span class="word-timeline-period">(Pre-1000 BCE)</span><br>
                <em>Common Semitic ancestor root</em>
            </div>
        </div>
        <div class="word-timeline-stage">
            <div class="word-timeline-num">2</div>
            <div class="word-timeline-content">
                <strong>South Semitic</strong>
                <span class="word-timeline-period">(~1000 BCE)</span><br>
                <em>South Arabian / Proto-Ethiopic branch</em>
            </div>
        </div>
        <div class="word-timeline-stage">
            <div class="word-timeline-num">3</div>
            <div class="word-timeline-content">
                <strong>Classical Ge'ez</strong>
                <span class="word-timeline-period">(~100 BCE - 700 CE)</span><br>
                <span class="word-timeline-geez">${root}</span>
                ${transliteration ? ` (${transliteration})` : ''}<br>
                <em>${definition || 'Aksumite literary language'}</em>
            </div>
        </div>
        <div class="word-timeline-stage">
            <div class="word-timeline-num">4</div>
            <div class="word-timeline-content">
                <strong>Ethiopic Liturgical</strong>
                <span class="word-timeline-period">(700 CE - present)</span><br>
                <em>Preserved in Ethiopian Orthodox Church tradition</em>
            </div>
        </div>
        <div class="word-timeline-stage">
            <div class="word-timeline-num">5</div>
            <div class="word-timeline-content">
                <strong>Modern Descendants</strong>
                <span class="word-timeline-period">(Amharic, Tigrinya, Tigre)</span><br>
                <em>Living descendant languages preserve Ge'ez roots</em>
            </div>
        </div>
    `;
}

// ============================================================================
// MODAL FUNCTIONS
// ============================================================================

async function showWordEvolution(geez) {
    const modal = document.getElementById('wordModal');
    if (!modal) {
        console.error('[FAIL] Modal element not found');
        return;
    }

    const body = modal.querySelector('.word-modal-body');

    // Show modal with loading
    modal.classList.add('show');
    document.body.style.overflow = 'hidden';

    // Check if we already have the word
    if (wordData && wordData[geez]) {
        body.innerHTML = buildWordHTML(wordData[geez]);
        return;
    }

    // Show loading
    if (loadingStatus === 'cached') {
        body.innerHTML = '<div class="word-modal-loading">Looking up word...</div>';
    } else if (loadingStatus === 'priority') {
        body.innerHTML = '<div class="word-modal-loading">Loading priority words...</div>';
    } else {
        body.innerHTML = '<div class="word-modal-loading">Loading word database...</div>';
    }

    // Load data
    try {
        const data = await loadWordData();
        const word = data[geez];

        if (!word) {
            // Word not in priority - try waiting for full load
            if (!fullLoaded) {
                body.innerHTML = `
                    <div class="word-modal-loading">
                        Loading complete lexicon for: <span lang="gez">${geez}</span><br>
                        <small>This word is not in the priority set. Loading full database...</small>
                    </div>
                `;

                // Wait for full lexicon
                await loadFullLexicon();
                const fullWord = wordData[geez];
                if (fullWord) {
                    body.innerHTML = buildWordHTML(fullWord);
                    return;
                }
            }

            body.innerHTML = `
                <div class="word-modal-loading">
                    Word not found: <span lang="gez">${geez}</span><br>
                    <small>This word may not be in our database yet.</small>
                </div>
            `;
            return;
        }

        body.innerHTML = buildWordHTML(word);
    } catch (error) {
        body.innerHTML = `
            <div class="word-modal-loading">
                Error loading word data.<br>
                <small>${error.message}</small>
            </div>
        `;
    }
}

function buildWordHTML(word) {
    // Look up definition from Ge'ez definitions database (secondary source)
    const def = lookupDefinition(word.geez);

    // Primary: Use data from words.json
    // Secondary: Fall back to geez_definitions.json lookup
    const translit = word.transliteration || def?.transliteration || '';
    const definition = word.definition || def?.definition || '';
    const root = word.root || def?.root || '';
    const source = word.source || def?.source || '';
    const variantNote = def?.variantNote || '';

    // Enriched fields from Leslau dictionary / classification
    const englishDef = word.english_definition || '';
    const pos = word.part_of_speech || '';
    const domain = word.semantic_domain || '';
    const enochUsage = word.enoch_usage || '';
    const cognates = word.cognates_english || '';

    // Build letter table rows from word data or auto-analysis
    let letterRows = '';
    const letters = word.letters || def?.letters || [];

    if (letters && letters.length > 0) {
        // Use provided letter data from words.json
        for (const letter of letters) {
            const char = letter.char || '';
            const name = letter.name || '';
            const value = letter.value || '';
            const meaning = letter.meaning || '';

            // Auto-analyze the Fidel character for consonant/order info
            const analysis = char ? analyzeGeezChar(char) : null;
            const consonantName = analysis ? analysis.consonant : '';
            const orderInfo = analysis ? analysis.orderName : '';

            letterRows += `
                <tr>
                    <td class="geez-letter-cell" lang="gez">${char}</td>
                    <td>${name}</td>
                    <td>${consonantName}</td>
                    <td>${orderInfo}</td>
                    <td>${value}</td>
                    <td>${meaning}</td>
                </tr>
            `;
        }
    } else if (word.geez) {
        // Auto-analyze each character in the Ge'ez word
        const chars = [...word.geez];
        for (const char of chars) {
            const analysis = analyzeGeezChar(char);
            letterRows += `
                <tr>
                    <td class="geez-letter-cell" lang="gez">${char}</td>
                    <td>${analysis.fullTranslit}</td>
                    <td>${analysis.consonant} (${analysis.translit})</td>
                    <td>${analysis.orderName}</td>
                    <td>-</td>
                    <td>-</td>
                </tr>
            `;
        }
    }

    // Pictographic / root meaning
    const pictographic = word.pictographic || def?.pictographic || '';

    // POS label mapping
    const posLabels = {
        'n': 'Noun', 'v': 'Verb', 'adj': 'Adjective', 'adv': 'Adverb',
        'prep': 'Preposition', 'conj': 'Conjunction', 'pron': 'Pronoun',
        'part': 'Particle', 'prop': 'Proper Noun', 'compound': 'Compound',
        'interj': 'Interjection'
    };
    const posLabel = posLabels[pos] || pos;

    // Domain badge color mapping
    const domainColors = {
        'divine': '#8B5CF6', 'angelic': '#6366F1', 'nature': '#10B981',
        'person': '#F59E0B', 'action': '#EF4444', 'temporal': '#3B82F6',
        'abstract': '#8B5CF6', 'grammar': '#6B7280'
    };
    const domainColor = domainColors[domain] || '#6B7280';

    return `
        <div class="word-header-section">
            <div class="word-language-badge">Ge'ez (Ethiopic)</div>
            <div class="word-geez-large" lang="gez">${word.geez}</div>
            ${translit ? `<div class="word-translit">(${translit}) ${variantNote}</div>` : ''}
            ${root ? `<div class="word-root"><strong>Root:</strong> <span lang="gez">${root}</span></div>` : ''}
            ${definition ? `<div class="word-definition"><strong>Meaning:</strong> ${definition}</div>` : ''}
            ${(pos || domain) ? `
                <div class="word-badges">
                    ${posLabel ? `<span class="word-pos-badge">${posLabel}</span>` : ''}
                    ${domain && domain !== 'unclassified' ? `<span class="word-domain-badge" style="background:${domainColor}">${domain}</span>` : ''}
                </div>
            ` : ''}
        </div>

        ${englishDef ? `
            <div class="word-english-section">
                <h3 class="word-section-header">English Definition</h3>
                <div class="word-english-def">${englishDef}</div>
                ${enochUsage ? `<div class="word-enoch-usage"><strong>In 1 Enoch:</strong> ${enochUsage}</div>` : ''}
                ${cognates ? `<div class="word-cognates"><strong>English cognates:</strong> ${cognates}</div>` : ''}
            </div>
        ` : ''}

        <div class="word-stats-row">
            <div class="word-stat-box">
                <div class="word-stat-value">${word.gematria || def?.gematria || 'N/A'}</div>
                <div class="word-stat-label">Gematria</div>
            </div>
            <div class="word-stat-box">
                <div class="word-stat-value">${word.digital_root || def?.digital_root || 'N/A'}</div>
                <div class="word-stat-label">Digital Root</div>
            </div>
            <div class="word-stat-box">
                <div class="word-stat-value">${word.frequency || def?.frequency || 'N/A'}</div>
                <div class="word-stat-label">Occurrences</div>
            </div>
            <div class="word-stat-box">
                <div class="word-stat-value">${word.first_occurrence || def?.first_occurrence || 'N/A'}</div>
                <div class="word-stat-label">First Occurrence</div>
            </div>
        </div>

        ${pictographic ? `
            <h3 class="word-section-header">Root Meaning</h3>
            <div class="word-pictographic">${pictographic}</div>
        ` : ''}

        <h3 class="word-section-header">Fidel Character Analysis</h3>
        <table class="word-letter-table">
            <tr>
                <th>Ge'ez</th>
                <th>Name</th>
                <th>Consonant</th>
                <th>Vowel Order</th>
                <th>Value</th>
                <th>Meaning</th>
            </tr>
            ${letterRows}
        </table>

        <h3 class="word-section-header">Word Evolution Timeline</h3>
        <div class="word-timeline">
            ${buildTimelineStages(word, definition)}
        </div>

        <div class="word-sources">
            <strong>Sources:</strong><br>
            ${source ? `- ${source}<br>` : ''}
            - Dillmann, Lexicon Linguae Aethiopicae (1865)<br>
            - Leslau, Comparative Dictionary of Ge'ez (1987)<br>
            - Ethiopian Orthodox Tewahedo Church liturgical tradition<br>
            - Dead Sea Scrolls comparative analysis
        </div>
    `;
}

function closeWordModal() {
    const modal = document.getElementById('wordModal');
    if (modal) {
        modal.classList.remove('show');
        document.body.style.overflow = '';
    }
}

// ============================================================================
// INITIALIZATION
// ============================================================================

function initWordModal() {
    // Create modal if it doesn't exist
    if (!document.getElementById('wordModal')) {
        const modalHTML = `
            <div id="wordModal" class="word-modal">
                <div class="word-modal-content">
                    <button class="word-modal-close" onclick="closeWordModal()">&times;</button>
                    <div class="word-modal-body"></div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }

    // Add Ge'ez font styles if not already present
    if (!document.getElementById('geezFontStyles')) {
        const styleEl = document.createElement('style');
        styleEl.id = 'geezFontStyles';
        styleEl.textContent = `
            .word-geez-large,
            .word-timeline-geez,
            .geez-letter-cell,
            [lang="gez"] {
                font-family: 'Nyala', 'Abyssinica SIL', 'Noto Sans Ethiopic', 'Ethiopic', sans-serif;
            }
            .word-geez-large {
                font-size: 3rem;
                line-height: 1.4;
                text-align: center;
                margin: 0.5rem 0;
            }
            .word-timeline-geez {
                font-size: 1.3rem;
            }
            .geez-letter-cell {
                font-size: 1.5rem;
                text-align: center;
            }
            .word-root span[lang="gez"] {
                font-size: 1.2rem;
            }
        `;
        document.head.appendChild(styleEl);
    }

    // Close on overlay click
    const modal = document.getElementById('wordModal');
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            closeWordModal();
        }
    });

    // Close on Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeWordModal();
        }
    });

    // Load Ge'ez definitions
    loadGeezDefinitions().catch(() => {});

    // Start loading immediately (check IndexedDB, then priority, then background full)
    loadWordData().catch(() => {});
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initWordModal);
} else {
    initWordModal();
}
