
document.addEventListener('DOMContentLoaded', () => {
    const piecesDataElement = document.getElementById('puzzle-data');
    const pieces = JSON.parse(piecesDataElement.textContent);

    let gridRows, gridCols;
    const baseGridSize = 60;
    let selectedPiece = null;
    const placedPieces = {};

    // Set grid dimensions based on difficulty
    if (difficulty === 'easy') {
        gridRows = 4;
        gridCols = 4;
    } else if (difficulty === 'medium') {
        gridRows = 6;
        gridCols = 6;
    } else if (difficulty === 'hard') {
        gridRows = 8;
        gridCols = 8;
    } else {
        // Default
        gridRows = 4;
        gridCols = 4;
    }

    const player1Stage = new Konva.Stage({
        container: 'player1-grid',
        width: baseGridSize * gridCols,
        height: baseGridSize * gridRows,
    });
    const player1Layer = new Konva.Layer();
    player1Stage.add(player1Layer);

    const player2Stage = new Konva.Stage({
        container: 'player2-grid',
        width: baseGridSize * gridCols,
        height: baseGridSize * gridRows,
    });
    const player2Layer = new Konva.Layer();
    player2Stage.add(player2Layer);

    function loadPuzzlePieces(piecesContainerId, piecesData) {
        const piecesContainer = document.getElementById(piecesContainerId);

        if ((playerRole === 'player1' && piecesContainerId === 'player1-pieces') ||
            (playerRole === 'player2' && piecesContainerId === 'player2-pieces')) {

            piecesData.forEach(piece => {
                const pieceElement = document.createElement('div');
                pieceElement.classList.add('piece');
                pieceElement.dataset.pieceId = piece.id;
                pieceElement.style.backgroundImage = `url('${piece.image_url}')`;

                pieceElement.addEventListener('click', () => {
                    if (selectedPiece) selectedPiece.classList.remove('selected');
                    selectedPiece = pieceElement;
                    pieceElement.classList.add('selected');
                });

                if (piece.is_placed) {
                    pieceElement.classList.add('disabled');
                    placedPieces[piece.id] = true;
                }

                piecesContainer.appendChild(pieceElement);
            });
        }
    }

    loadPuzzlePieces('player1-pieces', pieces);
    loadPuzzlePieces('player2-pieces', pieces);

    function createGrid(stage, layer, player) {
        const isPlayerGrid = (player === 'player1' && playerRole === 'player1') ||
                             (player === 'player2' && playerRole === 'player2');

        function setupGrid() {
            layer.destroyChildren();

            const currentGridSize = stage.width() / gridCols;
            for (let i = 0; i < gridCols; i++) {
                for (let j = 0; j < gridRows; j++) {
                    const square = new Konva.Rect({
                        x: i * currentGridSize,
                        y: j * currentGridSize,
                        width: currentGridSize,
                        height: currentGridSize,
                        stroke: 'gray',
                        strokeWidth: 1,
                    });

                    if (isPlayerGrid) {
                        square.on('click', () => {
                            placePiece(square, layer);
                        });
                    }

                    layer.add(square);
                }
            }
            layer.draw();
        }

        setupGrid();
        window.addEventListener('resize', () => {
            Object.entries(placedPieces).forEach(([pieceId, pieceData]) => {
                const currentLayer = playerRole === 'player1' ? player1Layer : player2Layer;
                addPieceToLayer(currentLayer, null, pieceData.x, pieceData.y, pieceId, pieceData.imageUrl);
            });
        });
    }

    createGrid(player1Stage, player1Layer, 'player1');
    createGrid(player2Stage, player2Layer, 'player2');

    // WebSocket setup
    const socket = new WebSocket(`ws://${window.location.host}/ws/puzzle/${roomId}/`);
    let isWebSocketConnected = false;

    socket.onopen = function() {
        console.log('WebSocket connection established');
        isWebSocketConnected = true;
    };
    socket.onclose = function() {
        console.log('WebSocket connection closed');
        isWebSocketConnected = false;
    };

    function sendMove(pieceId, newX, newY, imageUrl) {
        if (!isWebSocketConnected) {
            console.error('WebSocket not connected!');
            return;
        }
        socket.send(JSON.stringify({
            'type': 'piece_move',
            'piece_id': pieceId,
            'new_x': newX,
            'new_y': newY,
            'player_role': playerRole,
            'image_url': imageUrl
        }));
    }

    function placePiece(square, layer) {
        if (selectedPiece && !placedPieces[`${playerRole}_${selectedPiece.dataset.pieceId}`]) {
            const pieceId = selectedPiece.dataset.pieceId;
            const newX = square.x();
            const newY = square.y();
            const pieceImageUrl = selectedPiece.style.backgroundImage.slice(5, -2);

            const imageNode = new Konva.Image({
                x: newX,
                y: newY,
                width: baseGridSize,
                height: baseGridSize,
                image: new Image(),
                id: pieceId
            });

            imageNode.on('contextmenu', (e) => {
                e.evt.preventDefault();
                removePieceFromGrid(pieceId, layer);
            });

            imageNode.setAttr('placed_by', playerRole);
            imageNode.image().src = pieceImageUrl;
            imageNode.image().onload = () => {
                layer.add(imageNode);
                layer.draw();
            };

            sendMove(pieceId, newX, newY, pieceImageUrl);
            placedPieces[`${playerRole}_${pieceId}`] = {
                x: newX,
                y: newY,
                imageUrl: pieceImageUrl
            };

            selectedPiece.classList.add('disabled');
            selectedPiece.classList.remove('selected');
            selectedPiece = null;
        }
    }

    function addPieceToLayer(layer, selectedPiece, x, y, pieceId, imageUrl = null) {
        const imageObj = new Image();
        imageObj.onload = () => {
            const imageNode = new Konva.Image({
                x: x,
                y: y,
                width: baseGridSize,
                height: baseGridSize,
                image: imageObj,
                id: pieceId,
            });
            layer.add(imageNode);
            layer.draw();
        };
        imageObj.onerror = () => {
            console.error('Failed to load piece image');
        };
        const finalImageUrl = imageUrl || (selectedPiece ? selectedPiece.style.backgroundImage.replace(/url\(['"](.+)['"]\)/, '$1') : '');
        imageObj.src = finalImageUrl;
    }

    socket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        console.log('Received WebSocket message:', data);

        if (data.type === 'piece_move') {
            const { piece_id, new_x, new_y, player_role, image_url } = data;
            const targetLayer = player_role === 'player1' ? player1Layer : player2Layer;
            updatePieceOnGrid(targetLayer, piece_id, new_x, new_y, image_url);
            placedPieces[`${player_role}_${piece_id}`] = { x: new_x, y: new_y, imageUrl: image_url };
            const containerSelector = `#${player_role}-pieces [data-piece-id="${piece_id}"]`;
            const pieceElement = document.querySelector(containerSelector);
            if (pieceElement) pieceElement.classList.add('disabled');

        } else if (data.type === 'piece_remove') {
            const { piece_id, player_role } = data;
            const targetLayer = player_role === 'player1' ? player1Layer : player2Layer;
            const piece = targetLayer.findOne(`#${piece_id}`);
            if (piece) {
                piece.destroy();
                targetLayer.draw();
            }
            const containerSelector = `#${player_role}-pieces [data-piece-id="${piece_id}"]`;
            const pieceElement = document.querySelector(containerSelector);
            if (pieceElement) pieceElement.classList.remove('disabled');
            delete placedPieces[`${player_role}_${piece_id}`];

        } else if (data.type === 'init_pieces') {
            data.pieces.forEach(piece => {
                if (piece.is_placed) {
                    const targetLayer = piece.placed_by === 'player1' ? player1Layer : player2Layer;
                    updatePieceOnGrid(targetLayer, piece.id, piece.x, piece.y, piece.image_url);
                    placedPieces[`${piece.placed_by}_${piece.id}`] = { x: piece.x, y: piece.y, imageUrl: piece.image_url };
                    const containerSelector = `#${piece.placed_by}-pieces [data-piece-id="${piece.id}"]`;
                    const pieceElement = document.querySelector(containerSelector);
                    if (pieceElement) pieceElement.classList.add('disabled');
                }
            });

        } else if (data.type === 'both_ready') {
            // Both players ready: start or resume the countdown
            fetch(`/jigsaw/get_remaining_time/${roomId}/`)
                .then(response => response.json())
                .then(data => {
                    startCountdown(data.remaining_time);
                });
        }
    };

    function updatePieceOnGrid(layer, pieceId, newX, newY, imageUrl, isOpponentPiece = false) {
        const existingPiece = layer.findOne(`#${pieceId}`);
        if (existingPiece) {
            existingPiece.x(newX);
            existingPiece.y(newY);
        } else {
            const imageNode = new Konva.Image({
                x: newX,
                y: newY,
                width: baseGridSize,
                height: baseGridSize,
                image: new Image(),
                id: pieceId,
                opacity: isOpponentPiece ? 0.7 : 1,
            });

            imageNode.on('contextmenu', (e) => {
                e.evt.preventDefault();
                if (playerRole === (imageNode.getAttr('placed_by') || playerRole)) {
                    const pieceContainer = document.querySelector(`#${playerRole}-pieces [data-piece-id="${pieceId}"]`);
                    if (pieceContainer) pieceContainer.classList.remove('disabled');
                    
                    imageNode.destroy();
                    layer.draw();
                    const placedKey = `${playerRole}_${pieceId}`;
                    delete placedPieces[placedKey];

                    if (isWebSocketConnected) {
                        socket.send(JSON.stringify({
                            'type': 'piece_remove',
                            'piece_id': pieceId,
                            'player_role': playerRole
                        }));
                    }
                }
            });

            imageNode.setAttr('placed_by', playerRole);
            imageNode.image().src = imageUrl;
            imageNode.image().onload = () => {
                layer.add(imageNode);
                layer.draw();
            };
        }
        layer.draw();
    }

    function removePieceFromGrid(pieceId, layer) {
        const placedKey = `${playerRole}_${pieceId}`;
        if (placedPieces[placedKey]) {
            const pieceContainer = document.querySelector(`#${playerRole}-pieces [data-piece-id="${pieceId}"]`);
            if (pieceContainer) {
                pieceContainer.classList.remove('disabled');
            }

            const piece = layer.findOne(`#${pieceId}`);
            if (piece) {
                piece.destroy();
                layer.draw();
            }

            delete placedPieces[placedKey];

            fetch(`/jigsaw/remove_piece/${pieceId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify({}),
            }).then(response => response.json())
            .then(data => {
                if (data.status !== 'success') {
                    console.error('Failed to remove piece:', data.message);
                }
            });

            if (isWebSocketConnected) {
                socket.send(JSON.stringify({
                    'type': 'piece_remove',
                    'piece_id': pieceId,
                    'player_role': playerRole
                }));
            }
        }
    }

    function setupPieceClickHandlers() {
        const containers = document.querySelectorAll('.pieces-container');
        containers.forEach(container => {
            container.addEventListener('click', (e) => {
                if (e.target.classList.contains('piece')) {
                    if (selectedPiece) {
                        selectedPiece.classList.remove('selected');
                    }
                    selectedPiece = e.target;
                    selectedPiece.classList.add('selected');
                }
            });
        });
    }

    if (playerRole === 'player1') {
        document.getElementById('player2-grid').classList.add('blurred');
    } else if (playerRole === 'player2') {
        document.getElementById('player1-grid').classList.add('blurred');
    }

    loadInitialPieces(pieces);
    setupPieceClickHandlers();

    // If the game already started, resume the countdown
    fetch(`/jigsaw/get_remaining_time/${roomId}/`)
        .then(response => response.json())
        .then(data => {
            if (data.remaining_time < totalDuration) {
                startCountdown(data.remaining_time);
            }
        });

    function loadInitialPieces(pieces) {
        pieces.forEach(piece => {
            if (piece.is_placed) {
                const isOpponentPiece = (playerRole === 'player1' && piece.placed_by === 'player2') ||
                                        (playerRole === 'player2' && piece.placed_by === 'player1');
                const targetLayer = piece.placed_by === 'player1' ? player1Layer : player2Layer;
                updatePieceOnGrid(
                    targetLayer,
                    piece.id,
                    piece.x,
                    piece.y,
                    piece.image_url,
                    isOpponentPiece
                );
            }
        });
    }

    // Timer Functions
    let countdownInterval;
    function startCountdown(remaining) {
        const countdownElement = document.getElementById('countdown-timer');

        if (countdownInterval) clearInterval(countdownInterval);

        countdownInterval = setInterval(() => {
            if (remaining <= 0) {
                clearInterval(countdownInterval);
                countdownElement.textContent = "Time's up!";
                // Handle end-of-game scenario here
            } else {
                countdownElement.textContent = formatTime(remaining);
                remaining--;
            }
        }, 1000);
    }

    function formatTime(seconds) {
        const m = Math.floor(seconds / 60);
        const s = seconds % 60;
        return `${m}:${s < 10 ? '0' : ''}${s}`;
    }
});
