/**
 * Parallel Translation View - Dead Sea Scrolls
 * Side-by-side: Ge'ez original | Charles 1917 English
 *
 * Rearranges verse blocks into two-column parallel layout
 * for easy comparison of original text with English translation.
 *
 * English text: R.H. Charles, "The Book of Enoch" (1917)
 *
 * Copyright (c) 2026 Tammy L Casey. All rights reserved.
 */

// ============================================================================
// STATE
// ============================================================================

let parallelMode = false;

// ============================================================================
// PARALLEL VIEW TOGGLE
// ============================================================================

function toggleParallel() {
    parallelMode = !parallelMode;
    const btn = document.getElementById('parallel-toggle');
    if (btn) {
        btn.textContent = parallelMode ? 'Normal View' : 'Parallel View';
        btn.classList.toggle('active', parallelMode);
    }

    // If interlinear mode is on, turn it off first
    if (parallelMode && typeof interlinearMode !== 'undefined' && interlinearMode) {
        toggleInterlinear();
    }

    // Update interlinear button state
    const ilBtn = document.getElementById('interlinear-toggle');
    if (ilBtn) {
        ilBtn.disabled = parallelMode;
        ilBtn.style.opacity = parallelMode ? '0.4' : '1';
    }

    const verseBlocks = document.querySelectorAll('.verse-block');
    verseBlocks.forEach(block => {
        if (parallelMode) {
            enableParallel(block);
        } else {
            disableParallel(block);
        }
    });
}


function enableParallel(block) {
    if (block.dataset.parallelApplied === 'true') return;

    const textDiv = block.querySelector('.original-text.geez');
    const transDiv = block.querySelector('.translation');
    if (!textDiv || !transDiv) return;

    // Save original state
    block.dataset.parallelApplied = 'true';
    block.dataset.originalClass = block.className;

    // Get the verse ref for labeling
    const verseRef = block.querySelector('.verse-ref');

    // Build parallel layout
    // Wrap original-text and translation in side-by-side columns
    const parallelWrapper = document.createElement('div');
    parallelWrapper.className = 'parallel-verse';

    // Left column: Ge'ez
    const geezCol = document.createElement('div');
    geezCol.className = 'parallel-geez';
    const geezLabel = document.createElement('div');
    geezLabel.className = 'parallel-label';
    geezLabel.textContent = "Ge'ez";
    geezCol.appendChild(geezLabel);
    const geezContent = textDiv.cloneNode(true);
    geezCol.appendChild(geezContent);

    // Right column: English (Charles 1917)
    const engCol = document.createElement('div');
    engCol.className = 'parallel-english';
    const engLabel = document.createElement('div');
    engLabel.className = 'parallel-label';
    engLabel.textContent = 'English (Charles 1917)';
    engCol.appendChild(engLabel);
    const engContent = document.createElement('div');
    engContent.className = 'parallel-english-text';
    engContent.textContent = transDiv.textContent;
    engCol.appendChild(engContent);

    parallelWrapper.appendChild(geezCol);
    parallelWrapper.appendChild(engCol);

    // Hide original elements, insert parallel wrapper
    textDiv.style.display = 'none';
    transDiv.style.display = 'none';

    // Insert after verse-ref (or at beginning if no ref)
    if (verseRef && verseRef.nextSibling) {
        block.insertBefore(parallelWrapper, verseRef.nextSibling);
    } else {
        block.appendChild(parallelWrapper);
    }

    block.classList.add('parallel-active');
}


function disableParallel(block) {
    if (block.dataset.parallelApplied !== 'true') return;

    // Remove parallel wrapper
    const wrapper = block.querySelector('.parallel-verse');
    if (wrapper) {
        wrapper.remove();
    }

    // Restore original elements
    const textDiv = block.querySelector('.original-text.geez');
    const transDiv = block.querySelector('.translation');
    if (textDiv) textDiv.style.display = '';
    if (transDiv) transDiv.style.display = '';

    block.dataset.parallelApplied = 'false';
    block.classList.remove('parallel-active');

    // Re-enable interlinear button
    const ilBtn = document.getElementById('interlinear-toggle');
    if (ilBtn) {
        ilBtn.disabled = false;
        ilBtn.style.opacity = '1';
    }
}
