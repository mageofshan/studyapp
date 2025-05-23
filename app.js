// Elements
const startLearnBtn = document.getElementById('start-learn-btn');
const settingsModal = document.getElementById('settings-modal');
const closeModalBtns = document.querySelectorAll('.close-modal, .close-settings');
const startQuizBtn = document.getElementById('start-quiz-btn');
const homeScreen = document.getElementById('home-screen');
const quizContainer = document.getElementById('quiz-container');
const resultsContainer = document.getElementById('results-container');
const nextQuestionBtn = document.getElementById('next-question-btn');
const exitQuizBtn = document.getElementById('exit-quiz-btn');
const backToSetBtn = document.getElementById('back-to-set-btn');
const newRoundBtn = document.getElementById('new-round-btn');
const progressBar = document.querySelector('.progress-bar');
const addCardBtn = document.getElementById('add-card-btn');
const starBtns = document.querySelectorAll('.star-btn');
const submitAnswerBtn = document.getElementById('submit-answer-btn');
const sidebarSets = document.querySelector('.sidebar-sets');
const deleteSetBtn = document.querySelector('.delete-set-btn');

// Track total questions answered for continuous rounds
let totalQuestionsAnswered = 0;
let totalQuestionsCount = 0;

// --- SETS LOGIC ---

// Initial flashcards for default set
let defaultFlashcards = [
    {
        term: 'for loop',
        definition: 'A loop that iterates over a sequence of items',
        mastery: 0,
        starred: false
    },
    {
        term: 'list comprehension',
        definition: 'A concise way to create lists based on existing lists',
        mastery: 0,
        starred: true
    },
    {
        term: 'dictionary',
        definition: 'A collection of key-value pairs',
        mastery: 0,
        starred: false
    }
];

let sets = {};
let currentSetName = '';

function saveSets() {
    localStorage.setItem('flashlearn_sets', JSON.stringify(sets));
    localStorage.setItem('flashlearn_currentSet', currentSetName);
}

function loadSets() {
    const saved = localStorage.getItem('flashlearn_sets');
    const savedCurrent = localStorage.getItem('flashlearn_currentSet');
    if (saved) {
        sets = JSON.parse(saved);
    } else {
        sets = {'Python Basics': defaultFlashcards};
    }
    if (savedCurrent && sets[savedCurrent]) {
        currentSetName = savedCurrent;
    } else {
        currentSetName = Object.keys(sets)[0];
    }
}

function renderSidebarSets() {
    sidebarSets.innerHTML = '<h3>Your Sets</h3>';
    Object.keys(sets).forEach(setName => {
        const div = document.createElement('div');
        div.className = 'set-item' + (setName === currentSetName ? ' active' : '');
        div.textContent = setName;
        div.onclick = () => {
            currentSetName = setName;
            renderSidebarSets();
            onSetChange();
            saveSets();
        };
        sidebarSets.appendChild(div);
    });
}

document.querySelector('.new-set-btn').onclick = function () {
    const setName = prompt('Enter a name for your new set:');
    if (setName && !sets[setName]) {
        sets[setName] = [];
        currentSetName = setName;
        renderSidebarSets();
        onSetChange();
        saveSets();
    } else if (sets[setName]) {
        alert('A set with that name already exists.');
    }
};

deleteSetBtn.onclick = function () {
    if (Object.keys(sets).length === 1) {
        alert('You must have at least one set.');
        return;
    }
    if (confirm(`Delete set "${currentSetName}"? This cannot be undone.`)) {
        delete sets[currentSetName];
        // Pick another set
        currentSetName = Object.keys(sets)[0];
        saveSets();
        renderSidebarSets();
        onSetChange();
    }
};

// --- FLASHCARD CAROUSEL LOGIC ---
let carouselIndex = 0;
let carouselFlipped = false;

function renderFlashcardCarousel() {
    const cards = sets[currentSetName] || [];
    const front = document.getElementById('carousel-flashcard-front');
    const back = document.getElementById('carousel-flashcard-back');
    const card = cards[carouselIndex] || { term: '', definition: '' };
    front.textContent = card.term;
    back.textContent = card.definition;
    const flashcard = document.getElementById('carousel-flashcard');
    if (carouselFlipped) {
        flashcard.classList.add('flipped');
    } else {
        flashcard.classList.remove('flipped');
    }
}

function updateCarouselIndex(delta) {
    const cards = sets[currentSetName] || [];
    if (!cards.length) return;
    carouselIndex = (carouselIndex + delta + cards.length) % cards.length;
    carouselFlipped = false;
    renderFlashcardCarousel();
}

document.getElementById('carousel-left').onclick = () => updateCarouselIndex(-1);
document.getElementById('carousel-right').onclick = () => updateCarouselIndex(1);
document.getElementById('carousel-flashcard').onclick = () => {
    carouselFlipped = !carouselFlipped;
    renderFlashcardCarousel();
};

document.addEventListener('keydown', (e) => {
    if (document.activeElement.tagName === 'INPUT') return;
    if (e.key === 'ArrowLeft') updateCarouselIndex(-1);
    if (e.key === 'ArrowRight') updateCarouselIndex(1);
    if (e.key === ' ') {
        carouselFlipped = !carouselFlipped;
        renderFlashcardCarousel();
    }
});

// --- FLASHCARD LIST/ADD ROW LOGIC ---
function renderFlashcardList() {
    const flashcardList = document.querySelector('.flashcard-list');
    // Only keep the add row
    flashcardList.innerHTML = '';
    // Add row
    const addRow = document.createElement('div');
    addRow.className = 'flashcard-item add-row';
    addRow.innerHTML = `
        <input type="text" class="term add-term" placeholder="Enter term">
        <input type="text" class="definition add-definition" placeholder="Enter definition">
        <div></div>
        <button class="btn primary-btn add-row-btn">Add</button>
    `;
    flashcardList.appendChild(addRow);
    // Add event for add button
    addRow.querySelector('.add-row-btn').onclick = function () {
        const termInput = addRow.querySelector('.add-term');
        const defInput = addRow.querySelector('.add-definition');
        if (termInput.value && defInput.value) {
            const newCard = {
                term: termInput.value,
                definition: defInput.value,
                mastery: 0,
                starred: false
            };
            sets[currentSetName].push(newCard);
            saveSets();
            renderFlashcardList();
            renderFlashcardCarousel();
            termInput.value = '';
            defInput.value = '';
        }
    };
    // Render all cards
    (sets[currentSetName] || []).forEach((card, idx) => {
        const newItem = document.createElement('div');
        newItem.className = 'flashcard-item';
        newItem.innerHTML = `
             <div class="term-cell">${card.term}</div>
             <div class="definition-cell">${card.definition}</div>
             <div class="mastery-indicator">
                 <div class="mastery-bar">
                     <div class="mastery-fill" style="width: ${card.mastery}%;"></div>
                 </div>
                 ${card.mastery}%
             </div>
             <button class="star-btn${card.starred ? ' active' : ''}">★</button>
             <button class="edit-btn">✎</button>
             <button class="delete-btn">🗑️</button>
         `;
        // Star button
        const starBtn = newItem.querySelector('.star-btn');
        starBtn.addEventListener('click', function () {
            this.classList.toggle('active');
            card.starred = this.classList.contains('active');
            saveSets();
        });
        // Delete button
        const deleteBtn = newItem.querySelector('.delete-btn');
        deleteBtn.addEventListener('click', function () {
            if (confirm(`Delete term "${card.term}"?`)) {
                sets[currentSetName].splice(idx, 1);
                saveSets();
                renderFlashcardList();
                renderFlashcardCarousel();
            }
        });
        // Edit button
        const editBtn = newItem.querySelector('.edit-btn');
        editBtn.addEventListener('click', function () {
            // Replace term and definition cells with input fields
            const termCell = newItem.querySelector('.term-cell');
            const defCell = newItem.querySelector('.definition-cell');
            const oldTerm = card.term;
            const oldDef = card.definition;
            termCell.innerHTML = `<input type="text" class="edit-term-input" value="${card.term}">`;
            defCell.innerHTML = `<input type="text" class="edit-def-input" value="${card.definition}">`;
            editBtn.style.display = 'none';
            // Add save/cancel buttons
            const saveBtn = document.createElement('button');
            saveBtn.textContent = 'Save';
            saveBtn.className = 'save-btn';
            const cancelBtn = document.createElement('button');
            cancelBtn.textContent = 'Cancel';
            cancelBtn.className = 'cancel-btn';
            newItem.insertBefore(saveBtn, deleteBtn);
            newItem.insertBefore(cancelBtn, deleteBtn);
            saveBtn.onclick = function () {
                const newTerm = termCell.querySelector('.edit-term-input').value.trim();
                const newDef = defCell.querySelector('.edit-def-input').value.trim();
                if (newTerm && newDef) {
                    card.term = newTerm;
                    card.definition = newDef;
                    saveSets();
                    renderFlashcardList();
                    renderFlashcardCarousel();
                }
            };
            cancelBtn.onclick = function () {
                card.term = oldTerm;
                card.definition = oldDef;
                renderFlashcardList();
            };
        });
        flashcardList.appendChild(newItem);
    });
}

// Update carousel and list when set changes
function onSetChange() {
    carouselIndex = 0;
    carouselFlipped = false;
    renderFlashcardCarousel();
    renderFlashcardList();
}

// Quiz State
let quizState = {
    settings: {
        examDate: null,
        roundLength: 10,
        questionTypes: ['multipleChoice', 'written', 'trueFalse'],
        answerWith: 'term',
        shuffleTerms: true,
        allowTypos: true
    },
    currentRound: [],
    currentQuestionIndex: 0,
    correctAnswers: 0
};

// State for selected answer
let selectedOption = null;
let answerSubmitted = false;

// Event Listeners
startLearnBtn.addEventListener('click', () => {
    settingsModal.style.display = 'flex';
});

closeModalBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        settingsModal.style.display = 'none';
    });
});

// Close modal if clicked outside
window.addEventListener('click', (e) => {
    if (e.target === settingsModal) {
        settingsModal.style.display = 'none';
    }
});

// Start quiz
startQuizBtn.addEventListener('click', () => {
    // Get settings
    quizState.settings.examDate = document.getElementById('exam-date').value;
    quizState.settings.roundLength = parseInt(document.getElementById('round-length').value);

    quizState.settings.questionTypes = [];
    if (document.getElementById('multiple-choice').checked) {
        quizState.settings.questionTypes.push('multipleChoice');
    }
    if (document.getElementById('written').checked) {
        quizState.settings.questionTypes.push('written');
    }
    if (document.getElementById('true-false').checked) {
        quizState.settings.questionTypes.push('trueFalse');
    }

    quizState.settings.answerWith = document.getElementById('answer-term').checked ? 'term' : 'definition';
    quizState.settings.shuffleTerms = document.getElementById('shuffle-terms').checked;
    quizState.settings.allowTypos = document.getElementById('allow-typos').checked;

    // Generate quiz round
    generateQuizRound();

    // Hide settings and show quiz
    settingsModal.style.display = 'none';
    homeScreen.style.display = 'none';
    quizContainer.style.display = 'block';

    // Display first question
    displayCurrentQuestion();
});

// Generate a round of questions based on settings
function generateQuizRound() {
    quizState.currentRound = [];
    quizState.currentQuestionIndex = 0;
    quizState.correctAnswers = 0;

    // Make a copy of flashcards
    let cards = [...(sets[currentSetName] || [])];

    // Shuffle if needed
    if (quizState.settings.shuffleTerms) {
        cards = shuffleArray(cards);
    }

    // Prioritize starred and low mastery cards
    cards.sort((a, b) => {
        if (a.starred && !b.starred) return -1;
        if (!a.starred && b.starred) return 1;
        return a.mastery - b.mastery;
    });

    // Repeat terms if not enough to fill round
    let needed = quizState.settings.roundLength;
    let roundCards = [];
    let i = 0;
    while (roundCards.length < needed) {
        roundCards.push(cards[i % cards.length]);
        i++;
        if (cards.length === 0) break; // Prevent infinite loop if no cards
    }

    // Generate questions for each card
    for (const card of roundCards) {
        // Choose question type randomly from allowed types
        const questionType = quizState.settings.questionTypes[
            Math.floor(Math.random() * quizState.settings.questionTypes.length)
        ];

        let question;

        switch (questionType) {
            case 'multipleChoice':
                question = generateMultipleChoiceQuestion(card);
                break;
            case 'written':
                question = generateWrittenQuestion(card);
                break;
            case 'trueFalse':
                question = generateTrueFalseQuestion(card);
                break;
        }

        quizState.currentRound.push({
            card: card,
            question: question,
            answered: false,
            correct: false
        });
    }
}

// Generate multiple choice question
function generateMultipleChoiceQuestion(card) {
    const isTermAnswer = quizState.settings.answerWith === 'term';
    const question = isTermAnswer ? card.definition : card.term;
    const correctAnswer = isTermAnswer ? card.term : card.definition;

    // Get incorrect options from other flashcards
    const allCards = sets[currentSetName] || [];
    const incorrectOptions = allCards
        .filter(c => c !== card)
        .map(c => isTermAnswer ? c.term : c.definition)
        .sort(() => 0.5 - Math.random())
        .slice(0, 3);

    // Combine and shuffle options
    let options = [correctAnswer, ...incorrectOptions];
    options = shuffleArray(options);

    return {
        type: 'multipleChoice',
        text: question,
        options: options,
        correctAnswer: correctAnswer
    };
}

// Generate true/false question
function generateTrueFalseQuestion(card) {
    const isCorrectPair = Math.random() > 0.5;
    let question, correctAnswer;
    const allCards = sets[currentSetName] || [];

    if (isCorrectPair || allCards.length < 2) {
        // True question - correct pairing
        question = `Is "${card.term}" correctly defined as: "${card.definition}"?`;
        correctAnswer = 'True';
    } else {
        // False question - incorrect pairing
        // Get a different definition
        const otherCard = allCards.find(c => c !== card);
        question = `Is "${card.term}" correctly defined as: "${otherCard.definition}"?`;
        correctAnswer = 'False';
    }

    // Combine and shuffle options
    let options = ['True', 'False'];

    return {
        type: 'trueFalse',
        text: question,
        options: options,
        correctAnswer: correctAnswer
    };
}

// Generate written question
function generateWrittenQuestion(card) {
    const isTermAnswer = quizState.settings.answerWith === 'term';
    const question = isTermAnswer ? card.definition : card.term;
    const correctAnswer = isTermAnswer ? card.term : card.definition;

    return {
        type: 'written',
        text: question,
        correctAnswer: correctAnswer
    };
}

// Display current question
function displayCurrentQuestion() {
    const currentItem = quizState.currentRound[quizState.currentQuestionIndex];
    const questionText = document.getElementById('question-text');

    // Update progress bar
    const progress = ((quizState.currentQuestionIndex + 1) / quizState.currentRound.length) * 100;
    progressBar.style.width = `${progress}%`;

    // Set question text
    questionText.textContent = currentItem.question.text;

    // Hide all answer containers
    document.querySelector('.multiple-choice-container').style.display = 'none';
    document.querySelector('.written-container').style.display = 'none';
    document.querySelector('.true-false-container').style.display = 'none';

    // Show appropriate answer container based on question type
    switch (currentItem.question.type) {
        case 'multipleChoice':
            setupMultipleChoiceQuestion(currentItem.question);
            break;

        case 'written':
            setupWrittenQuestion(currentItem.question);
            break;

        case 'trueFalse':
            setupTrueFalseQuestion(currentItem.question);
            break;
    }
}

// Setup multiple choice question display
function setupMultipleChoiceQuestion(question) {
    const container = document.querySelector('.multiple-choice-container');
    container.style.display = 'grid';
    container.innerHTML = '';
    selectedOption = null;
    answerSubmitted = false;
    submitAnswerBtn.style.display = 'inline-block';
    nextQuestionBtn.style.display = 'none';
    nextQuestionBtn.disabled = true;

    question.options.forEach(option => {
        const optionEl = document.createElement('div');
        optionEl.className = 'answer-option';
        optionEl.textContent = option;
        optionEl.tabIndex = 0;
        optionEl.addEventListener('click', function () {
            if (answerSubmitted) return;
            document.querySelectorAll('.answer-option').forEach(opt => {
                opt.classList.remove('selected');
            });
            this.classList.add('selected');
            selectedOption = option;
        });
        optionEl.addEventListener('keydown', function (e) {
            if ((e.key === 'Enter' || e.key === ' ') && !answerSubmitted) {
                this.click();
            }
        });
        container.appendChild(optionEl);
    });
}

// Setup true/false question display
function setupTrueFalseQuestion(question) {
    const container = document.querySelector('.true-false-container');
    container.style.display = 'grid';
    container.innerHTML = '';
    selectedOption = null;
    answerSubmitted = false;
    submitAnswerBtn.style.display = 'inline-block';
    nextQuestionBtn.style.display = 'none';
    nextQuestionBtn.disabled = true;

    question.options.forEach(option => {
        const optionEl = document.createElement('div');
        optionEl.className = 'tf-option';
        optionEl.textContent = option;
        optionEl.tabIndex = 0;
        optionEl.addEventListener('click', function () {
            if (answerSubmitted) return;
            document.querySelectorAll('.tf-option').forEach(opt => {
                opt.classList.remove('selected');
            });
            this.classList.add('selected');
            selectedOption = option;
        });
        optionEl.addEventListener('keydown', function (e) {
            if ((e.key === 'Enter' || e.key === ' ') && !answerSubmitted) {
                this.click();
            }
        });
        container.appendChild(optionEl);
    });
}

// Setup written question display
function setupWrittenQuestion() {
    const container = document.querySelector('.written-container');
    container.style.display = 'block';
    const input = container.querySelector('.text-input');
    input.value = '';
    input.placeholder = 'Type your answer';
    input.focus();
    input.select();
    input.classList.remove('correct', 'incorrect');
    input.classList.add('selected');
    selectedOption = null;
    answerSubmitted = false;
    submitAnswerBtn.style.display = 'inline-block';
    nextQuestionBtn.style.display = 'none';
    nextQuestionBtn.disabled = true;
}

// Submit answer handler
submitAnswerBtn.onclick = function () {
    if (answerSubmitted) return;
    const currentItem = quizState.currentRound[quizState.currentQuestionIndex];
    const question = currentItem.question;
    let isCorrect = false;
    if (question.type === 'multipleChoice') {
        if (!selectedOption) return;
        isCorrect = selectedOption === question.correctAnswer;
        // Mark options
        document.querySelectorAll('.answer-option').forEach(opt => {
            if (opt.textContent === selectedOption) {
                opt.classList.add('selected');
            }
            if (opt.textContent === question.correctAnswer) {
                opt.classList.add('correct');
            }
            opt.classList.remove('selected');
        });
    } else if (question.type === 'trueFalse') {
        if (!selectedOption) return;
        isCorrect = selectedOption === question.correctAnswer;
        document.querySelectorAll('.tf-option').forEach(opt => {
            if (opt.textContent === selectedOption) {
                opt.classList.add('selected');
            }
            if (opt.textContent === question.correctAnswer) {
                opt.classList.add('correct');
            }
            opt.classList.remove('selected');
        });
    } else if (question.type === 'written') {
        const inputEl = document.querySelector('.written-container .text-input');
        const userAnswer = inputEl.value.trim();
        const correctAnswer = question.correctAnswer;
        inputEl.classList.add('selected');
        if (quizState.settings.allowTypos) {
            isCorrect = calculateStringSimilarity(userAnswer, correctAnswer) > 0.8;
        } else {
            isCorrect = userAnswer === correctAnswer;
        }
        if (isCorrect) {
            inputEl.classList.add('correct');
        } else {
            inputEl.classList.add('incorrect');
            inputEl.value = question.correctAnswer;
        }
        inputEl.classList.remove('selected');
    }
    currentItem.answered = true;
    currentItem.correct = isCorrect;
    if (isCorrect) quizState.correctAnswers++;
    answerSubmitted = true;
    submitAnswerBtn.style.display = 'none';
    nextQuestionBtn.style.display = 'inline-block';
    nextQuestionBtn.disabled = false;
};

// Allow Enter key to submit or go next
quizContainer.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') {
        if (!answerSubmitted) {
            submitAnswerBtn.click();
        } else if (nextQuestionBtn.style.display !== 'none' && !nextQuestionBtn.disabled) {
            nextQuestionBtn.click();
        }
    }
});

// Next question handler
nextQuestionBtn.addEventListener('click', () => {
    if (!answerSubmitted) return; // Prevent skipping without submit

    // For written questions, reset input state for next question
    if (
        quizState.currentRound[quizState.currentQuestionIndex] &&
        quizState.currentRound[quizState.currentQuestionIndex].question.type === 'written'
    ) {
        const inputEl = document.querySelector('.written-container .text-input');
        if (inputEl) {
            inputEl.classList.remove('correct', 'incorrect', 'selected');
            inputEl.value = '';
        }
    }

    // Move to next question or show results
    quizState.currentQuestionIndex++;

    if (quizState.currentQuestionIndex < quizState.currentRound.length) {
        answerSubmitted = false;
        displayCurrentQuestion();
    } else {
        // End of round, show results
        showResults();
    }
});

// Calculate string similarity (0-1) for typo checking
function calculateStringSimilarity(str1, str2) {
    if (str1 === null || str2 === null) {
        return 0;
    }
    str1 = str1.toLowerCase();
    str2 = str2.toLowerCase();
    if (str1 === str2) {
        return 1;
    }
    const pairs1 = new Set();
    for (let i = 0; i < str1.length - 1; i++) {
        pairs1.add(str1.substring(i, i + 2));
    }
    const pairs2 = new Set();
    for (let i = 0; i < str2.length - 1; i++) {
        pairs2.add(str2.substring(i, i + 2));
    }
    let intersectionSize = 0;
    for (const pair of pairs1) {
        if (pairs2.has(pair)) {
            intersectionSize++;
        }
    }
    return (2 * intersectionSize) / (pairs1.size + pairs2.size);
}

// Exit quiz button
exitQuizBtn.addEventListener('click', () => {
    // Confirm exit
    if (confirm('Are you sure you want to exit? Your progress will be lost.')) {
        goBackToHomeScreen();
    }
});

// Back to set button
backToSetBtn.addEventListener('click', () => {
    goBackToHomeScreen();
});

// New round button
newRoundBtn.addEventListener('click', () => {
    // Hide results
    resultsContainer.style.display = 'none';

    // Show settings modal for a new round
    settingsModal.style.display = 'flex';
});

// Go back to home screen
function goBackToHomeScreen() {
    // Hide quiz and results
    quizContainer.style.display = 'none';
    resultsContainer.style.display = 'none';

    // Update flashcard mastery display
    updateFlashcardMasteryDisplay();

    // Show home screen
    homeScreen.style.display = 'block';
    renderFlashcardCarousel();
    renderFlashcardList();
    // Reset running total for new session
    totalQuestionsAnswered = 0;
    totalQuestionsCount = 0;
}

// Update the flashcard display with new mastery levels
function updateFlashcardMasteryDisplay() {
    const flashcardItems = document.querySelectorAll('.flashcard-item');
    flashcardItems.forEach((item, index) => {
        const card = sets[currentSetName][index];
        const masteryBar = item.querySelector('.mastery-fill');
        const masteryText = item.querySelector('.mastery-indicator');

        masteryBar.style.width = `${card.mastery}%`;
        masteryText.innerHTML = `
             <div class="mastery-bar">
                 <div class="mastery-fill" style="width: ${card.mastery}%;"></div>
             </div>
             ${card.mastery}%
         `;
    });
}

// Utility function to shuffle an array
function shuffleArray(array) {
    const newArray = [...array];
    for (let i = newArray.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [newArray[i], newArray[j]] = [newArray[j], newArray[i]];
    }
    return newArray;
}

// Show results
function showResults() {
    quizContainer.style.display = 'none';
    resultsContainer.style.display = 'block';
    // Update summary
    const summaryEl = document.querySelector('.results-summary');
    const totalQuestions = quizState.currentRound.length;
    const correctQuestions = quizState.currentRound.filter(item => item.correct).length;
    const correctPercentage = totalQuestions > 0 ? Math.round((correctQuestions / totalQuestions) * 100) : 0;
    summaryEl.innerHTML = `
         <p>You answered ${correctQuestions} out of ${totalQuestions} questions correctly.</p>
         <p>Round Accuracy: ${correctPercentage}%</p>
     `;
    // Update term mastery list
    const termResultsEl = document.querySelector('.term-results');
    termResultsEl.innerHTML = '<h3>Term Mastery:</h3>';
    // Calculate and display mastery for each term
    const termMastery = {};
    quizState.currentRound.forEach(item => {
        const term = item.card.term;
        if (!termMastery[term]) {
            termMastery[term] = {
                card: item.card,
                correct: 0,
                total: 0,
                questionTypes: []
            };
        }
        termMastery[term].total++;
        if (item.correct) {
            termMastery[term].correct++;
            termMastery[term].questionTypes.push(item.question.type);
        }
    });
    for (const [term, data] of Object.entries(termMastery)) {
        // Mastery increment logic
        let masteryGain = 0;
        data.questionTypes.forEach(type => {
            if (type === 'trueFalse') masteryGain += 10;
            else if (type === 'multipleChoice') masteryGain += 20;
            else if (type === 'written') masteryGain += 30;
        });
        // Cap at 100
        data.card.mastery = Math.min(100, (data.card.mastery || 0) + masteryGain);
        // Create result item
        const resultItem = document.createElement('div');
        resultItem.className = 'term-result-item';
        resultItem.innerHTML = `
             <span>${term}</span>
             <span>${data.card.mastery}% mastery</span>
         `;
        termResultsEl.appendChild(resultItem);
    }
}

// On page load, load sets and render
loadSets();
renderSidebarSets();
renderFlashcardList();
renderFlashcardCarousel();