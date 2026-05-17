// Game Constants & Configuration
const NUM_DECKS = 6;
const PENETRATION = 0.75;
const BLACKJACK_PAYOUT = 1.5; // 3:2
const WIN_PAYOUT = 1;         // 1:1
const INSURANCE_PAYOUT = 2;   // 2:1

const SUITS = ['♠', '♥', '♦', '♣'];
const RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A'];

// Game State
let shoe = [];
let runningCount = 0;
let trueCount = 0;
let balance = 1000;
let currentBet = 0;

let dealerHand = { cards: [], score: 0, isSoft: false, hasBlackjack: false };
let playerHands = []; // Array of objects { cards: [], bet: 0, score: 0, isSoft: false, isBusted: false, hasBlackjack: false, isStood: false, canDouble: true, canSplit: false, surrendered: false, isFromSplitAces: false }
let currentHandIndex = 0;

let insuranceBet = 0;
let gameDataForAI = null;
let playerActionHistory = []; // Array of actions for the AI

// DOM Elements
const balanceDisplay = document.getElementById('balanceDisplay');
const currentBetDisplay = document.getElementById('currentBetDisplay');
const dealBtn = document.getElementById('dealBtn');
const bettingControls = document.getElementById('bettingControls');
const actionControls = document.getElementById('actionControls');
const insuranceControls = document.getElementById('insuranceControls');
const aiReviewContainer = document.getElementById('aiReviewContainer');
const gameMessage = document.getElementById('gameMessage');

const dealerCardsDiv = document.getElementById('dealerCards');
const dealerScoreDiv = document.getElementById('dealerScore');
const dealerScoreVal = document.getElementById('dealerScoreVal');
const playersAreaDiv = document.getElementById('playersArea');

// Buttons
const hitBtn = document.getElementById('hitBtn');
const standBtn = document.getElementById('standBtn');
const doubleBtn = document.getElementById('doubleBtn');
const splitBtn = document.getElementById('splitBtn');
const surrenderBtn = document.getElementById('surrenderBtn');

// --- Retro Audio Synthesizer ---
class RetroAudio {
    constructor() {
        this.ctx = new (window.AudioContext || window.webkitAudioContext)();
    }

    // "Thwack" (Short white noise burst with quick decay)
    playDeal() {
        if (this.ctx.state === 'suspended') this.ctx.resume();
        const bufferSize = this.ctx.sampleRate * 0.1; // 100ms
        const buffer = this.ctx.createBuffer(1, bufferSize, this.ctx.sampleRate);
        const data = buffer.getChannelData(0);
        for (let i = 0; i < bufferSize; i++) {
            data[i] = Math.random() * 2 - 1; // White noise
        }

        const noiseSource = this.ctx.createBufferSource();
        noiseSource.buffer = buffer;

        // Lowpass filter to make it a "thwack" instead of harsh static
        const filter = this.ctx.createBiquadFilter();
        filter.type = 'lowpass';
        filter.frequency.setValueAtTime(1000, this.ctx.currentTime);
        filter.frequency.exponentialRampToValueAtTime(100, this.ctx.currentTime + 0.1);

        const gainNode = this.ctx.createGain();
        gainNode.gain.setValueAtTime(0.5, this.ctx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, this.ctx.currentTime + 0.1);

        noiseSource.connect(filter);
        filter.connect(gainNode);
        gainNode.connect(this.ctx.destination);
        noiseSource.start();
    }

    // "Crackle" (Low-bitrate rhythmic shuffle)
    playShuffle() {
        if (this.ctx.state === 'suspended') this.ctx.resume();
        const duration = 0.5;
        const bufferSize = this.ctx.sampleRate * duration;
        const buffer = this.ctx.createBuffer(1, bufferSize, this.ctx.sampleRate);
        const data = buffer.getChannelData(0);

        for (let i = 0; i < bufferSize; i++) {
            // Simulate bit-crushed crackle by dropping samples
            if (Math.random() > 0.9) {
                data[i] = (Math.random() * 2 - 1) * 0.5;
            } else {
                data[i] = 0;
            }
        }

        const source = this.ctx.createBufferSource();
        source.buffer = buffer;
        source.connect(this.ctx.destination);
        source.start();
    }

    // "Win" (Polyphonic 2-note synth swell)
    playWin() {
        if (this.ctx.state === 'suspended') this.ctx.resume();
        const t = this.ctx.currentTime;

        // Note 1 (E4)
        const osc1 = this.ctx.createOscillator();
        osc1.type = 'sine';
        osc1.frequency.setValueAtTime(329.63, t);

        // Note 2 (G#4)
        const osc2 = this.ctx.createOscillator();
        osc2.type = 'sine';
        osc2.frequency.setValueAtTime(415.30, t);

        const gainNode = this.ctx.createGain();
        gainNode.gain.setValueAtTime(0, t);
        gainNode.gain.linearRampToValueAtTime(0.3, t + 0.3); // Swell up
        gainNode.gain.exponentialRampToValueAtTime(0.01, t + 1.5); // Fade out

        osc1.connect(gainNode);
        osc2.connect(gainNode);
        gainNode.connect(this.ctx.destination);

        osc1.start(t);
        osc2.start(t);
        osc1.stop(t + 1.5);
        osc2.stop(t + 1.5);
    }

    // "Bust" (Low-frequency square wave buzz with pitch drop)
    playBust() {
        if (this.ctx.state === 'suspended') this.ctx.resume();
        const t = this.ctx.currentTime;

        const osc = this.ctx.createOscillator();
        osc.type = 'square';
        osc.frequency.setValueAtTime(150, t);
        osc.frequency.exponentialRampToValueAtTime(50, t + 0.5); // Pitch drop

        const filter = this.ctx.createBiquadFilter();
        filter.type = 'lowpass';
        filter.frequency.setValueAtTime(500, t);

        const gainNode = this.ctx.createGain();
        gainNode.gain.setValueAtTime(0.3, t);
        gainNode.gain.exponentialRampToValueAtTime(0.01, t + 0.5);

        osc.connect(filter);
        filter.connect(gainNode);
        gainNode.connect(this.ctx.destination);

        osc.start(t);
        osc.stop(t + 0.5);
    }
}

const audio = new RetroAudio();

// --- Card & Shoe Logic ---

function createShoe() {
    shoe = [];
    runningCount = 0;
    for (let d = 0; d < NUM_DECKS; d++) {
        for (let s = 0; s < SUITS.length; s++) {
            for (let r = 0; r < RANKS.length; r++) {
                shoe.push({ suit: SUITS[s], rank: RANKS[r] });
            }
        }
    }
    shuffleShoe();
}

function shuffleShoe() {
    for (let i = shoe.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [shoe[i], shoe[j]] = [shoe[j], shoe[i]];
    }
    audio.playShuffle();
}

function getCardValue(rank) {
    if (['J', 'Q', 'K'].includes(rank)) return 10;
    if (rank === 'A') return 11;
    return parseInt(rank);
}

function updateHiLoCount(card) {
    const val = getCardValue(card.rank);
    if (val >= 2 && val <= 6) runningCount += 1;
    else if (val >= 10 || val === 11) runningCount -= 1;

    const decksRemaining = Math.max(1, shoe.length / 52);
    trueCount = Math.floor(runningCount / decksRemaining);
    // Note: True count and running count are intentionally NOT displayed on UI
}

let cardIdCounter = 0; // Unique ID for cards to track animation

function drawCard() {
    if (shoe.length < (NUM_DECKS * 52 * (1 - PENETRATION))) {
        createShoe();
        showMessage("Shuffling Shoe...", 1500);
    }
    const card = shoe.pop();
    card.id = cardIdCounter++; // Assign unique ID for animation tracking
    updateHiLoCount(card);
    audio.playDeal();
    return card;
}

function calculateScore(cards) {
    let score = 0;
    let aces = 0;
    for (let card of cards) {
        let val = getCardValue(card.rank);
        if (val === 11) {
            aces += 1;
        }
        score += val;
    }

    let isSoft = false;
    while (score > 21 && aces > 0) {
        score -= 10;
        aces -= 1;
    }
    if (aces > 0 && score <= 21) {
        isSoft = true;
    }

    return { score, isSoft };
}

// --- UI Rendering ---

// Global set to track which cards have already been animated
const animatedCards = new Set();

function renderCard(card, isHidden = false, animateDeal = false) {
    const container = document.createElement('div');
    container.className = `card-container ${isHidden ? 'flipped' : ''}`;

    // Only animate if requested and not animated before
    if (animateDeal && !animatedCards.has(card.id)) {
        container.classList.add('card-dealt');
        animatedCards.add(card.id);
    }

    const inner = document.createElement('div');
    inner.className = 'card-inner';

    // Front of the card
    const front = document.createElement('div');
    front.className = 'card-front';
    const isRed = card.suit === '♥' || card.suit === '♦';
    front.classList.add(isRed ? 'card-red' : 'card-black');
    front.innerHTML = `
        <div class="rank-top-left">${card.rank}</div>
        <div class="suit-center">${card.suit}</div>
        <div class="rank-bottom-right">${card.rank}</div>
    `;

    // Back of the card
    const back = document.createElement('div');
    back.className = 'card-back';

    inner.appendChild(front);
    inner.appendChild(back);
    container.appendChild(inner);

    return container;
}

function updateUI(hideDealerDownCard = true) {
    balanceDisplay.innerText = balance.toFixed(2);
    currentBetDisplay.innerText = currentBet;

    // Render Dealer
    dealerCardsDiv.innerHTML = '';
    dealerHand.cards.forEach((card, index) => {
        if (index === 1 && hideDealerDownCard) {
            dealerCardsDiv.appendChild(renderCard(card, true, true)); // Request animation, set will filter
        } else {
            dealerCardsDiv.appendChild(renderCard(card, false, true)); // Request animation, set will filter
        }
    });

    if (hideDealerDownCard) {
        dealerScoreDiv.classList.add('hidden');
    } else {
        dealerScoreDiv.classList.remove('hidden');
        dealerScoreVal.innerText = dealerHand.score + (dealerHand.isSoft ? " (Soft)" : "");
    }

    // Render Players
    playersAreaDiv.innerHTML = '';
    playerHands.forEach((hand, index) => {
        const handDiv = document.createElement('div');
        handDiv.className = `hand-container flex flex-col items-center ${index === currentHandIndex ? 'hand-active' : ''}`;

        const cardsDiv = document.createElement('div');
        cardsDiv.className = 'flex justify-center mb-2';
        hand.cards.forEach((card) => {
            cardsDiv.appendChild(renderCard(card, false, true)); // Request animation, set will filter
        });
        handDiv.appendChild(cardsDiv);

        let statusText = `Bet: $${hand.bet} | Score: ${hand.score}`;
        if (hand.isSoft) statusText += " (Soft)";
        if (hand.isBusted) statusText += " - BUST!";
        if (hand.surrendered) statusText += " - SURRENDERED";
        if (hand.hasBlackjack) statusText += " - BLACKJACK!";

        const statusDiv = document.createElement('div');
        statusDiv.className = 'text-sm font-mono text-gray-200';
        statusDiv.innerText = statusText;
        handDiv.appendChild(statusDiv);

        playersAreaDiv.appendChild(handDiv);
    });

    updateActionButtons();
}

function updateActionButtons() {
    if (playerHands.length === 0 || currentHandIndex >= playerHands.length) {
        actionControls.classList.add('hidden');
        return;
    }

    const hand = playerHands[currentHandIndex];

    hitBtn.disabled = hand.isBusted || hand.isStood || hand.surrendered || hand.score >= 21 || hand.isFromSplitAces;
    standBtn.disabled = hand.isBusted || hand.isStood || hand.surrendered;

    // Double Down: Any initial 2 cards (including after split, unless split aces)
    doubleBtn.disabled = hand.cards.length !== 2 || balance < hand.bet || hand.isFromSplitAces;

    // Split: 2 cards of same rank/value, max 4 hands
    const canSplitValue = hand.cards.length === 2 && (getCardValue(hand.cards[0].rank) === getCardValue(hand.cards[1].rank));
    splitBtn.disabled = !canSplitValue || playerHands.length >= 4 || balance < hand.bet;

    // Surrender: Only on first 2 cards of initial hand (late surrender after dealer checks BJ handled in logic)
    surrenderBtn.disabled = playerHands.length > 1 || hand.cards.length !== 2;
}

function showMessage(msg, duration = 0) {
    gameMessage.innerText = msg;
    gameMessage.classList.remove('hidden');
    if (duration > 0) {
        setTimeout(() => {
            gameMessage.classList.add('hidden');
        }, duration);
    }
}

// --- Game Actions ---

function placeBet(amount) {
    if (balance >= amount) {
        balance -= amount;
        currentBet += amount;
        balanceDisplay.innerText = balance.toFixed(2);
        currentBetDisplay.innerText = currentBet;
        dealBtn.disabled = false;
    }
}

function clearBet() {
    balance += currentBet;
    currentBet = 0;
    balanceDisplay.innerText = balance.toFixed(2);
    currentBetDisplay.innerText = currentBet;
    dealBtn.disabled = true;
}

async function dealInitialCards() {
    if (shoe.length === 0) createShoe();

    // Clear animation tracking set for new round
    animatedCards.clear();

    gameMessage.classList.add('hidden');
    bettingControls.classList.add('hidden');
    aiReviewContainer.classList.add('hidden');
    playerActionHistory = [];
    insuranceBet = 0;

    dealerHand = { cards: [], score: 0, isSoft: false, hasBlackjack: false };
    playerHands = [{
        cards: [], bet: currentBet, score: 0, isSoft: false,
        isBusted: false, hasBlackjack: false, isStood: false,
        surrendered: false, isFromSplitAces: false
    }];
    currentHandIndex = 0;

    // Deal alternating
    playerHands[0].cards.push(drawCard());
    dealerHand.cards.push(drawCard());
    playerHands[0].cards.push(drawCard());
    dealerHand.cards.push(drawCard()); // hidden card

    // Calculate initial scores
    const pScore = calculateScore(playerHands[0].cards);
    playerHands[0].score = pScore.score;
    playerHands[0].isSoft = pScore.isSoft;

    const dScore = calculateScore(dealerHand.cards);
    dealerHand.score = dScore.score;
    dealerHand.isSoft = dScore.isSoft;

    if (playerHands[0].score === 21) {
        playerHands[0].hasBlackjack = true;
    }
    if (dealerHand.score === 21) {
        dealerHand.hasBlackjack = true;
    }

    updateUI(true);

    // Capture initial state for AI Review
    gameDataForAI = {
        dealerUpcard: dealerHand.cards[0].rank,
        playerInitialCards: [playerHands[0].cards[0].rank, playerHands[0].cards[1].rank],
        trueCount: trueCount,
        actions: []
    };

    // Insurance check
    if (dealerHand.cards[0].rank === 'A') {
        if (balance >= currentBet / 2) {
            insuranceControls.classList.remove('hidden');
            return; // Wait for insurance decision
        }
    }

    checkDealerBlackjack();
}

function handleInsurance(wantsInsurance) {
    insuranceControls.classList.add('hidden');
    if (wantsInsurance) {
        insuranceBet = currentBet / 2;
        balance -= insuranceBet;
        showMessage("Insurance Placed", 1000);
    }
    setTimeout(checkDealerBlackjack, 1000);
}

function checkDealerBlackjack() {
    if (dealerHand.hasBlackjack) {
        updateUI(false); // Reveal dealer card
        if (insuranceBet > 0) {
            balance += insuranceBet + (insuranceBet * INSURANCE_PAYOUT);
            showMessage("Dealer has Blackjack. Insurance pays 2:1.", 2000);
            audio.playWin();
        }

        if (playerHands[0].hasBlackjack) {
            // Return original bet on push
            balance += playerHands[0].bet;
            setTimeout(() => resolveGame("Push! Both have Blackjack."), 2000);
        } else {
            setTimeout(() => resolveGame("Dealer Blackjack. You lose."), 2000);
        }
    } else {
        if (insuranceBet > 0) {
            showMessage("Nobody home. Insurance lost.", 1500);
        }

        if (playerHands[0].hasBlackjack) {
            updateUI(false);
            // Player Blackjack pays 3:2
            balance += playerHands[0].bet + (playerHands[0].bet * BLACKJACK_PAYOUT);
            setTimeout(() => resolveGame("Blackjack! You win 3:2!"), 1500);
        } else {
            // Normal play continues
            actionControls.classList.remove('hidden');
            updateUI(true);
        }
    }
}

function playerAction(action) {
    const hand = playerHands[currentHandIndex];
    gameDataForAI.actions.push(action); // Record for AI

    if (action === 'Hit') {
        hand.cards.push(drawCard());
        const s = calculateScore(hand.cards);
        hand.score = s.score;
        hand.isSoft = s.isSoft;

        if (hand.score > 21) {
            hand.isBusted = true;
            nextHand();
        } else if (hand.score === 21) {
            hand.isStood = true;
            nextHand();
        } else {
            updateUI(true);
        }
    }
    else if (action === 'Stand') {
        hand.isStood = true;
        nextHand();
    }
    else if (action === 'Double') {
        balance -= hand.bet;
        hand.bet *= 2;
        hand.cards.push(drawCard());
        const s = calculateScore(hand.cards);
        hand.score = s.score;
        hand.isSoft = s.isSoft;

        if (hand.score > 21) hand.isBusted = true;
        hand.isStood = true;
        nextHand();
    }
    else if (action === 'Split') {
        balance -= hand.bet;
        const card1 = hand.cards[0];
        const card2 = hand.cards[1];

        const isSplitAces = card1.rank === 'A';

        // Create new hand
        const newHand = {
            cards: [card2], bet: hand.bet, score: 0, isSoft: false,
            isBusted: false, hasBlackjack: false, isStood: false,
            surrendered: false, isFromSplitAces: isSplitAces
        };

        // Update current hand
        hand.cards = [card1];
        hand.isFromSplitAces = isSplitAces;

        playerHands.splice(currentHandIndex + 1, 0, newHand);

        // Deal 1 card to current hand immediately
        hand.cards.push(drawCard());
        const s1 = calculateScore(hand.cards);
        hand.score = s1.score;
        hand.isSoft = s1.isSoft;

        // Deal 1 card to new hand immediately
        newHand.cards.push(drawCard());
        const s2 = calculateScore(newHand.cards);
        newHand.score = s2.score;
        newHand.isSoft = s2.isSoft;

        if (isSplitAces) {
            hand.isStood = true;
            newHand.isStood = true;
            updateUI(true);
            setTimeout(nextHand, 1000); // Move to next hand/dealer
        } else {
            updateUI(true);
            if(hand.score === 21) nextHand();
        }
    }
    else if (action === 'Surrender') {
        hand.surrendered = true;
        // Late surrender pays half bet back
        balance += hand.bet / 2;
        hand.bet = 0; // effectively lost the other half
        nextHand();
    }
}

function nextHand() {
    currentHandIndex++;

    if (currentHandIndex >= playerHands.length) {
        updateUI(true);
        actionControls.classList.add('hidden');
        setTimeout(playDealerTurn, 500);
    } else {
        // Check if the newly focused hand needs to be skipped
        const hand = playerHands[currentHandIndex];
        if (hand.isStood || hand.isBusted || hand.score === 21) {
            hand.isStood = true;
            nextHand(); // recursively move to next
        } else {
            updateUI(true);
        }
    }
}

async function playDealerTurn() {
    // Reveal down card
    updateUI(false);

    // Check if dealer needs to play (did player have any non-busted/non-surrendered hands?)
    let needToPlay = playerHands.some(h => !h.isBusted && !h.surrendered && !h.hasBlackjack);

    if (needToPlay) {
        // Dealer hits on soft 17 or below 17 (Casino rule: Dealer stands on all 17s)
        // Wait, rule specifies "Dealer stands on all 17s (including soft 17)".
        // So dealer hits while score < 17.
        while (dealerHand.score < 17) {
            await new Promise(r => setTimeout(r, 800)); // Delay for visual effect
            dealerHand.cards.push(drawCard());
            const s = calculateScore(dealerHand.cards);
            dealerHand.score = s.score;
            dealerHand.isSoft = s.isSoft;
            updateUI(false);
        }
    }

    setTimeout(resolveGame, 1000);
}

function resolveGame(forcedMessage = null) {
    let resultMsg = forcedMessage;
    let totalWin = 0;

    if (!forcedMessage) {
        const dScore = dealerHand.score;
        const dBust = dScore > 21;

        playerHands.forEach((hand, idx) => {
            if (hand.surrendered) return; // already handled
            if (hand.isBusted) return;    // bet lost

            if (hand.hasBlackjack && !dealerHand.hasBlackjack) {
                // Handled earlier usually, but safety net
                balance += hand.bet + (hand.bet * BLACKJACK_PAYOUT);
                totalWin += hand.bet * BLACKJACK_PAYOUT;
            } else if (dBust) {
                balance += hand.bet * 2;
                totalWin += hand.bet;
            } else if (hand.score > dScore) {
                balance += hand.bet * 2;
                totalWin += hand.bet;
            } else if (hand.score === dScore) {
                balance += hand.bet; // Push
            } else {
                // Lost, do nothing
            }
        });

        if (playerHands.every(h => h.isBusted)) {
            resultMsg = "Player Busts. Dealer Wins.";
            audio.playBust();
        } else if (playerHands.every(h => h.surrendered)) {
            resultMsg = "Player Surrendered.";
            audio.playBust();
        } else if (dBust) {
            resultMsg = `Dealer Busts! You Win!`;
            audio.playWin();
        } else {
            // Calculate if the player won, lost, or pushed overall based on the best non-busted hand
            let hasWon = false;
            let hasLost = true;
            let hasPush = false;

            playerHands.forEach(hand => {
                if (!hand.isBusted && !hand.surrendered) {
                    if (hand.score > dScore) {
                        hasWon = true;
                        hasLost = false;
                    } else if (hand.score === dScore) {
                        hasPush = true;
                        hasLost = false;
                    }
                }
            });

            if (hasWon) {
                resultMsg = `你赢了！ (Dealer has ${dScore})`;
                audio.playWin();
            } else if (hasPush) {
                resultMsg = `平局！ (Dealer has ${dScore})`;
            } else {
                resultMsg = `你输了！ (Dealer has ${dScore})`;
                audio.playBust();
            }
        }
    }

    updateUI(false);
    showMessage(resultMsg);

    currentBet = 0;
    currentBetDisplay.innerText = "0";

    // Show AI Review button and betting controls
    setTimeout(() => {
        aiReviewContainer.classList.remove('hidden');
        bettingControls.classList.remove('hidden');
    }, 1500);
}

function resetGameUI() {
    gameMessage.classList.add('hidden');
    dealerCardsDiv.innerHTML = '';
    dealerScoreDiv.classList.add('hidden');
    playersAreaDiv.innerHTML = '';
    aiReviewContainer.classList.add('hidden');
}

// --- AI Review Feature ---

async function fetchAIReview(gameData) {
    const apiKey = document.getElementById('apiKey').value;
    if (!apiKey) {
        return "Error: Please enter your Gemini API Key in the top right corner.";
    }

    const apiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key=${apiKey}`;

    /*
       System Prompt Structure requested by user:
       "你是一个基于数学概率的21点教练。结合基本策略(Basic Strategy)和当前Hi-Lo真数，评价玩家的操作。请直接输出三点：1. 最优解：期望值最高的操作。2. 应该做：简述为何该操作胜率最高。3. 不该做：玩家实际操作的风险所在。"
    */

    const promptText = `
你是一个基于数学概率的21点教练。结合基本策略(Basic Strategy)和当前Hi-Lo真数，评价玩家的操作。请直接输出三点：
1. 最优解：期望值最高的操作。
2. 应该做：简述为何该操作胜率最高。
3. 不该做：玩家实际操作的风险所在。

当前游戏数据：
- 庄家明牌：${gameData.dealerUpcard}
- 玩家初始手牌：${gameData.playerInitialCards.join(', ')}
- 当前Hi-Lo真数：${gameData.trueCount}
- 玩家实际操作序列：${gameData.actions.join(' -> ') || '无操作(可能直接发到了Blackjack等)'}
    `;

    try {
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                contents: [{
                    parts: [{ text: promptText }]
                }]
            })
        });

        if (!response.ok) {
            let errorMsg = `HTTP error! status: ${response.status}`;
            try {
                const errorData = await response.json();
                console.error("Gemini API Error details:", errorData);
                if (errorData.error && errorData.error.message) {
                    errorMsg += ` - ${errorData.error.message}`;
                }
            } catch (e) {
                // If we can't parse the error JSON, just stick to the status code
            }
            throw new Error(errorMsg);
        }

        const data = await response.json();
        if (data.candidates && data.candidates[0].content.parts[0].text) {
            return data.candidates[0].content.parts[0].text;
        } else {
            return "Error: Unexpected response format from Gemini API.";
        }
    } catch (error) {
        console.error("AI Review Fetch Error:", error);
        return `Error connecting to Gemini API: ${error.message}`;
    }
}

async function requestAIReview() {
    if (!gameDataForAI) return;

    const modal = document.getElementById('aiModal');
    const loading = document.getElementById('aiLoading');
    const content = document.getElementById('aiContent');

    modal.classList.remove('hidden');
    loading.classList.remove('hidden');
    content.innerText = '';

    const reviewText = await fetchAIReview(gameDataForAI);

    loading.classList.add('hidden');
    content.innerText = reviewText;
}

function closeAIModal() {
    document.getElementById('aiModal').classList.add('hidden');
}
