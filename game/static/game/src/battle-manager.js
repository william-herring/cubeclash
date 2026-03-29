let scrambleText;
let scrambleDisplay;
let timerText;
let actionHintText;
let solveNoLabel;
let competitorNumber;
let comp1MatchScore, comp2MatchScore = 0;
let comp1SetScore, comp2SetScore = 0;
let comp1Times = [];
let comp2Times = [];
let scramble;
let inspecting = false;
let timing = false;
let inspectionTime = 16.0;
let time = 0.0;
let currentPenalty = 0;

const updateScramble = (newScramble) => {
    scrambleText.innerHTML = newScramble;
    scrambleDisplay.setAttribute('scramble', newScramble);
}

const getResultText = (result) => {
    let suffix = "";

    if (result < 0) {
        if (result === -1) {
            return "DNF";
        } else if (result === -2) {
            return "DNS";
        } else {
            suffix = "+"
            result = Math.abs(result);
        }
    }

    if (result < 60) {
        return result.toFixed(2).padStart(1, '0') + suffix;
    } else {
        const minutes = String(Math.floor(result / 60)).padStart(1, '0');
        const seconds = (result % 60).toFixed(1).padStart(4, '0');
        return minutes + ':' + seconds + suffix;
    }
}

const updateScoresHTML = () => {
    const resultsTable = document.getElementById('results-table');
    const userSetScoreLabel = document.getElementById('user-set-score');
    const opponentSetScoreLabel = document.getElementById('opponent-set-score');
    let rowsToAppend = '';

    if (competitorNumber === 1) {
        userSetScoreLabel.innerHTML = comp1SetScore;
        opponentSetScoreLabel.innerHTML = comp2SetScore;
        for (let i = comp1Times.length - 1; i >= 0; i--) {
            const c1 = parseFloat(comp1Times[i]);
            const c2 = parseFloat(comp2Times[i]);
            rowsToAppend += `<tr><td>${i + 1}</td><td ${c1 < c2 ? 'class="text-green"' : ''}>${comp1Times[i]}</td><td ${c2 < c1 ? 'class="text-green"' : ''}>${comp2Times[i]}</td></tr>`;
        }
    } else {
        userSetScoreLabel.innerHTML = comp2SetScore;
        opponentSetScoreLabel.innerHTML = comp1SetScore;
        for (let i = comp1Times.length - 1; i >= 0; i--) {
            const c1 = parseFloat(comp1Times[i]);
            const c2 = parseFloat(comp2Times[i]);
            rowsToAppend += `<tr><td>${i + 1}</td><td ${c2 < c1 ? 'class="text-green"' : ''}>${comp2Times[i]}</td><td ${c1 < c2 ? 'class="text-green"' : ''}>${comp1Times[i]}</td></tr>`;
        }
    }

    const tableContent = document.getElementById('results-table-headings').outerHTML;
    resultsTable.innerHTML = tableContent + rowsToAppend;
}

const handleBattleEvent = (message) => {
    switch (message.detail) {
        case 'competitor_joined':
            if (message.competitor_number === 2 && competitorNumber === 1) {
                window.location.reload();
            }
            break;
        case 'score_update':
            comp1Times.push(getResultText(message.competitor_1_latest_result, message.competitor_1_latest_result));
            comp2Times.push(getResultText(message.competitor_2_latest_result, message.competitor_2_latest_result));
            comp1SetScore = message.competitor_1_score;
            comp2SetScore = message.competitor_2_score;
            updateScoresHTML();
            break;
        case 'scramble':
            scramble = message.scramble;
            updateScramble(scramble);
            timing = false;
            inspectionTime = 16.0;
            currentPenalty = 0;
            time = 0.0;
            actionHintText.innerHTML = "Space bar to begin inspection";
            solveNoLabel.innerHTML = "Solve " + (comp1Times.length + 1);
            break;
        case 'end_set':
            break;
        case 'end_match':
            break;
    }
}

const inspectionCountdown = () => {
    if (!inspecting) return;

    inspectionTime -= 0.01;

    if (inspectionTime < 1) {
        if (inspectionTime > -1) {
            currentPenalty = 2;
            timerText.innerHTML = "+2";
        } else {
            currentPenalty = -1;
            timerText.innerHTML = "DNF";
        }
    } else {
        timerText.innerHTML = inspectionTime | 0;
    }
}

const timer = () => {
    if (!timing) return;

    time += 0.01;
    if (time < 60) {
        timerText.innerHTML = time.toFixed(1).padStart(1, '0');
    } else {
        const minutes = String(Math.floor(time / 60)).padStart(1, '0');
        const seconds = (time % 60).toFixed(1).padStart(4, '0');
        timerText.innerHTML = minutes + ':' + seconds;
    }
}

window.onload = () => {
    const battleId = JSON.parse(document.getElementById('battleId').textContent);
    const socket = new WebSocket(`ws://${window.location.host}/ws/battle/${battleId}/`);
    let timerInterval;
    let inspectionInterval;
    scramble = JSON.parse(document.getElementById('currentScramble').textContent);
    competitorNumber = JSON.parse(document.getElementById('competitorNumber').textContent)
    scrambleText = document.getElementById('scramble-text');
    scrambleDisplay = document.getElementById('scramble-display');
    timerText = document.getElementById('timer-text');
    actionHintText = document.getElementById('timer-action-hint-text');
    solveNoLabel = document.getElementById('solve-number-text');


    socket.onopen = () => socket.send(
        JSON.stringify({
            'event': 'battle.join',
            'message': {
                'competitor_number': competitorNumber,
            },
        })
    );

    socket.onmessage = (e) => {
        const data = JSON.parse(e.data);
        handleBattleEvent(JSON.parse(data.message));
    }

    document.addEventListener('keydown', (e) => {
        const keyInput = e.code;

        if (keyInput === 'Space') {
            if (time > 0 && timing) {
                timing = false;

                if (currentPenalty > 0) {
                    time = 0 - (time + currentPenalty);
                } else if (currentPenalty < 0) {
                    time = currentPenalty;
                }

                timerText.innerHTML = getResultText(time);

                clearInterval(timerInterval);
                actionHintText.innerHTML = "Waiting for opponent";

                socket.send(
                    JSON.stringify({
                        'event': 'battle.submit',
                        'message': {
                            'competitor_number': competitorNumber,
                            'time': time.toFixed(2),
                        }
                    })
                );
            } else if (!timing) {
                timerText.classList.remove('text-red');
                timerText.classList.add('text-green');
            }
        }
    })

    document.addEventListener('keyup', (e) => {
        const keyInput = e.code;

        if (keyInput === 'Space') {
            if (inspectionTime === 16) {
                inspecting = true;
                timerText.classList.remove('text-green');
                timerText.classList.add('text-red');
                actionHintText.innerHTML = "Inspecting";
                inspectionInterval = setInterval(inspectionCountdown, 10);
            } else if (time === 0) {
                inspecting = false;
                timing = true;
                timerText.classList.remove('text-green');
                timerText.classList.remove('text-red');
                actionHintText.innerHTML = "Timing";
                clearInterval(inspectionInterval);
                timerInterval = setInterval(timer, 10);
            }
        }
    })
}