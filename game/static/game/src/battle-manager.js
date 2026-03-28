let scrambleText;
let scrambleDisplay;
let timerText;
let competitorNumber;
let comp1MatchScore, comp2MatchScore = 0;
let comp1SetScore, comp2SetScore = 0;
let comp1Times, comp2Times = [];
let scramble;
let inspecting = false;
let timing = false;
let inspectionTime = 16.00;
let time = 0.00;
let penalty;

const updateScramble = (newScramble) => {
    scrambleText.innerHTML = newScramble;
    scrambleDisplay.setAttribute('scramble', newScramble);
}

const getResultText = () => {
    time += penalty;
    let suffix;

    if (penalty > 0) {
        suffix = "+"
    } else if (penalty === -1) {
        return "DNF";
    } else if (penalty === -2) {
        return "DNS";
    }

    if (time < 60) {
        return time.toFixed(2).padStart(1, '0') + suffix;
    } else {
        const minutes = String(Math.floor(time / 60)).padStart(1, '0');
        const seconds = (time % 60).toFixed(1).padStart(4, '0');
        return minutes + ':' + seconds + suffix;
    }
}

const handleBattleEvent = (message) => {
    switch (message.detail) {
        case 'competitor_joined':
            if (message.competitor_number === 2 && competitorNumber === 1) {
                window.location.reload();
            }
            break;
        case 'score_update':
            break;
        case 'scramble':
            scramble = message.scramble;
            updateScramble(scramble);
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
            penalty = 2;
            timerText.innerHTML = "+2";
        } else {
            penalty = -1;
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
    const actionHintText = document.getElementById('timer-action-hint-text');

    scramble = JSON.parse(document.getElementById('currentScramble').textContent);
    competitorNumber = JSON.parse(document.getElementById('competitorNumber').textContent)
    scrambleText = document.getElementById('scramble-text');
    scrambleDisplay = document.getElementById('scramble-display');
    timerText = document.getElementById('timer-text');

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
            if (time > 0) {
                timing = false;

                timerText.innerHTML = getResultText(); // Applies inspection penalties automatically

                clearInterval(timer);
                actionHintText.innerHTML = "Space bar to begin inspection";

                socket.send(
                    JSON.stringify({
                        'event': 'battle.submit',
                        'message': {
                            'competitor_number': competitorNumber,
                            'time': penalty < 0? penalty : time.toFixed(2),
                        }
                    })
                );
            } else {
                timerText.classList.remove('timer-text-inspection');
                timerText.classList.add('timer-text-ready');
            }
        }
    })

    document.addEventListener('keyup', (e) => {
        const keyInput = e.code;

        if (keyInput === 'Space') {
            if (inspectionTime === 16) {
                inspecting = true;
                timerText.classList.remove('timer-text-ready');
                timerText.classList.add('timer-text-inspection');
                actionHintText.innerHTML = "Inspecting";
                setInterval(inspectionCountdown, 10);
            } else if (time === 0) {
                inspecting = false;
                timing = true;
                timerText.classList.remove('timer-text-ready');
                timerText.classList.remove('timer-text-inspection');
                actionHintText.innerHTML = "Timing";
                clearInterval(inspectionCountdown);
                setInterval(timer, 10);
            }
        }
    })
}