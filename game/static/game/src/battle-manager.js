const socket = new WebSocket(`ws://${window.location.host}/ws/battle/${battleId}/`);

const handleBattleEvent = (message) => {
    switch (message.detail) {
        case 'competitor_joined':
            if (message.competitor_number === 2 && competitorNumber === 1) {
                window.location.reload();
            }
            break;
        case 'score_update':
            break;
    }
}

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