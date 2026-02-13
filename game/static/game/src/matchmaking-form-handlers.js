const startBattleForm = document.getElementById('start-battle-form');

const handleMatchmakingEvent = (message) => {
    if (message.status === 'success') {
        window.location.replace('/battle/' + message['battle_id']);
    }
    else {
        // TODO Handle loop_already_initiated and queue_empty status
        console.log(message.status);
    }
}

startBattleForm.addEventListener('submit', (e) => {
    e.preventDefault();

    const battleType = document.getElementById('battle-type-select').value;
    const opponentType = document.getElementById('opponent-type-select').value;

    fetch('battle/join/' + new URLSearchParams({
        'battle_type': battleType,
        'opponent_type': opponentType,
    })).then(async (res) => {
        const data = await res.json();

        if (opponentType === 'random') {
            const positionId = data['position_id'];
            const socket = new WebSocket(`ws://${window.location.host}/ws/matchmaking/${positionId}/`);

            socket.send(JSON.stringify({
                'event': 'matchmaking.ready'
            }));

            socket.onmessage = (e) => {
                const messageData = JSON.parse(e.data).message;
                console.log('Matchmaking: ' + e.data);
                handleMatchmakingEvent(messageData);
            };
        }
    });
})