const handleMatchmakingEvent = (message) => {
    if (message.status === 'success') {
        window.location.replace('/battle/b/' + message['battle_id']);
    }
    else {
        // TODO Handle loop_already_initiated and queue_empty status
    }
};

window.onload = () => {
    const startBattleForm = document.getElementById('start-battle-form');
    const matchmakingLoadingWrapper = document.getElementById('matchmaking-loading-wrapper');
    const csrfToken = getCookie('csrftoken');
    let battleType;

    startBattleForm.addEventListener('submit', (e) => {
        const opponentType = document.getElementById('opponent-type-select').value;

        if (opponentType === 'random') {
            e.preventDefault();
        }

        battleType = document.getElementById('battle-type-select').value;

        fetch('/battle/join?' + new URLSearchParams({
            'battle_type': battleType,
            'opponent_type': opponentType,
        })).then(async (res) => {
            startBattleForm.style.setProperty('display', 'none');
            matchmakingLoadingWrapper.style.setProperty('display', 'block');

            const data = await res.json();
            const positionId = data['position_id'];
            const socket = new WebSocket(`ws://${window.location.host}/ws/matchmaking/${positionId}/`);

            socket.onopen = () => socket.send(JSON.stringify({
                'event': 'matchmaking.ready'
            }));

            socket.onmessage = (e) => {
                const data = JSON.parse(e.data);
                handleMatchmakingEvent(JSON.parse(data.message));
            };
        });
    });

    matchmakingLoadingWrapper.addEventListener('submit', (e) => {
        e.preventDefault();

        fetch('/battle/cancel-matchmaking/', {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken,
            },
            body: JSON.stringify({
                "battle_type": battleType,
            })
        }).then((res) => {
            if (res.status === 200)  {
                startBattleForm.style.setProperty('display', 'flex');
                matchmakingLoadingWrapper.style.setProperty('display', 'none');
            }
        });
    });
};