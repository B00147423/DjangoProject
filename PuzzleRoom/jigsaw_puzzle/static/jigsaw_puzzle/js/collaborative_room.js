//C:\Users\beka\OneDrive\Desktop\Year4DjangoMajor-Project\DjangoProject\PuzzleRoom\jigsaw_puzzle\static\jigsaw_puzzle\js\collaborative_room.js
document.addEventListener("DOMContentLoaded", () => {
    // Extract Django Template Data from JSON Script Tags
    const roomId = JSON.parse(document.getElementById('room-data').textContent).room_id;
    const playerRole = JSON.parse(document.getElementById('room-data').textContent).player_role;
    const difficulty = JSON.parse(document.getElementById('room-data').textContent).difficulty;
    const piecesData = JSON.parse(document.getElementById('puzzle-data').textContent);

    // Grid Setup
    const gridSizes = { easy: 4, medium: 6, hard: 8 };
    const gridRows = gridSizes[difficulty];
    const gridCols = gridSizes[difficulty];
    const baseGridSize = 80;

    // Create Konva Stage
    const stage = new Konva.Stage({
        container: 'grid-container',
        width: baseGridSize * gridCols,
        height: baseGridSize * gridRows,
    });

    const layer = new Konva.Layer();
    stage.add(layer);

    // Initialize WebSocket
    const socket = new WebSocket(`ws://${window.location.host}/ws/puzzle/${roomId}/`);

    // Game State
    let selectedPiece = null;
    let placedPieces = {};

    // Preload Piece Images
    const pieceImages = {};
    piecesData.forEach(piece => {
        pieceImages[piece.id] = piece.image_url;
    });

    // Create Grid
    function createGrid() {
        for (let i = 0; i < gridCols; i++) {
            for (let j = 0; j < gridRows; j++) {
                const square = new Konva.Rect({
                    x: i * baseGridSize,
                    y: j * baseGridSize,
                    width: baseGridSize,
                    height: baseGridSize,
                    stroke: 'gray',
                    strokeWidth: 1,
                });
                square.on('click', () => {
                    if (selectedPiece) placePiece(square, i, j);
                });
                layer.add(square);
            }
        }
        layer.draw();
    }

    // Load Puzzle Pieces
    function loadPuzzlePieces(pieces) {
        const piecesGrid = document.getElementById('pieces-grid');

        pieces.forEach(piece => {
            if (piece.is_placed) {
                placePieceOnGrid(piece.id, piece.x, piece.y, piece.image_url);
            } else {
                const pieceElement = document.createElement('div');
                pieceElement.classList.add('piece');
                pieceElement.dataset.pieceId = piece.id;
                pieceElement.style.backgroundImage = `url('${piece.image_url}')`;

                pieceElement.addEventListener('click', () => {
                    if (selectedPiece) selectedPiece.classList.remove('selected');
                    selectedPiece = pieceElement;
                    pieceElement.classList.add('selected');
                });

                piecesGrid.appendChild(pieceElement);
            }
        });
    }

    // Place Piece on the Grid
    function placePiece(square, gridX, gridY) {
        if (selectedPiece) {
            const pieceId = selectedPiece.dataset.pieceId;
            const newX = gridX * baseGridSize;
            const newY = gridY * baseGridSize;

            placePieceOnGrid(pieceId, newX, newY);
            sendMove(pieceId, newX, newY);

            selectedPiece.classList.add('disabled');
            selectedPiece.classList.remove('selected');
            selectedPiece = null;
        }
    }

    // Render Piece on Konva Grid
    function placePieceOnGrid(pieceId, x, y, imageUrl = pieceImages[pieceId]) {
        const imageObj = new Image();
        imageObj.src = imageUrl;

        imageObj.onload = () => {
            const imageNode = new Konva.Image({
                x: x,
                y: y,
                width: baseGridSize,
                height: baseGridSize,
                image: imageObj,
                id: `piece-${pieceId}`,
            });

            imageNode.on('contextmenu', (e) => {
                e.evt.preventDefault();
                removePiece(pieceId);
            });

            layer.add(imageNode);
            layer.draw();
        };
    }

    // Remove Piece from the Grid
    function removePiece(pieceId) {
        removePieceFromGrid(pieceId);
        sendRemove(pieceId);
    }

    // WebSocket Messaging
    function sendMove(pieceId, newX, newY) {
        socket.send(JSON.stringify({
            type: "piece_move",
            piece_id: pieceId,
            new_x: newX,
            new_y: newY,
            player_role: playerRole,
        }));
    }

    function sendRemove(pieceId) {
        socket.send(JSON.stringify({
            type: "piece_remove",
            piece_id: pieceId,
            player_role: playerRole,
        }));
    }

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === "piece_move") {
            placePieceOnGrid(data.piece_id, data.new_x, data.new_y, data.image_url);

            const pieceElement = document.querySelector(`[data-piece-id="${data.piece_id}"]`);
            if (pieceElement) pieceElement.classList.add('disabled');
        } else if (data.type === "piece_remove") {
            removePieceFromGrid(data.piece_id);
        }
    };

    // Remove Piece from Konva Grid
    function removePieceFromGrid(pieceId) {
        const piece = layer.findOne(`#piece-${pieceId}`);
        if (piece) {
            piece.destroy();
            layer.draw();
        }

        delete placedPieces[pieceId];

        // Re-enable in pieces list if not present
        const existingPieceElement = document.querySelector(`[data-piece-id="${pieceId}"]`);
        if (!existingPieceElement) {
            const piecesGrid = document.getElementById('pieces-grid');
            const pieceElement = document.createElement('div');
            pieceElement.classList.add('piece');
            pieceElement.dataset.pieceId = pieceId;
            pieceElement.style.backgroundImage = `url('${pieceImages[pieceId]}')`;

            pieceElement.addEventListener('click', () => {
                if (selectedPiece) selectedPiece.classList.remove('selected');
                selectedPiece = pieceElement;
                pieceElement.classList.add('selected');
            });

            piecesGrid.appendChild(pieceElement);
        } else {
            existingPieceElement.classList.remove('disabled');
        }
    }

    // Initialize the Game
    createGrid();
    loadPuzzlePieces(piecesData);
});
