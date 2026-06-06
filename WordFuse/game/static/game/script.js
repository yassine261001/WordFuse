//CSRF helper
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

function post(url, data) {
    return fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify(data),
    }).then(r => r.json());
}

//UI helpers
function showSection(id) {
    ['auth-section', 'game-section', 'leaderboard-section'].forEach(s => {
        document.getElementById(s).style.display = 'none';
    });
    document.getElementById(id).style.display = 'block';
}

function showTab(tab) {
    document.getElementById('login-form').style.display = tab === 'login' ? 'flex' : 'none';
    document.getElementById('register-form').style.display = tab === 'register' ? 'flex' : 'none';
    document.getElementById('tab-login').classList.toggle('active', tab === 'login');
    document.getElementById('tab-register').classList.toggle('active', tab === 'register');
}

function showGame() { showSection('game-section'); }
function showLeaderboard() {
    showSection('leaderboard-section');
    loadLeaderboard();
}

//Auth
async function handleLogin() {
    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value.trim();
    const data = await post('/auth/login/', { username, password });
    if (data.error) {
        document.getElementById('login-error').textContent = data.error;
    } else {
        onLoggedIn(data.username);
    }
}

async function handleRegister() {
    const username = document.getElementById('reg-username').value.trim();
    const password = document.getElementById('reg-password').value.trim();
    const data = await post('/auth/register/', { username, password });
    if (data.error) {
        document.getElementById('reg-error').textContent = data.error;
    } else {
        onLoggedIn(data.username);
    }
}

async function handleLogout() {
    await post('/auth/logout/', {});
    location.reload();
}

function onLoggedIn(username) {
    document.getElementById('welcome-msg').textContent = `Hello, ${username}`;
    showSection('game-section');
}

//Game state
let score = 0;
let lives = 3;
let currentSyllable = '';
let sessionId = null;
let timerInterval = null;
let timeLeft = 15;
let gameActive = false;

function resetGameUI() {
    score = 0;
    lives = 3;
    updateScoreUI();
    updateLivesUI();
    document.getElementById('game-message').textContent = '';
    document.getElementById('word-input').value = '';
    document.getElementById('syllable-display').textContent = '—';
    document.getElementById('timer-text').textContent = '15';
}

function updateScoreUI() {
    document.getElementById('score-display').textContent = `Score: ${score}`;
}

function updateLivesUI() {
    document.getElementById('lives-display').textContent = 'Lives: ' + '❤️'.repeat(lives);
}

//Timer (with change color)
function startTimer() {

    clearInterval(timerInterval);
    timeLeft = 15;

    const timerWrap = document.getElementById('timer-wrap');
    const timerText = document.getElementById('timer-text');

    timerWrap.className = '';
    timerText.textContent = timeLeft;

    timerInterval = setInterval(() => {

        timeLeft--;
        timerText.textContent = timeLeft;

        if (timeLeft <= 5) {
            timerWrap.className = 'danger';
        } else if (timeLeft <= 10) {
            timerWrap.className = 'warning';
        }
        if (timeLeft <= 0) {
            clearInterval(timerInterval);
            handleTimeout();
        }
    }, 1000);
}

async function handleTimeout() {
    const data = await post('/game/timeout/', { session_id: sessionId, lives: lives });
    lives = data.lives;
    updateLivesUI();

    document.getElementById('game-message').textContent = '⏰ Time up!';

    if (data.game_over) {
        endGame(data.score);
    } else {
        currentSyllable = data.syllable;
        document.getElementById('syllable-display').textContent = currentSyllable;
        startTimer();
    }
}

//Game flow
async function startGame() {
    resetGameUI();
    const data = await post('/game/start/', {});
    if (data.error) {
        document.getElementById('game-message').textContent = data.error;
        return;
    }
    sessionId = data.session_id;
    currentSyllable = data.syllable;
    document.getElementById('syllable-display').textContent = currentSyllable;
    document.getElementById('start-btn').style.display = 'none';
    document.getElementById('word-input').disabled = false;
    document.getElementById('submit-btn').disabled = false;
    gameActive = true;
    startTimer();
}

async function submitWord() {
    if (!gameActive) return;
    const word = document.getElementById('word-input').value.trim();
    if (!word) return;

    clearInterval(timerInterval);
    document.getElementById('word-input').value = '';
    document.getElementById('game-message').textContent = '⏳ Checking...';

    const timeTaken = (15 - timeLeft) * 1000;
    const data = await post('/game/submit/', { session_id: sessionId, word, lives, time_ms: timeTaken });
    
    if (data.already_used) {
        document.getElementById('game-message').textContent = `⚠️ "${word}" already used this session!`;
        document.getElementById('word-input').value = '';
        startTimer();
        return;
    }
    if (data.valid) {
        score = data.score;
        updateScoreUI();
        document.getElementById('game-message').textContent = `✅ "${word}" — +${data.points} pts`;
    } else {
        lives = data.lives;
        updateLivesUI();
        document.getElementById('game-message').textContent = `❌ "${word}" is not valid`;
    }

    if (data.achievements && data.achievements.length > 0) {
        data.achievements.forEach(name => showAchievementPopup(name));
    }

    if (data.game_over) {
        endGame(data.score);
        return;
    }

    currentSyllable = data.syllable;
    document.getElementById('syllable-display').textContent = currentSyllable;
    startTimer();
}

function endGame(finalScore) {
    gameActive = false;
    clearInterval(timerInterval);
    document.getElementById('syllable-display').textContent = '—';
    document.getElementById('timer-text').textContent = '—';
    document.getElementById('word-input').disabled = true;
    document.getElementById('submit-btn').disabled = true;
    document.getElementById('start-btn').style.display = 'inline-block';
    document.getElementById('game-message').textContent = `Game over! Final score: ${finalScore}`;
}

//Leaderboard
async function loadLeaderboard() {
    const data = await fetch('/game/leaderboard/').then(r => r.json());
    const tbody = document.getElementById('leaderboard-body');
    tbody.innerHTML = '';
    data.leaderboard.forEach((entry, i) => {
        const row = document.createElement('tr');
        row.innerHTML = `<td>${i + 1}</td><td>${entry.username}</td><td>${entry.best_score}</td>`;
        tbody.appendChild(row);
    });
}

//On page load
window.addEventListener('load', async () => {
    const data = await fetch('/auth/status/').then(r => r.json());
    if (data.logged_in) {
        onLoggedIn(data.username);
    }

    document.getElementById('word-input').addEventListener('keydown', e => {
        if (e.key === 'Enter') submitWord();
    });
});

function showAchievementPopup(name) {
    const popup = document.getElementById('achievement-popup');
    document.getElementById('achievement-popup-text').textContent = `🏆 ${name}`;
    popup.classList.add('show');
    setTimeout(() => popup.classList.remove('show'), 3000);
}

// animation bar for timer
function startTimer() {
    clearInterval(timerInterval);
    timeLeft = 15;
    const timerWrap = document.getElementById('timer-wrap');
    const timerText = document.getElementById('timer-text');
    const barFill = document.getElementById('timer-bar-fill');

    barFill.style.transition = 'none';
    barFill.style.width = '100%';
    barFill.className = '';
    timerWrap.className = '';
    timerText.textContent = timeLeft;

    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            barFill.style.transition = 'width 15s linear';
            barFill.style.width = '0%';
        });
    });

    timerInterval = setInterval(() => {
        timeLeft--;
        timerText.textContent = timeLeft;
        if (timeLeft <= 5) {
            timerWrap.className = 'danger';
            barFill.className = 'danger';
        } else if (timeLeft <= 10) {
            timerWrap.className = 'warning';
            barFill.className = 'warning';
        }
        if (timeLeft <= 0) {
            clearInterval(timerInterval);
            handleTimeout();
        }
    }, 1000);
}

function openTutorial() {
    document.getElementById('tutorial-overlay').style.display = 'flex';
}

function closeTutorial() {
    document.getElementById('tutorial-overlay').style.display = 'none';
}