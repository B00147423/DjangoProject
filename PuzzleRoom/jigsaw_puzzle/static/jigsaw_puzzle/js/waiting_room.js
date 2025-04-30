document.addEventListener('DOMContentLoaded', () => {
    // Extract variables from the context
    const roomId = context.room.id;
    const playerRole = context.player_role;
    const redirectUrl = context.redirect_url;

    // Initialize WebSocket
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const socket = new WebSocket(`${protocol}://${window.location.host}/ws/puzzle/${roomId}/`);
    let isReady = false;

    socket.onmessage = function (event) {
        const data = JSON.parse(event.data);

        if (data.type === 'player_ready') {
            const statusMessage = document.getElementById('statusMessage');
            if (data.player_role === 'player1') {
                statusMessage.innerText = `Player 1 is ${data.is_ready ? "ready" : "not ready"}`;
            } else if (data.player_role === 'player2') {
                statusMessage.innerText = `Player 2 is ${data.is_ready ? "ready" : "not ready"}`;
            }
        } else if (data.type === 'both_ready') {
            document.getElementById('statusMessage').innerText = 'Both players are ready. Redirecting...';
            setTimeout(() => {
                window.location.href = redirectUrl;
            }, 2000);
        }
    };

    window.toggleReady = function() {
        isReady = !isReady;
        socket.send(JSON.stringify({
            type: 'player_ready',
            player_role: playerRole,
            is_ready: isReady,
        }));
    };
});
