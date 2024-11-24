
document.addEventListener('DOMContentLoaded', () => {
    const puzzleContainer = document.getElementById('puzzle-container');
    let puzzleArray = savedPuzzleState || [...Array(15).keys(), 'empty'];  // Puzzle state array
    let emptyTileIndex = puzzleArray.indexOf('empty');
    const socket = new WebSocket(`ws://${window.location.host}/ws/sliding_puzzle/${roomId}/`);  // Updated path

    // Replace this with a dynamic path
    const baseImageUrl = `${window.location.origin}${mediaUrl}puzzles/${roomId}/`; // Dynamic base URL for puzzle pieces

    const tileWidth = 75;  // Adjust based on image tile size
    const tileHeight = 75;

    // WebSocket on message event (handling updates from other users)
    socket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        const pieceId = data.piece_id;
        const colTarget = data.col_target;
        const rowTarget = data.row_target;

        // Update puzzle state based on the incoming WebSocket message
        puzzleArray[pieceId] = { col: colTarget, row: rowTarget };
        createPuzzle();  // Re-render the puzzle with updated positions
    };

    // Create the initial puzzle layout
    function createPuzzle() {
        puzzleContainer.innerHTML = '';
        puzzleArray.forEach((tile, index) => {
            const tileDiv = document.createElement('div');
            tileDiv.classList.add('tile');
            
            if (tile === 'empty') {
                tileDiv.classList.add('empty');
            } else {
                const row = Math.floor(index / 4);
                const col = index % 4;

                // Set the background image from the correct puzzle piece path
                const tileImageUrl = `${baseImageUrl}tile_${row}_${col}.png`;
                tileDiv.style.backgroundImage = `url(${tileImageUrl})`;
                tileDiv.style.backgroundPosition = `-${col * tileWidth}px -${row * tileHeight}px`;

                tileDiv.onclick = () => moveTile(index);
            }
            puzzleContainer.appendChild(tileDiv);
        });
    }

    // Move a tile if adjacent to the empty tile
    function moveTile(index) {
        const validMoves = [emptyTileIndex - 1, emptyTileIndex + 1, emptyTileIndex - 4, emptyTileIndex + 4];
        if (validMoves.includes(index)) {
            [puzzleArray[emptyTileIndex], puzzleArray[index]] = [puzzleArray[index], puzzleArray[emptyTileIndex]];
            emptyTileIndex = index;
            createPuzzle();
            savePuzzleState();  // Save the new puzzle state to the backend
        }
    }

    // Save the puzzle state to the server
    function savePuzzleState() {
        const csrftoken = document.querySelector('[name=csrf-token]').content;

        fetch(`/sliding_puzzle/save-puzzle-state/${roomId}/`, {  // Updated URL
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken,
            },
            body: JSON.stringify({ puzzleState: puzzleArray })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                console.log('Puzzle state saved successfully');
            } else {
                console.error('Error saving puzzle state');
            }
        });
    }

    // Initialize puzzle on load
    createPuzzle();
});
