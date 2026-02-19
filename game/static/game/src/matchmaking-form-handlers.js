const handleMatchmakingEvent = (message) => {
    console.log(message['status']);

    if (message.status === 'success') {
        window.location.replace('/battle/go/' + message['battle_id']);
    }
    else {
        // TODO Handle loop_already_initiated and queue_empty status
    }
};

window.onload = () => {
    const startBattleForm = document.getElementById('start-battle-form');

    startBattleForm.addEventListener('submit', (e) => {
        e.preventDefault();

        const battleType = document.getElementById('battle-type-select').value;
        const opponentType = document.getElementById('opponent-type-select').value;

        fetch('/battle/join?' + new URLSearchParams({
            'battle_type': battleType,
            'opponent_type': opponentType,
        })).then(async (res) => {
            const data = await res.json();

            if (opponentType === 'random') {
                const positionId = data['position_id'];
                const socket = new WebSocket(`ws://${window.location.host}/ws/matchmaking/${positionId}/`);

                socket.onopen = () => socket.send(JSON.stringify({
                    'event': 'matchmaking.ready'
                }));

                socket.onmessage = (e) => {
                    const messageData = JSON.parse(e.data).message;
                    console.log('Received: ' + messageData);
                    handleMatchmakingEvent(messageData);
                };
            }
        });
    });
};