document.addEventListener('DOMContentLoaded', () => {
    const puzzleContainer = document.getElementById('puzzle-container');
    const savedState = JSON.parse(savedPuzzleState);
    const gridSize = savedState.grid_size || 4;
    let puzzleArray = savedState.pieces || [...Array(gridSize * gridSize - 1)].map((_, i) => i + 1).concat(['empty']);
    let emptyTileIndex = puzzleArray.indexOf('empty');
    let moveCount = savedState.move_count || 0;
    let bestTime = savedState.best_time || null;
    let bestMoves = savedState.best_moves || null;
    let gamesCompleted = savedState.games_completed || 0;
    const moveCountDisplay = document.getElementById('moveCount');
    const completionMessage = document.getElementById('completionMessage');
    let startTime = savedState.start_time || Date.now();
    let timerInterval;

    // Set CSS variable for grid size
    document.documentElement.style.setProperty('--grid-size', gridSize);

    // Calculate responsive tile size
    const containerWidth = puzzleContainer.clientWidth;
    const tileSize = Math.floor((containerWidth - (gridSize + 1) * 3) / gridSize); // Account for gap
    document.documentElement.style.setProperty('--tile-size', `${tileSize}px`);

    // Define the base URL for puzzle pieces
    const baseImageUrl = `${window.location.origin}${mediaUrl}puzzles/${roomId}/`;

    // Update move count display initially
    moveCountDisplay.textContent = moveCount;

    // Update stats display
    function updateStats() {
        if (bestTime) {
            const minutes = Math.floor(bestTime / 60).toString().padStart(2, '0');
            const seconds = (bestTime % 60).toString().padStart(2, '0');
            document.getElementById('bestTime').textContent = `${minutes}:${seconds}`;
        }
        if (bestMoves) {
            document.getElementById('bestMoves').textContent = bestMoves;
        }
        document.getElementById('gamesCompleted').textContent = gamesCompleted;
    }

    // Initialize stats
    updateStats();

    // Check if puzzle is complete
    function isPuzzleComplete() {
        for (let i = 0; i < puzzleArray.length - 1; i++) {
            if (puzzleArray[i] !== i + 1) {
                return false;
            }
        }
        return puzzleArray[puzzleArray.length - 1] === 'empty';
    }

    // Show completion message
    function showCompletionMessage() {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        document.getElementById('finalMoves').textContent = moveCount;
        const minutes = Math.floor(elapsed / 60).toString().padStart(2, '0');
        const seconds = (elapsed % 60).toString().padStart(2, '0');
        document.getElementById('finalTime').textContent = `${minutes}:${seconds}`;
        completionMessage.style.display = 'block';
        
        if (!bestTime || elapsed < bestTime) {
            bestTime = elapsed;
        }
        if (!bestMoves || moveCount < bestMoves) {
            bestMoves = moveCount;
        }
        gamesCompleted++;
        updateStats();

        // Save completion state
        savePuzzleState(true);
        clearInterval(timerInterval);
    }

    // Create the initial puzzle layout
    function createPuzzle() {
        puzzleContainer.innerHTML = '';
        puzzleArray.forEach((tile, index) => {
            const tileDiv = document.createElement('div');
            tileDiv.classList.add('tile');
            
            if (tile === 'empty') {
                tileDiv.classList.add('empty');
            } else {
                const originalRow = Math.floor((tile - 1) / gridSize);
                const originalCol = (tile - 1) % gridSize;

                const tileImageUrl = `${baseImageUrl}tile_${originalRow}_${originalCol}.png`;
                tileDiv.style.backgroundImage = `url(${tileImageUrl})`;
                tileDiv.setAttribute('data-number', tile);

                tileDiv.onclick = () => moveTile(index);
            }
            puzzleContainer.appendChild(tileDiv);
        });

        if (savedState.is_completed && isPuzzleComplete()) {
            showCompletionMessage();
        }
    }

    // Check if move is valid
    function isValidMove(index) {
        const validMoves = [
            emptyTileIndex - 1, // left
            emptyTileIndex + 1, // right
            emptyTileIndex - gridSize, // up
            emptyTileIndex + gridSize  // down
        ];

        return validMoves.includes(index) && 
            !(emptyTileIndex % gridSize === 0 && index % gridSize === gridSize - 1) && // Prevent wrapping from left to right
            !(emptyTileIndex % gridSize === gridSize - 1 && index % gridSize === 0); // Prevent wrapping from right to left
    }

    // Move a tile
    function moveTile(index) {
        if (isValidMove(index)) {
            [puzzleArray[emptyTileIndex], puzzleArray[index]] = [puzzleArray[index], puzzleArray[emptyTileIndex]];
            emptyTileIndex = index;
            moveCount++;
            moveCountDisplay.textContent = moveCount;
            
            createPuzzle();
            savePuzzleState();

            if (isPuzzleComplete()) {
                showCompletionMessage();
            }
        }
    }

    // Save the puzzle state to the server
    function savePuzzleState(isCompleted = false) {
        const csrftoken = document.querySelector('[name=csrf-token]').content;
        const elapsed = Math.floor((Date.now() - startTime) / 1000);

        fetch(`/sliding_puzzle/save-puzzle-state/${roomId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken,
            },
            body: JSON.stringify({ 
                puzzleState: puzzleArray,
                moveCount: moveCount,
                grid_size: gridSize,
                best_time: bestTime,
                best_moves: bestMoves,
                games_completed: gamesCompleted,
                current_time: elapsed,
                is_completed: isCompleted,
                start_time: startTime
            })
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

    // Function to shuffle array randomly
    function shuffleArray(array) {
        let currentIndex = array.length;
        while (currentIndex !== 0) {
            const randomIndex = Math.floor(Math.random() * currentIndex);
            currentIndex--;
            [array[currentIndex], array[randomIndex]] = [array[randomIndex], array[currentIndex]];
        }
        return array;
    }

    // Function to check if puzzle is solvable
    function isSolvable(puzzle) {
        let inversions = 0;
        const puzzleWithoutEmpty = puzzle.filter(x => x !== 'empty').map(x => x - 1);
        
        for (let i = 0; i < puzzleWithoutEmpty.length - 1; i++) {
            for (let j = i + 1; j < puzzleWithoutEmpty.length; j++) {
                if (puzzleWithoutEmpty[i] > puzzleWithoutEmpty[j]) {
                    inversions++;
                }
            }
        }

        const emptyIndex = puzzle.indexOf('empty');
        const emptyRowFromBottom = gridSize - Math.floor(emptyIndex / gridSize);
        
        return emptyRowFromBottom % 2 === 0 ? inversions % 2 === 1 : inversions % 2 === 0;
    }

    // Function to create a solvable puzzle
    function createSolvablePuzzle() {
        let puzzle = [...Array(gridSize * gridSize - 1)].map((_, i) => i + 1).concat(['empty']);
        do {
            puzzle = shuffleArray([...puzzle]);
        } while (!isSolvable(puzzle));
        return puzzle;
    }

    // Add reset game functionality
    window.shuffleAndReset = function() {
        moveCount = 0;
        moveCountDisplay.textContent = '0';
        completionMessage.style.display = 'none';
        
        puzzleArray = createSolvablePuzzle();
        emptyTileIndex = puzzleArray.indexOf('empty');
        
        startTime = Date.now();
        
        createPuzzle();
        savePuzzleState();
    };

    // Timer functionality
    function startTimer() {
        clearInterval(timerInterval);
        updateTimer();
        timerInterval = setInterval(updateTimer, 1000);
    }

    function updateTimer() {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        const minutes = Math.floor(elapsed / 60).toString().padStart(2, '0');
        const seconds = (elapsed % 60).toString().padStart(2, '0');
        document.getElementById('timer').textContent = `${minutes}:${seconds}`;
    }

    // Initialize puzzle and start timer
    createPuzzle();
    startTimer();
});
