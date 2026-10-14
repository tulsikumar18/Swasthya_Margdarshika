/**
 * Personalized Medical Recommendation System - Client Application Logic
 * Modern Vanilla JavaScript with asynchronous Fetch API,
 * Conversational Natural Language Symptom Extraction & Confirmation,
 * Speech Recognition, and Auto-Deduplicating Multi-Symptom Tagging.
 */

(function () {
    'use strict';

    // State
    const state = {
        allSymptoms: [],           // Loaded from /api/symptoms
        selectedSymptoms: [],      // Active user-selected symptoms [{key, label}]
        extractedSymptomsBuffer: [], // Symptoms awaiting user confirmation
        isLoading: false,
        recognition: null,
        isRecording: false
    };

    // DOM Elements
    const elements = {
        symptomInput: document.getElementById('symptomSearchInput'),
        autocompleteList: document.getElementById('autocompleteDropdown'),
        selectedChipsContainer: document.getElementById('selectedChipsContainer'),
        emptyChipsNotice: document.getElementById('emptyChipsNotice'),
        selectedCountBadge: document.getElementById('selectedCountBadge'),
        predictionForm: document.getElementById('symptomCheckerForm'),
        hiddenSymptomsInput: document.getElementById('hiddenSymptomsInput'),
        submitButton: document.getElementById('predictSubmitBtn'),
        clearAllBtn: document.getElementById('clearAllSymptomsBtn'),
        loadingIndicator: document.getElementById('loadingIndicator'),
        errorContainer: document.getElementById('clientAlertContainer'),
        resultsContainer: document.getElementById('predictionResultsArea'),
        quickPills: document.querySelectorAll('.suggestion-pill'),
        
        // Mode switching
        modeQuickSelectBtn: document.getElementById('modeQuickSelectBtn'),
        modeConversationalBtn: document.getElementById('modeConversationalBtn'),
        quickSearchContainer: document.getElementById('quickSearchInputContainer'),
        conversationalContainer: document.getElementById('conversationalInputContainer'),
        conversationalText: document.getElementById('conversationalTextInput'),
        extractBtn: document.getElementById('extractSymptomsBtn'),

        // Confirmation Card
        confirmationCard: document.getElementById('symptomConfirmationCard'),
        confirmationChipsList: document.getElementById('confirmationChipsList'),
        confirmationPromptText: document.getElementById('confirmationPromptText'),
        detectedCountBadge: document.getElementById('detectedCountBadge'),
        confirmAndAnalyzeBtn: document.getElementById('confirmAndAnalyzeBtn'),
        cancelConfirmationBtn: document.getElementById('cancelConfirmationBtn'),

        // Speech Recognition
        micBtn: document.getElementById('micButton'),
        micConversationalBtn: document.getElementById('micConversationalBtn')
    };

    // Initialize application
    document.addEventListener('DOMContentLoaded', () => {
        loadSupportedSymptoms();
        setupEventListeners();
        setupSpeechRecognition();
    });

    /**
     * Fetches all 132 supported symptoms from the FastAPI backend.
     */
    async function loadSupportedSymptoms() {
        try {
            const response = await fetch('/api/symptoms');
            if (!response.ok) return;
            const data = await response.json();
            state.allSymptoms = data.symptoms || [];
        } catch (err) {
            console.error('Failed to load symptoms list:', err);
        }
    }

    /**
     * Sets up DOM event listeners.
     */
    function setupEventListeners() {
        // Autocomplete & Comma Input
        if (elements.symptomInput) {
            elements.symptomInput.addEventListener('input', handleInputChange);
            elements.symptomInput.addEventListener('keydown', handleInputKeydown);
            elements.symptomInput.addEventListener('paste', handleInputPaste);

            // Close dropdown when clicking outside
            document.addEventListener('click', (e) => {
                if (!elements.symptomInput.contains(e.target) && !elements.autocompleteList.contains(e.target)) {
                    hideAutocomplete();
                }
            });
        }

        // Quick suggestion pills
        elements.quickPills.forEach(pill => {
            pill.addEventListener('click', () => {
                const symptomKey = pill.getAttribute('data-symptom');
                const symptomLabel = pill.textContent.trim();
                addSymptom(symptomKey, symptomLabel);
            });
        });

        // Mode Toggles
        if (elements.modeQuickSelectBtn && elements.modeConversationalBtn) {
            elements.modeQuickSelectBtn.addEventListener('click', () => switchMode('quick'));
            elements.modeConversationalBtn.addEventListener('click', () => switchMode('conversational'));
        }

        // Extract Symptoms from Natural Language Text
        if (elements.extractBtn) {
            elements.extractBtn.addEventListener('click', () => {
                const text = elements.conversationalText ? elements.conversationalText.value.trim() : '';
                if (!text) {
                    showAlert('Please describe your symptoms first.', 'warning');
                    return;
                }
                extractSymptomsFromText(text);
            });
        }

        // Confirmation Actions
        if (elements.confirmAndAnalyzeBtn) {
            elements.confirmAndAnalyzeBtn.addEventListener('click', handleConfirmAndAnalyze);
        }

        if (elements.cancelConfirmationBtn) {
            elements.cancelConfirmationBtn.addEventListener('click', () => {
                hideConfirmationCard();
            });
        }

        // Clear all selected symptoms
        if (elements.clearAllBtn) {
            elements.clearAllBtn.addEventListener('click', () => {
                state.selectedSymptoms = [];
                renderSelectedChips();
                hideAlert();
                hideConfirmationCard();
            });
        }

        // Form submission (AJAX Fetch)
        if (elements.predictionForm) {
            elements.predictionForm.addEventListener('submit', handleFormSubmit);
        }
    }

    /**
     * Switches between Search & Select mode vs Conversational Speech/Text mode.
     */
    function switchMode(mode) {
        if (mode === 'conversational') {
            elements.modeConversationalBtn.classList.add('active');
            elements.modeQuickSelectBtn.classList.remove('active');
            elements.conversationalContainer.style.display = 'block';
            elements.quickSearchContainer.style.display = 'none';
            if (elements.conversationalText) elements.conversationalText.focus();
        } else {
            elements.modeQuickSelectBtn.classList.add('active');
            elements.modeConversationalBtn.classList.remove('active');
            elements.quickSearchContainer.style.display = 'block';
            elements.conversationalContainer.style.display = 'none';
            if (elements.symptomInput) elements.symptomInput.focus();
        }
    }

    /**
     * Handles typing in search input: detects commas or autocompletes.
     */
    function handleInputChange() {
        const value = elements.symptomInput.value;

        // If user typed a comma, split and add preceding symptoms
        if (value.includes(',')) {
            processCommaSeparatedInput(value);
            return;
        }

        const query = value.trim().toLowerCase();
        if (!query) {
            hideAutocomplete();
            return;
        }

        const matches = state.allSymptoms.filter(item => {
            const keyMatch = item.key.toLowerCase().includes(query.replace(' ', '_'));
            const labelMatch = item.label.toLowerCase().includes(query);
            return (keyMatch || labelMatch) && !state.selectedSymptoms.some(s => s.key === item.key);
        }).slice(0, 8);

        renderAutocomplete(matches, query);
    }

    /**
     * Handles pasted comma-separated text (e.g. "stomach_pain, acidity, ulcers_on_tongue, vomiting").
     */
    function handleInputPaste(e) {
        setTimeout(() => {
            const text = elements.symptomInput.value;
            if (text.includes(',') || text.includes(';') || text.includes(' then ')) {
                processCommaSeparatedInput(text);
            }
        }, 10);
    }

    /**
     * Processes text containing commas or delimiters into individual symptoms.
     */
    function processCommaSeparatedInput(rawText) {
        const parts = rawText.split(/[,;\n]+/).map(p => p.trim()).filter(Boolean);
        if (parts.length > 1) {
            parts.forEach(part => {
                const normKey = part.toLowerCase().replace(/\s+/g, '_');
                addSymptom(normKey, formatSymptomTitle(part));
            });
            elements.symptomInput.value = '';
            hideAutocomplete();
        }
    }

    /**
     * Handles Enter key in search box.
     */
    function handleInputKeydown(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            const text = elements.symptomInput.value.trim();
            if (!text) return;

            // If it contains commas, process as list
            if (text.includes(',')) {
                processCommaSeparatedInput(text);
                return;
            }

            const firstItem = elements.autocompleteList.querySelector('.autocomplete-item');
            if (firstItem && elements.autocompleteList.style.display !== 'none') {
                firstItem.click();
            } else {
                // If it looks like conversational sentence, extract symptoms
                if (text.split(' ').length > 2 || text.includes('feeling') || text.includes('have')) {
                    extractSymptomsFromText(text);
                } else {
                    addSymptom(text.toLowerCase().replace(/\s+/g, '_'), formatSymptomTitle(text));
                }
                elements.symptomInput.value = '';
                hideAutocomplete();
            }
        } else if (e.key === 'Escape') {
            hideAutocomplete();
        }
    }

    /**
     * Calls POST /api/symptoms/extract to parse natural conversational sentences.
     */
    async function extractSymptomsFromText(text) {
        setLoading(true);
        hideAlert();

        try {
            const response = await fetch('/api/symptoms/extract', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text })
            });

            if (!response.ok) {
                showAlert('Could not extract symptoms from text.', 'danger');
                return;
            }

            const data = await response.json();
            const extracted = data.extracted_symptoms || [];

            if (extracted.length === 0) {
                showAlert('No recognized clinical symptoms were identified in your description. Please choose from the list or try different keywords.', 'info');
                return;
            }

            if (extracted.length < 4) {
                showAlert(`Identified ${extracted.length} symptom(s). At least 4 symptoms are required for accurate diagnosis (need ${4 - extracted.length} more). Please confirm these and add additional symptoms.`, 'info');
            }

            // Show Confirmation Card
            showConfirmationCard(extracted, data.confirmation_message);

        } catch (err) {
            console.error('Extract error:', err);
            showAlert('Error contacting extraction service.', 'danger');
        } finally {
            setLoading(false);
        }
    }

    /**
     * Displays the interactive Confirmation Card for user review.
     */
    function showConfirmationCard(extractedList, promptText) {
        if (!elements.confirmationCard) return;

        state.extractedSymptomsBuffer = [...extractedList];
        const count = extractedList.length;
        const countNotice = count < 4 
            ? ` (${count}/4 required - please add ${4 - count} more)` 
            : ` (${count} detected)`;
        
        elements.confirmationPromptText.textContent = promptText + (count < 4 ? ` Please note: at least 4 symptoms are required for accurate prediction.` : '');
        elements.detectedCountBadge.textContent = `${count} detected` + (count < 4 ? ` (min 4 required)` : '');
        elements.confirmationChipsList.innerHTML = '';

        extractedList.forEach((item, index) => {
            const chip = document.createElement('span');
            chip.className = 'badge bg-primary px-3 py-2 rounded-pill d-inline-flex align-items-center gap-2';
            chip.innerHTML = `
                <span>${escapeHtml(item.label)}</span>
                <button type="button" class="btn-close btn-close-white btn-sm" style="font-size: 0.65rem;" aria-label="Remove"></button>
            `;
            chip.querySelector('.btn-close').addEventListener('click', () => {
                state.extractedSymptomsBuffer.splice(index, 1);
                showConfirmationCard(state.extractedSymptomsBuffer, promptText);
            });
            elements.confirmationChipsList.appendChild(chip);
        });

        elements.confirmationCard.style.display = 'block';
        elements.confirmationCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    function hideConfirmationCard() {
        if (elements.confirmationCard) {
            elements.confirmationCard.style.display = 'none';
        }
        state.extractedSymptomsBuffer = [];
    }

    /**
     * User clicks "Confirm & Proceed to Diagnosis" on the confirmation card.
     */
    function handleConfirmAndAnalyze() {
        if (state.extractedSymptomsBuffer.length === 0) {
            showAlert('No symptoms selected to confirm.', 'warning');
            hideConfirmationCard();
            return;
        }

        // Add confirmed symptoms to selectedSymptoms
        state.extractedSymptomsBuffer.forEach(item => {
            if (!state.selectedSymptoms.some(s => s.key === item.key)) {
                state.selectedSymptoms.push(item);
            }
        });

        renderSelectedChips();
        hideConfirmationCard();

        // Switch to quick mode for viewing selected chips and results
        switchMode('quick');

        // Check if we meet the minimum 4 symptoms requirement
        if (state.selectedSymptoms.length < 4) {
            showAlert(`Confirmed ${state.selectedSymptoms.length} symptom(s). At least 4 symptoms are required for accurate analysis. Please select at least ${4 - state.selectedSymptoms.length} more symptom(s) below.`, 'warning');
            if (elements.symptomInput) {
                elements.symptomInput.focus();
                elements.symptomInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
            return;
        }

        // Automatically trigger prediction if 4 or more symptoms are confirmed!
        if (elements.predictionForm) {
            submitPrediction();
        }
    }

    /**
     * Setup Web Speech API for voice recording.
     */
    function setupSpeechRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            if (elements.micBtn) elements.micBtn.style.display = 'none';
            if (elements.micConversationalBtn) elements.micConversationalBtn.style.display = 'none';
            return;
        }

        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';

        recognition.onstart = () => {
            state.isRecording = true;
            if (elements.micBtn) elements.micBtn.classList.add('text-danger', 'fa-fade');
            if (elements.micConversationalBtn) {
                elements.micConversationalBtn.innerHTML = '<i class="fas fa-circle-dot text-danger fa-fade me-1"></i> Listening... Speak Now';
            }
        };

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            console.log('Speech transcript:', transcript);

            // If in conversational mode, place in textarea and auto extract
            if (elements.conversationalContainer && elements.conversationalContainer.style.display !== 'none') {
                if (elements.conversationalText) {
                    elements.conversationalText.value = transcript;
                }
                extractSymptomsFromText(transcript);
            } else {
                // If in quick search mode, put in input and extract
                if (elements.symptomInput) {
                    elements.symptomInput.value = transcript;
                }
                extractSymptomsFromText(transcript);
            }
        };

        recognition.onerror = (e) => {
            console.warn('Speech recognition error:', e.error);
            state.isRecording = false;
            resetMicUI();
        };

        recognition.onend = () => {
            state.isRecording = false;
            resetMicUI();
        };

        state.recognition = recognition;

        const toggleRecording = () => {
            if (state.isRecording) {
                recognition.stop();
            } else {
                try { recognition.start(); } catch (err) { console.warn(err); }
            }
        };

        if (elements.micBtn) elements.micBtn.addEventListener('click', toggleRecording);
        if (elements.micConversationalBtn) elements.micConversationalBtn.addEventListener('click', toggleRecording);
    }

    function resetMicUI() {
        if (elements.micBtn) elements.micBtn.classList.remove('text-danger', 'fa-fade');
        if (elements.micConversationalBtn) {
            elements.micConversationalBtn.innerHTML = '<i class="fas fa-microphone me-1"></i> Speak Symptoms';
        }
    }

    /**
     * Renders autocomplete dropdown options.
     */
    function renderAutocomplete(matches, query) {
        if (!elements.autocompleteList) return;
        elements.autocompleteList.innerHTML = '';

        if (matches.length === 0) {
            const customDiv = document.createElement('div');
            customDiv.className = 'autocomplete-item text-muted';
            customDiv.innerHTML = `<span><i class="fas fa-plus-circle me-2 text-primary"></i>Add "<strong>${escapeHtml(query)}</strong>"</span> <small class="badge bg-secondary-subtle text-secondary">Custom</small>`;
            customDiv.addEventListener('click', () => {
                addSymptom(query.toLowerCase().replace(/\s+/g, '_'), formatSymptomTitle(query));
                elements.symptomInput.value = '';
                hideAutocomplete();
            });
            elements.autocompleteList.appendChild(customDiv);
        } else {
            matches.forEach(item => {
                const itemDiv = document.createElement('div');
                itemDiv.className = 'autocomplete-item';
                itemDiv.innerHTML = `<span><i class="fas fa-notes-medical me-2 text-primary"></i>${escapeHtml(item.label)}</span> <small class="text-muted font-monospace">ML Dataset</small>`;
                itemDiv.addEventListener('click', () => {
                    addSymptom(item.key, item.label);
                    elements.symptomInput.value = '';
                    hideAutocomplete();
                });
                elements.autocompleteList.appendChild(itemDiv);
            });
        }

        elements.autocompleteList.style.display = 'block';
    }

    function hideAutocomplete() {
        if (elements.autocompleteList) {
            elements.autocompleteList.style.display = 'none';
        }
    }

    /**
     * Adds a symptom to the selected list.
     */
    function addSymptom(key, label) {
        if (!key) return;
        if (state.selectedSymptoms.some(s => s.key === key)) {
            return;
        }

        state.selectedSymptoms.push({ key, label: label || formatSymptomTitle(key) });
        renderSelectedChips();
        hideAlert();
    }

    /**
     * Removes a symptom by key.
     */
    function removeSymptom(key) {
        state.selectedSymptoms = state.selectedSymptoms.filter(s => s.key !== key);
        renderSelectedChips();
    }

    /**
     * Re-renders the selected symptom tags/chips in the DOM.
     */
    function renderSelectedChips() {
        if (!elements.selectedChipsContainer) return;
        elements.selectedChipsContainer.innerHTML = '';

        const count = state.selectedSymptoms.length;
        if (elements.selectedCountBadge) {
            elements.selectedCountBadge.textContent = `${count} selected`;
        }

        if (count === 0) {
            if (elements.emptyChipsNotice) elements.emptyChipsNotice.style.display = 'block';
            if (elements.hiddenSymptomsInput) elements.hiddenSymptomsInput.value = '';
            return;
        }

        if (elements.emptyChipsNotice) elements.emptyChipsNotice.style.display = 'none';

        state.selectedSymptoms.forEach(item => {
            const chip = document.createElement('span');
            chip.className = 'symptom-chip';
            chip.innerHTML = `
                <span>${escapeHtml(item.label)}</span>
                <button type="button" class="chip-remove" aria-label="Remove symptom">&times;</button>
            `;
            chip.querySelector('.chip-remove').addEventListener('click', (e) => {
                e.stopPropagation();
                removeSymptom(item.key);
            });
            elements.selectedChipsContainer.appendChild(chip);
        });

        if (elements.hiddenSymptomsInput) {
            elements.hiddenSymptomsInput.value = state.selectedSymptoms.map(s => s.key).join(',');
        }
    }

    /**
     * Handles Asynchronous Form Submission.
     */
    function handleFormSubmit(e) {
        e.preventDefault();
        submitPrediction();
    }

    /**
     * Executes prediction using Fetch API.
     */
    async function submitPrediction() {
        if (state.selectedSymptoms.length === 0) {
            showAlert('Please select or enter at least 4 symptoms before predicting.', 'warning');
            if (elements.symptomInput) elements.symptomInput.focus();
            return;
        }

        if (state.selectedSymptoms.length < 4) {
            showAlert(`Please select or enter at least 4 symptoms for accurate disease prediction (currently selected: ${state.selectedSymptoms.length}). At least 4 symptoms are required to reliably identify a condition and avoid misclassification.`, 'warning');
            if (elements.symptomInput) {
                elements.symptomInput.focus();
                elements.symptomInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
            return;
        }

        setLoading(true);
        hideAlert();

        const symptomKeys = state.selectedSymptoms.map(s => s.key);

        try {
            const response = await fetch('/api/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    symptoms: symptomKeys,
                    allow_ai_fallback: true
                })
            });

            const data = await response.json();

            if (!response.ok) {
                const errorMsg = data.detail || data.message || 'An error occurred during prediction.';
                showAlert(errorMsg, 'danger');
                return;
            }

            renderPredictionResults(data);

            if (elements.resultsContainer) {
                elements.resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }

        } catch (error) {
            console.error('Fetch error:', error);
            showAlert('Network or server error. Please ensure the server is running and try again.', 'danger');
        } finally {
            setLoading(false);
        }
    }

    /**
     * Renders the structured prediction response in the results area.
     */
    function renderPredictionResults(data) {
        if (!elements.resultsContainer) return;

        // ── Special case: need more symptoms ────────────────────────────────
        if (data.mode === 'clarification_required') {
            const foundChips = (data.recognized_symptoms || []).map(k =>
                `<span class="selected-chip" style="pointer-events:none;">${escapeHtml(k.replace(/_/g,' ').replace(/\b\w/g,c=>c.toUpperCase()))}</span>`
            ).join('');

            const tipsHtml = (data.precautions || []).map(t =>
                `<li class="mb-1"><i class="fas fa-lightbulb text-warning me-2"></i>${escapeHtml(t)}</li>`
            ).join('');

            const html = `
                <div class="result-box mt-5">
                    <div class="result-header d-flex flex-wrap align-items-center justify-content-between gap-3">
                        <div>
                            <div class="d-flex align-items-center gap-2 mb-2">
                                <span class="mode-badge mode-clarify"><i class="fas fa-magnifying-glass-plus me-1"></i> More Symptoms Needed</span>
                            </div>
                            <h2 class="fw-bold mb-1">Let's narrow it down</h2>
                            <p class="text-muted small mb-0">${escapeHtml(data.message)}</p>
                        </div>
                    </div>
                    <div class="p-4 p-md-5">
                        <div class="neu-card p-4 mb-4">
                            <h5 class="fw-bold mb-3 text-primary d-flex align-items-center gap-2">
                                <i class="fas fa-notes-medical"></i> Symptoms Recognized So Far
                            </h5>
                            <div class="d-flex flex-wrap gap-2 mb-3">
                                ${foundChips || '<span class="text-muted small">None yet</span>'}
                            </div>
                            <p class="text-secondary mb-0" style="font-size:1rem;">
                                ${escapeHtml(data.description || '')}
                            </p>
                        </div>
                        <div class="neu-card p-4 mb-4">
                            <h5 class="fw-bold mb-3 text-primary d-flex align-items-center gap-2">
                                <i class="fas fa-circle-question"></i> What to Add Next
                            </h5>
                            <ul class="list-unstyled mb-3 text-secondary small">
                                ${tipsHtml}
                            </ul>
                            <button type="button" class="neu-btn neu-btn-action px-4 py-2"
                                onclick="document.getElementById('symptomSearchInput').focus(); document.getElementById('checker-section').scrollIntoView({behavior:'smooth'});">
                                <i class="fas fa-plus-circle me-2"></i> Add More Symptoms
                            </button>
                        </div>
                        <div class="neu-card p-3 d-flex align-items-start gap-3" role="alert">
                            <i class="fas fa-triangle-exclamation text-warning fs-4 mt-1"></i>
                            <div class="small text-secondary">
                                <strong class="text-dark">Medical Notice:</strong> ${escapeHtml(data.disclaimer || '')}
                            </div>
                        </div>
                    </div>
                </div>`;

            elements.resultsContainer.innerHTML = html;
            elements.resultsContainer.style.display = 'block';
            elements.resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
            return;
        }

        // ── Normal result rendering ──────────────────────────────────────────
        let modeBadge = '';
        if (data.mode === 'ml_prediction') {
            modeBadge = '<span class="mode-badge mode-ml"><i class="fas fa-check-circle me-1"></i> Validated ML Prediction</span>';
        } else if (data.mode === 'ai_assisted') {
            modeBadge = '<span class="mode-badge mode-ai"><i class="fas fa-robot me-1"></i> AI-Assisted Informational Guidance</span>';
        } else {
            modeBadge = '<span class="mode-badge mode-fallback"><i class="fas fa-info-circle me-1"></i> Health Guidance</span>';
        }

        let confidenceBadge = '';
        if (data.confidence !== null && data.confidence !== undefined) {
            const pct = Math.round(data.confidence * 100);
            confidenceBadge = `<span class="neu-btn text-primary py-1 px-3" style="font-size: 0.8rem;"><i class="fas fa-gauge me-1"></i> Model Confidence: ${pct}%</span>`;
        } else {
            confidenceBadge = `<span class="neu-btn text-secondary py-1 px-3" style="font-size: 0.8rem;" title="SVC model uses deterministic hyperplane classification without probability scoring"><i class="fas fa-info-circle me-1"></i> Confidence: Deterministic SVM</span>`;
        }

        const renderListItems = (items, emptyText, icon = 'check-circle', iconColor = '#0284c7') => {
            if (!items || items.length === 0) {
                return `<li class="list-group-item text-muted small">${emptyText}</li>`;
            }
            return items.map(item => `
                <li class="list-group-item d-flex align-items-start gap-2 border-0 px-0 py-2">
                    <i class="fas fa-${icon} mt-1" style="color: ${iconColor};"></i>
                    <span>${escapeHtml(item)}</span>
                </li>
            `).join('');
        };

        const html = `
            <div class="result-box mt-5">
                <div class="result-header d-flex flex-wrap align-items-center justify-content-between gap-3">
                    <div>
                        <div class="d-flex align-items-center gap-2 mb-2">
                            ${modeBadge}
                            ${confidenceBadge}
                        </div>
                        <h2 class="fw-bold mb-1">${escapeHtml(data.predicted_disease || 'Symptom Evaluation')}</h2>
                        <p class="text-muted small mb-0">${escapeHtml(data.message)}</p>
                    </div>
                    <div class="d-flex gap-2">
                        <button type="button" class="neu-btn btn-sm" id="readAloudBtn">
                            <i class="fas fa-volume-high me-1 text-primary"></i> Read Aloud
                        </button>
                        <button type="button" class="neu-btn btn-sm" onclick="window.print()">
                            <i class="fas fa-print me-1"></i> Print
                        </button>
                    </div>
                </div>

                <div class="p-4 p-md-5">
                    <div class="neu-card p-4 mb-4">
                        <h5 class="fw-bold mb-2 text-primary d-flex align-items-center gap-2">
                            <i class="fas fa-book-medical"></i> Overview &amp; Description
                        </h5>
                        <p class="mb-0 text-secondary" style="font-size: 1.05rem;">
                            ${escapeHtml(data.description || 'No detailed description available.')}
                        </p>
                    </div>

                    <div class="row g-4 mb-4">
                        <div class="col-lg-6">
                            <div class="category-card">
                                <div class="neu-circle-recessed text-primary mb-3">
                                    <i class="fas fa-pills"></i>
                                </div>
                                <h5 class="fw-bold mb-1">Recommended Medicines (Top 5)</h5>
                                <p class="text-muted small mb-3">Informational list from medical dataset. Not a prescription.</p>
                                <ul class="list-group list-group-flush">
                                    ${renderListItems(data.medications, 'No specific medications listed.', 'capsules', '#0284c7')}
                                </ul>
                            </div>
                        </div>

                        <div class="col-lg-6">
                            <div class="category-card">
                                <div class="neu-circle-recessed text-warning mb-3">
                                    <i class="fas fa-shield-virus"></i>
                                </div>
                                <h5 class="fw-bold mb-1">Preventative Precautions</h5>
                                <p class="text-muted small mb-3">Key health safeguards to minimize complications.</p>
                                <ul class="list-group list-group-flush">
                                    ${renderListItems(data.precautions, 'Standard health precautions apply.', 'shield-halved', '#f59e0b')}
                                </ul>
                            </div>
                        </div>

                        <div class="col-lg-6">
                            <div class="category-card">
                                <div class="neu-circle-recessed text-success mb-3">
                                    <i class="fas fa-carrot"></i>
                                </div>
                                <h5 class="fw-bold mb-1">Dietary Recommendations</h5>
                                <p class="text-muted small mb-3">Nutritional choices supporting recovery.</p>
                                <ul class="list-group list-group-flush">
                                    ${renderListItems(data.diet_recommendations, 'Maintain standard balanced hydration and nutrition.', 'leaf', '#10b981')}
                                </ul>
                            </div>
                        </div>

                        <div class="col-lg-6">
                            <div class="category-card">
                                <div class="neu-circle-recessed text-purple mb-3">
                                    <i class="fas fa-person-running"></i>
                                </div>
                                <h5 class="fw-bold mb-1">Workout &amp; Physical Rest</h5>
                                <p class="text-muted small mb-3">Appropriate activity levels and routines.</p>
                                <ul class="list-group list-group-flush">
                                    ${renderListItems(data.workout_recommendations, 'Rest and avoid strenuous exercise as tolerated.', 'heart-pulse', '#8b5cf6')}
                                </ul>
                            </div>
                        </div>
                    </div>

                    <div class="neu-card p-4 d-flex align-items-start gap-3" role="alert">
                        <i class="fas fa-triangle-exclamation text-warning fs-4 mt-1"></i>
                        <div class="small text-secondary">
                            <strong class="text-dark">Medical Notice:</strong> ${escapeHtml(data.disclaimer)}
                        </div>
                    </div>
                </div>
            </div>
        `;

        elements.resultsContainer.innerHTML = html;
        elements.resultsContainer.style.display = 'block';

        const readBtn = document.getElementById('readAloudBtn');
        if (readBtn) {
            readBtn.addEventListener('click', () => {
                readResultsAloud(data);
            });
        }
    }



    /**
     * Browser Web Speech API for voice reading.
     */
    function readResultsAloud(data) {
        if (!('speechSynthesis' in window)) {
            showAlert('Speech synthesis is not supported in your browser.', 'info');
            return;
        }

        window.speechSynthesis.cancel();
        const textToRead = `Predicted condition: ${data.predicted_disease}. Description: ${data.description}. Recommended precautions: ${data.precautions.join('. ')}.`;
        const utterance = new SpeechSynthesisUtterance(textToRead);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        window.speechSynthesis.speak(utterance);
    }

    /**
     * Toggles loading spinner.
     */
    function setLoading(loading) {
        state.isLoading = loading;
        if (elements.loadingIndicator) {
            elements.loadingIndicator.style.display = loading ? 'block' : 'none';
        }
        if (elements.submitButton) {
            elements.submitButton.disabled = loading;
            elements.submitButton.innerHTML = loading
                ? '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Analyzing Symptoms...'
                : '<i class="fas fa-stethoscope me-2"></i>Analyze Symptoms';
        }
    }

    function showAlert(message, type = 'danger') {
        if (!elements.errorContainer) return;

        let icon = 'circle-exclamation';
        if (type === 'warning') icon = 'triangle-exclamation';
        else if (type === 'info') icon = 'circle-info';
        else if (type === 'success') icon = 'circle-check';

        elements.errorContainer.innerHTML = `
            <div class="neu-alert neu-alert-${type}" role="alert">
                <div class="d-flex align-items-center gap-3">
                    <div class="neu-alert-icon-box">
                        <i class="fas fa-${icon}"></i>
                    </div>
                    <div class="neu-alert-text">
                        ${escapeHtml(message)}
                    </div>
                </div>
                <button type="button" class="neu-alert-close" aria-label="Close" onclick="this.closest('.neu-alert').remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        elements.errorContainer.style.display = 'block';
    }

    function hideAlert() {
        if (elements.errorContainer) {
            elements.errorContainer.innerHTML = '';
            elements.errorContainer.style.display = 'none';
        }
    }

    function formatSymptomTitle(key) {
        return key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()).trim();
    }

    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

})();
