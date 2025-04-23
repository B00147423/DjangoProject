

const roomId = '{{ room.id }}';
const piecesData = JSON.parse(document.getElementById('puzzle-data').textContent);
const gridSizes = { easy: 4, medium: 6, hard: 8 };
const gridRows = gridSizes['{{ room.difficulty }}'];
const gridCols = gridSizes['{{ room.difficulty }}'];
const baseGridSize = 80; // Size of each grid cell
const playerRole = '{{ player_role }}';
const stage = new Konva.Stage({
    container: 'grid-container',
    width: baseGridSize * gridCols,
    height: baseGridSize * gridRows,
});
const layer = new Konva.Layer();
stage.add(layer);
let selectedPiece = null;

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
                if (selectedPiece) {
                    placePiece(square, i, j);
                }
            });
            layer.add(square);
        }
    }
    layer.draw();
}
function loadInitialPieces(pieces) {
    pieces.forEach(piece => {
        if (piece.is_placed) {
            // Place piece on the grid
            placePieceOnGrid(piece.id, piece.x, piece.y);
        } else {
            // Add piece back to the container
            const pieceElement = document.createElement('div');
            pieceElement.classList.add('piece');
            pieceElement.dataset.pieceId = piece.id;
            pieceElement.style.backgroundImage = `url('${piece.image_url}')`;
            document.getElementById('pieces-grid').appendChild(pieceElement);
        }
    });
}

    function placePiece(square, layer) {
        if (selectedPiece) {
            const pieceId = selectedPiece.dataset.pieceId;
            const newX = square.x();
            const newY = square.y();

            // Update piece on the server
            sendMove(pieceId, newX, newY);

            // Update piece on the grid
            placePieceOnGrid(pieceId, newX, newY);

            selectedPiece.classList.add('disabled');
            selectedPiece.classList.remove('selected');
            selectedPiece = null;
        }
    }


function sendMove(pieceId, newX, newY) {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
        console.error('WebSocket not connected!');
        return;
    }
    socket.send(JSON.stringify({
        'type': 'piece_move',
        'piece_id': pieceId,
        'new_x': newX,
        'new_y': newY,
        'player_role': playerRole
    }));
}

function placePiece(square, i, j) {
    if (selectedPiece) {
        const pieceId = selectedPiece.dataset.pieceId;
        const newX = square.x();
        const newY = square.y();

        // Update piece on the server
        sendMove(pieceId, newX, newY);

        // Update piece on the grid
        placePieceOnGrid(pieceId, newX, newY);

        selectedPiece.classList.add('disabled');
        selectedPiece.classList.remove('selected');
        selectedPiece = null;
    }
}

function removePieceFromGrid(pieceId) {
        const pieceElement = document.querySelector(`[data-piece-id="${pieceId}"]`);
        if (pieceElement) {
            // Reset piece to the container
            pieceElement.classList.remove('disabled');
            pieceElement.style.left = '';
            pieceElement.style.top = '';
            document.getElementById('pieces-grid').appendChild(pieceElement);
        }

        // Update the server
        fetch(`/jigsaw/remove_piece/${pieceId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
        }).then(response => response.json()).then(data => {
            if (data.status === 'success') {
                console.log('Piece removed successfully');
            }
        });
    }


// Bind right-click to remove pieces
document.addEventListener('contextmenu', (e) => {
e.preventDefault();
const pieceElement = e.target.closest('.piece');
if (pieceElement) {
    const pieceId = pieceElement.dataset.pieceId;
    removePieceFromGrid(pieceId);
}
});

document.addEventListener('contextmenu', (e) => {
    e.preventDefault();
    const pieceElement = e.target.closest('.piece');
    if (pieceElement) {
        const pieceId = pieceElement.dataset.pieceId;
        removePieceFromGrid(pieceId);
    }
});

const socket = new WebSocket(`ws://${window.location.host}/ws/puzzle/${roomId}/`);

socket.onmessage = function (event) {
const data = JSON.parse(event.data);
if (data.type === 'piece_move') {
    placePieceOnGrid(data.piece_id, data.new_x, data.new_y);
} else if (data.type === 'piece_remove') {
    removePieceFromGrid(data.piece_id);
}
};

document.addEventListener('DOMContentLoaded', () => {
    createGrid();
    loadInitialPieces(piecesData);
});

