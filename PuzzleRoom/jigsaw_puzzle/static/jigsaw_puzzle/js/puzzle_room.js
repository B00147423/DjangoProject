document.addEventListener('DOMContentLoaded', () => {
    let isWebSocketConnected = false; // 🔥 Move this line here!

    function updateMoveCounters(player1Moves, player2Moves) {
        const player1Element = document.getElementById("player1-moves");
        const player2Element = document.getElementById("player2-moves");
        
        if (player1Element && player1Moves !== undefined) {
            player1Element.textContent = player1Moves;
        }
        
        if (player2Element && player2Moves !== undefined) {
            player2Element.textContent = player2Moves;
        }
        
        console.log(`✅ Move counters updated - Player 1: ${player1Moves}, Player 2: ${player2Moves}`);
    }
    // Parse the JSON data from the script tags
    const piecesDataElement = document.getElementById('puzzle-data');
    const pieces = JSON.parse(piecesDataElement.textContent);

    const roomDataElement = document.getElementById('room-data');
    const roomData = JSON.parse(roomDataElement.textContent);

    // Access the variables from roomData
    const csrfToken = roomData.csrfToken;
    const playerRole = roomData.playerRole;
    const difficulty = roomData.difficulty;
    const roomId = roomData.roomId;
    const totalDuration = roomData.totalDuration;
    const username = roomData.username;

    let gridRows, gridCols;
    let selectedPiece = null;
    const placedPieces = {};
    let moveCounter = 0;  // Tracks moves

    // Get container width and calculate responsive grid size
    const container = document.getElementById('player1-grid').parentElement;
    const containerWidth = container.clientWidth;
    const containerSize = Math.min(400, containerWidth * 0.8); // Match backend calculation

    let baseGridSize;
    if (difficulty === 'easy') {
        gridRows = 4;
        gridCols = 4;
        baseGridSize = containerSize / 4;  // Responsive size for easy
    } else if (difficulty === 'medium') {
        gridRows = 6;
        gridCols = 6;
        baseGridSize = containerSize / 6;   // Responsive size for medium
    } else if (difficulty === 'hard') {
        gridRows = 8;
        gridCols = 8;
        baseGridSize = containerSize / 8;   // Responsive size for hard
    } else {
        // Default
        gridRows = 4;
        gridCols = 4;
        baseGridSize = containerSize / 4;  // Default to easy
    }

    // Initialize Konva stages and layers with responsive sizes
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

    // Load puzzle pieces
    loadPuzzlePieces('player1-pieces', pieces);
    loadPuzzlePieces('player2-pieces', pieces);

    // Create grids for both players
    createGrid(player1Stage, player1Layer, 'player1');
    createGrid(player2Stage, player2Layer, 'player2');

    // WebSocket setup
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const socket = new WebSocket(`${protocol}://${window.location.host}/ws/puzzle/${roomId}/`);
 
    socket.onopen = function () {
        console.log('WebSocket connection established');
        isWebSocketConnected = true;
    };

    socket.onclose = function () {
        console.log('WebSocket connection closed');
        isWebSocketConnected = false;
    };

    socket.onerror = function(error) {
        console.error('WebSocket error:', error);
    };

    // Chat elements
    const chatContainer = document.querySelector('.chat-container');
    const chatBox = document.getElementById('chat-box');
    const chatInput = document.getElementById('chat-input');
    const sendChatButton = document.getElementById('send-chat');
    const toggleChatBtn = document.getElementById('toggle-chat');
    const chatHeader = document.querySelector('.chat-header');

    // Chat functionality
    function sendChatMessage() {
        const message = chatInput.value.trim();
        if (message && isWebSocketConnected) {
            console.log('💬 Sending chat message:', message);
            socket.send(JSON.stringify({
                type: 'chat_message',
                message: message,
                username: username
            }));
            chatInput.value = '';
        }
    }

    // Chat event listeners
    if (sendChatButton && chatInput) {
        sendChatButton.addEventListener('click', sendChatMessage);
        chatInput.addEventListener('keypress', (event) => {
            if (event.key === 'Enter') {
                event.preventDefault();
                sendChatMessage();
            }
        });
    }

    // Chat minimization
    if (chatContainer && toggleChatBtn && chatHeader) {
        function toggleChat() {
            chatContainer.classList.toggle('minimized');
            toggleChatBtn.textContent = chatContainer.classList.contains('minimized') ? '+' : '-';
        }

        toggleChatBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleChat();
        });

        chatHeader.addEventListener('click', toggleChat);
    }

    function appendChatMessage(username, message) {
        if (!chatBox) return;
        console.log('📝 Appending chat message:', username, message);
        
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('chat-message');
        messageDiv.innerHTML = `<span class="message-sender">${username}</span>: ${message}`;
        chatBox.appendChild(messageDiv);
        chatBox.scrollTop = chatBox.scrollHeight;

        // Notify if chat is minimized
        if (chatContainer && chatContainer.classList.contains('minimized')) {
            chatHeader.style.animation = 'pulse 1s';
            setTimeout(() => {
                chatHeader.style.animation = '';
            }, 1000);
        }
    }

    socket.onmessage = function (event) {
        const data = JSON.parse(event.data);
        console.log("📥 WebSocket Data Received:", data);
        
        if (data.type === "current_state") {
            console.log(`📊 Initial game state - Player 1 Moves: ${data.player1_moves}, Player 2 Moves: ${data.player2_moves}`);
            updateMoveCounters(data.player1_moves, data.player2_moves);

            if (data.elapsed_time !== undefined) {
                console.log("⏳ Starting count-up timer with elapsed time:", data.elapsed_time);
                startCountup(data.elapsed_time);
            }

            // Load initial chat messages
            if (data.chat_messages && Array.isArray(data.chat_messages)) {
                data.chat_messages.forEach(msg => {
                    appendChatMessage(msg.user__username, msg.message);
                });
            }

            // Load initial pieces
            if (data.pieces && Array.isArray(data.pieces)) {
                data.pieces.forEach(piece => {
                    if (piece.is_placed) {
                        const targetLayer = piece.placed_by === 'player1' ? player1Layer : player2Layer;
                        updatePieceOnGrid(
                            targetLayer,
                            piece.id,
                            piece.x_position,
                            piece.y_position,
                            piece.image_piece,
                            piece.placed_by !== playerRole
                        );
                    }
                });
            }
        }
        else if (data.type === "chat_message") {
            console.log(`💬 Received chat message from ${data.username}: ${data.message}`);
            appendChatMessage(data.username, data.message);
        }
        else if (data.type === "piece_move") {
            console.log(`📌 Piece moved: ID=${data.piece_id}, New X=${data.new_x}, New Y=${data.new_y}`);
            
            // Update move counters with the latest values
            updateMoveCounters(data.player1_moves, data.player2_moves);
            
            // Sync local move counter
            moveCounter = data.player_role === "player1" ? data.player1_moves : data.player2_moves;
            console.log(`🔄 Synced moveCounter: ${moveCounter}`);
            
            // Determine the correct layer based on player role
            const targetLayer = data.player_role === "player1" ? player1Layer : player2Layer;
            
            // Update the piece position
            updatePieceOnGrid(targetLayer, data.piece_id, data.new_x, data.new_y, data.image_url);
            
            // Store the updated position
            placedPieces[`${data.player_role}_${data.piece_id}`] = { 
                x: data.new_x, 
                y: data.new_y, 
                imageUrl: data.image_url,
                is_correct: data.is_correct
            };
            
            console.log(`✅ Piece ${data.piece_id} updated in real-time.`);
        }
        else if (data.type === "puzzle_completed") {
            console.log("🎉 Puzzle Completed!");
            showCompletionModal(
                data.completion_time,
                data.moves_taken,
                data.winner
            );
        }
    };
    
    

    // Function to show the completion modal
    function showCompletionModal(completionTime = 0, movesTaken = 0, winner = null) {
        if (document.getElementById("completion-modal")) {
            console.log("Modal already displayed.");
            return;
        }

        // Disable piece interaction
        document.querySelectorAll(".piece").forEach(piece => {
            piece.style.pointerEvents = "none";
        });

        console.log("💡 Display Completion Modal");

        const modalHtml = `
            <div id="completion-modal" class="modal-overlay">
                <div class="modal-content animate-modal">
                    <h2>🎉 ${winner ? winner + " Wins!" : "Puzzle Completed!"} 🎉</h2>
                    <p>${winner ? "Congratulations! You finished first in the 1v1 match." : "Great teamwork! The puzzle is now complete."}</p>
                    <p><strong>⏳ Time Taken:</strong> ${completionTime} seconds</p>
                    <p><strong>🔢 Moves Taken:</strong> ${movesTaken}</p>
                    <button id="view-leaderboard">🏆 View Leaderboard</button>
                    <button id="return-home">🏠 Return to Dashboard</button>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML("beforeend", modalHtml);

        // Add event listeners for buttons
        document.getElementById("return-home").addEventListener("click", () => {
            window.location.href = "/user/dashboard";
        });

        document.getElementById("view-leaderboard").addEventListener("click", () => {
            window.location.href = "/jigsaw/leaderboard";
        });

        // Confetti animation for celebration 🎉
        confetti({
            particleCount: 200,
            spread: 90,
            origin: { y: 0.6 },
        });
    }

    // Function to update a piece on the grid
    function updatePieceOnGrid(layer, pieceId, newX, newY, imageUrl, isOpponentPiece = false) {
        console.log(`🔄 Placing piece ${pieceId} at (${newX}, ${newY}) - Opponent: ${isOpponentPiece}`);
    
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
                            'player_role': playerRole,
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

    // Function to remove a piece from the grid
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
            })
                .then(response => response.json())
                .then(data => {
                    if (data.status !== 'success') {
                        console.error('Failed to remove piece:', data.message);
                    }
                });

            if (isWebSocketConnected) {
                socket.send(JSON.stringify({
                    'type': 'piece_remove',
                    'piece_id': pieceId,
                    'player_role': playerRole,
                }));
            }
        }
    }

    // Function to set up click handlers for puzzle pieces
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

    // Blur the opponent's grid based on player role
    if (playerRole === 'player1') {
        document.getElementById('player2-grid').classList.add('blurred');
    } else if (playerRole === 'player2') {
        document.getElementById('player1-grid').classList.add('blurred');
    }

    // Load initial pieces and set up click handlers
    loadInitialPieces(pieces);
    setupPieceClickHandlers();

    // If the game already started, resume the countdown
    fetch(`/jigsaw/get_remaining_time/${roomId}/`)
        .then(response => response.json())
        .then(data => {
            if (data.remaining_time < totalDuration) {
                startCountup(totalDuration - data.remaining_time);
            }
        });

        function safeImageUrl(url) {
            if (url.startsWith("http") || url.startsWith("https")) {
                return url;  // It's a full Cloudinary URL — use it directly
            }
            return `/media/${url}`;  // It's a relative local path
        }
        

        function loadPuzzlePieces(piecesContainerId, piecesData) {
            const piecesContainer = document.getElementById(piecesContainerId);
            const containerRect = piecesContainer.getBoundingClientRect();
            const pieceSize = 60; // Adjust according to your grid size
            let nextX = 10; // Initial position
            let nextY = 10;
        
            if ((playerRole === 'player1' && piecesContainerId === 'player1-pieces') ||
                (playerRole === 'player2' && piecesContainerId === 'player2-pieces')) {
        
                piecesData.forEach((piece, index) => {
                    const pieceElement = document.createElement('div');
                    pieceElement.classList.add('piece');
                    pieceElement.dataset.pieceId = piece.id;
                    pieceElement.style.backgroundImage = `url('${safeImageUrl(piece.image_url)}')`;
        
                    // Positioning logic to prevent stacking
                    pieceElement.style.position = "absolute";
                    pieceElement.style.left = `${nextX}px`;
                    pieceElement.style.top = `${nextY}px`;
        
                    nextX += pieceSize + 15; // Move right for next piece
                    if (nextX + pieceSize > containerRect.width) {
                        nextX = 10; // Reset to start of the row
                        nextY += pieceSize + 20; // Move down for next row
                    }
        
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
        
                // Ensure the container doesn't scroll
                piecesContainer.style.overflow = 'hidden';
                piecesContainer.style.position = 'relative';
            }
        }
    
    
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
                    updatePieceOnGrid(currentLayer, pieceId, pieceData.x, pieceData.y, pieceData.imageUrl);
                });
            });
        }

    // Function to load initial pieces
    function loadInitialPieces(pieces) {
        console.log("🔄 Loading all pieces after refresh...");
    
        pieces.forEach(piece => {
            if (piece.is_placed) {
                console.log(`🔍 Loading piece ${piece.id} placed by ${piece.placed_by}`);
    
                const isOpponentPiece = (playerRole === 'player1' && piece.placed_by === 'player2') ||
                                        (playerRole === 'player2' && piece.placed_by === 'player1');
                const targetLayer = piece.placed_by === 'player1' ? player1Layer : player2Layer;
    
                console.log(`📌 Drawing piece ${piece.id} at (${piece.x}, ${piece.y}) - Opponent: ${isOpponentPiece}`);
    
                updatePieceOnGrid(
                    targetLayer,
                    piece.id,
                    piece.x,  // ✅ Correct field name
                    piece.y,  // ✅ Correct field name
                    piece.image_url,  // ✅ Correct image field
                    isOpponentPiece
                );
            }
        });
    
        console.log("✅ All pieces loaded.");
    }
    

    // Timer functions
    let countupInterval;
    function startCountup(initialTime = 0) {
        const timerElement = document.getElementById('game-timer');
        let elapsedTime = initialTime;
    
        if (countupInterval) clearInterval(countupInterval);
    
        countupInterval = setInterval(() => {
            timerElement.textContent = formatTime(elapsedTime);
            elapsedTime++;
        }, 1000);
    }
    
    // Keep your formatTime function the same
    function formatTime(seconds) {
        const m = Math.floor(seconds / 60);
        const s = seconds % 60;
        return `${m}:${s < 10 ? '0' : ''}${s}`;
    }

    // Function to send a move via WebSocket
    function sendMove(pieceId, newX, newY, imageUrl) {
        if (!isWebSocketConnected) {
            console.error('WebSocket not connected!');
            return;
        }
        moveCounter++; // Keep local count, but do NOT update UI directly

        socket.send(JSON.stringify({
            'type': 'piece_move',
            'piece_id': pieceId,
            'new_x': newX,
            'new_y': newY,
            'player_role': playerRole,
            'image_url': imageUrl,
            'base_grid_size': baseGridSize,
            'moves_taken': moveCounter  // Send move count
        }));
    }

    // Function to check if a piece is in the correct position
    function checkPiecePosition(pieceId, x, y) {
        const piece = pieces.find(p => p.id === pieceId);
        if (piece) {
            // Calculate which grid cell the piece is in
            const currentGridX = Math.floor(x / baseGridSize);
            const currentGridY = Math.floor(y / baseGridSize);

            // The backend already provides grid positions in grid coordinates
            const expectedGridX = piece.grid_x;
            const expectedGridY = piece.grid_y;

            console.log(`🔍 Checking grid position for piece ${pieceId}`);
            console.log(`Current grid: (${currentGridX}, ${currentGridY})`);
            console.log(`Expected grid: (${expectedGridX}, ${expectedGridY})`);
            console.log(`Piece grid_x: ${piece.grid_x}, grid_y: ${piece.grid_y}`);

            // Compare the grid positions
            const isCorrect = (currentGridX === expectedGridX && currentGridY === expectedGridY);

            if (isCorrect) {
                console.log(`✅ Piece ${pieceId} is in the correct grid cell.`);
                piece.is_correct = true;
                highlightPiece(pieceId, "green");
                return true;
            } else {
                console.log(`❌ Piece ${pieceId} is not in the correct grid cell.`);
                piece.is_correct = false;
                highlightPiece(pieceId, "red");
                return false;
            }
        } else {
            console.error(`❌ Piece ${pieceId} not found in pieces.`);
            return false;
        }
    }

    // Function to place a piece on the grid
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
                id: pieceId,
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

            // Check if piece is placed correctly
            const isCorrect = checkPiecePosition(pieceId, newX, newY);
            const placedKey = `${playerRole}_${pieceId}`;
            placedPieces[placedKey] = {
                x: newX,
                y: newY,
                imageUrl: pieceImageUrl,
                is_correct: isCorrect
            };

            selectedPiece.classList.add('disabled');
            selectedPiece.classList.remove('selected');
            selectedPiece = null;

            checkPuzzleCompletion(); // Check if the puzzle is complete
        }
    }

    // Function to check if the puzzle is completed
    function checkPuzzleCompletion() {
        // Get all pieces for the current player
        const playerPieces = Object.entries(placedPieces)
            .filter(([key]) => key.startsWith(playerRole))
            .map(([_, piece]) => piece);

        // Check if all pieces are correct
        const allCorrect = playerPieces.every(piece => piece.is_correct);
        console.log("Checking puzzle completion:", allCorrect);

        if (allCorrect) {
            console.log("🎉 Puzzle completed! Sending completion event...");
            socket.send(JSON.stringify({
                type: "check_completion",
                room_id: roomId,
                base_grid_size: baseGridSize
            }));
        }
    }

    // Function to highlight a piece
    function highlightPiece(pieceId, color) {
        const piece = document.querySelector(`[data-piece-id="${pieceId}"]`);
        if (piece) {
            piece.style.border = `2px solid ${color}`;
            setTimeout(() => {
                piece.style.border = '';
            }, 1000);
        }
    }
});


document.addEventListener('DOMContentLoaded', () => {
    const toggleButton = document.getElementById('toggle-view');
    const gameArea = document.getElementById('game-area');
    const player1Container = document.getElementById('player1-container');
    const player2Container = document.getElementById('player2-container');

    // Get player role from room data
    const roomDataElement = document.getElementById('room-data');
    const roomData = JSON.parse(roomDataElement.textContent);
    const playerRole = roomData.playerRole;

    // Read URL params to check the state (solo mode or split-screen)
    const urlParams = new URLSearchParams(window.location.search);
    let isSoloMode = urlParams.get('solo') === 'true';

    // Function to update visibility based on player role and solo mode
    function updateVisibility() {
        console.log('Updating visibility:', { isSoloMode, playerRole });
        
        if (isSoloMode) {
            // Show only the current player's container
            if (playerRole === 'player1') {
                player1Container.style.display = 'flex';
                player1Container.style.width = '100%';
                player2Container.style.display = 'none';
            } else if (playerRole === 'player2') {
                player2Container.style.display = 'flex';
                player2Container.style.width = '100%';
                player1Container.style.display = 'none';
            }
            toggleButton.textContent = "Show Both Players";
        } else {
            // Show both containers
            player1Container.style.display = 'flex';
            player2Container.style.display = 'flex';
            player1Container.style.width = '50%';
            player2Container.style.width = '50%';
            toggleButton.textContent = "Show Only My Side";
        }

        // Force redraw of Konva stages
        if (window.player1Stage) {
            window.player1Stage.width(player1Container.clientWidth);
            window.player1Stage.draw();
        }
        if (window.player2Stage) {
            window.player2Stage.width(player2Container.clientWidth);
            window.player2Stage.draw();
        }
    }

    // Apply initial visibility
    updateVisibility();

    // Toggle event listener
    toggleButton.addEventListener('click', () => {
        isSoloMode = !isSoloMode;
        console.log('Toggle clicked:', { isSoloMode, playerRole });

        // Update the URL without refreshing the page
        const newUrl = new URL(window.location);
        if (isSoloMode) {
            newUrl.searchParams.set('solo', 'true');
        } else {
            newUrl.searchParams.delete('solo');
        }
        window.history.pushState({}, '', newUrl);

        // Update visibility with animation
        updateVisibility();
    });
});
