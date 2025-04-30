document.addEventListener("DOMContentLoaded", () => {
    // Global variables for Konva stage and layer
    let stage;
    let layer;
    let selectedPiece = null;

    // Ensure required elements exist before proceeding
    const roomDataElement = document.getElementById("room-data");
    const puzzleDataElement = document.getElementById("puzzle-data");
    const chatMessagesElement = document.getElementById("chat-messages");

    if (!roomDataElement || !puzzleDataElement || !chatMessagesElement) {
        console.error("Missing critical HTML elements.");
        return;
    }

    // Extract Django template data
    const { room_id: roomId, player_role: playerRole, difficulty, username } = JSON.parse(roomDataElement.textContent);
    const piecesData = JSON.parse(puzzleDataElement.textContent);
    const initialMessages = JSON.parse(chatMessagesElement.textContent);

    // EXACT MATCH from puzzle_room.js for grid calculations
    const container = document.getElementById('grid-container').parentElement;
    const containerWidth = container.clientWidth;
    const containerSize = Math.min(400, containerWidth * 0.8); // Match puzzle_room.js calculation

    let gridRows, gridCols;
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

    // Set up grid container with responsive size
    const containerElement = document.getElementById("grid-container");
    containerElement.style.setProperty("--grid-cols", gridCols);
    containerElement.style.setProperty("--grid-rows", gridRows);
    containerElement.style.width = `${baseGridSize * gridCols}px`;
    containerElement.style.height = `${baseGridSize * gridRows}px`;

    // Initialize Konva stage with the exact same dimensions
    stage = new Konva.Stage({
        container: 'grid-container',
        width: baseGridSize * gridCols,
        height: baseGridSize * gridRows,
    });

    layer = new Konva.Layer();
    stage.add(layer);

    // Chat functionality
    const chatBox = document.getElementById("chat-box");
    const chatInput = document.getElementById("chat-input");
    const sendChatButton = document.getElementById("send-chat");

    // WebSocket connection
    let socket;
    let gameStartTime = Date.now();
    let gameTimerInterval;
    let moveCounter = 0;  // Tracks moves
    let lastLockedPiece = null;

    // Preload piece images
    const pieceImages = {};
    piecesData.forEach((piece) => {
        pieceImages[piece.id] = piece.image_url;
    });

    // Create grid
    function createGrid() {
        for (let i = 0; i < gridCols; i++) {
            for (let j = 0; j < gridRows; j++) {
                const square = new Konva.Rect({
                    x: i * baseGridSize,
                    y: j * baseGridSize,
                    width: baseGridSize,
                    height: baseGridSize,
                    stroke: "gray",
                    strokeWidth: 1,
                });

                square.on("click", () => {
                    if (selectedPiece) {
                        placePiece(square, i, j);
                    }
                });

                layer.add(square);
            }
        }
        layer.draw();
    }

    function initializeWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
        socket = new WebSocket(`${protocol}://${window.location.host}/ws/puzzle/${roomId}/`);
    
        socket.onopen = () => {
            startGameTimer();
        };
    
        socket.onclose = () => {
            console.error("⚠️ WebSocket disconnected. Reconnecting...");
            setTimeout(initializeWebSocket, 1000); // Retry connection every 1 second
        };
    
        socket.onerror = (error) => {
            socket.close(); // Close the socket on error
        };

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log("🔄 Message received:", data);
    
            if (data.type === "piece_move") {
                placePieceOnGrid(data.piece_id, data.new_x, data.new_y, data.image_url);
                    // Update move counter
                moveCounter = data.moves_taken;
                document.getElementById("move-counter").textContent = moveCounter;
                // Update timer if elapsed_time is sent
                if (data.elapsed_time !== undefined) {
                    gameStartTime = Date.now() - data.elapsed_time * 1000;
                }

                const piece = piecesData.find(p => p.id === data.piece_id);
                if (piece) {
                    piece.x = data.new_x;
                    piece.y = data.new_y;
                    piece.is_correct = data.is_correct;
                }
    
                setTimeout(checkPuzzleCompletion, 50);
    

                if (data.is_correct) {
                    socket.send(JSON.stringify({ type: "confirm_piece", piece_id: data.piece_id }));
                }
    
                // Remove the piece from the sidebar if it's there
                const sidebarPiece = document.querySelector(`[data-piece-id="${data.piece_id}"]`);
                if (sidebarPiece) {
                    sidebarPiece.remove();
                }
    
                checkPuzzleCompletion();
            } 
            else if (data.type === "piece_lock") {
                lockPieceUI(data.piece_id, data.player_role);
            } 
            else if (data.type === "piece_unlock") {
                unlockPieceUI(data.piece_id);
            }
            
            else if (data.type === "piece_remove") {
                handlePieceRemove(data.piece_id);
            } 
            
            else if (data.type === "chat_message") {
                appendChatMessage(data.username, data.message);
            } 
            
            else if (data.type === "current_state") {
                loadGameState(data.pieces, data.chat_messages);
                   
                // Set correct timer & moves count
                if (data.elapsed_time) {
                    gameStartTime = Date.now() - data.elapsed_time * 1000;
                }
                if (data.moves_taken !== undefined) {
                    moveCounter = data.moves_taken;
                    document.getElementById("move-counter").textContent = moveCounter;
                }

                // Restart timer
                startGameTimer();
                // If the puzzle was already completed, show the modal
                if (data.puzzle_completed) {
                    showCompletionModal(data.completion_time, data.moves_taken);
                }
            } 
            
            else if (data.type === "puzzle_completed") {
                console.log("🎉 Puzzle Completed! Showing summary.");

                // Stop timer
                clearInterval(gameTimerInterval);
            
                // Ensure completion time and moves taken are displayed
                showCompletionModal(data.completion_time, data.moves_taken);
            }
        };
    }

    function lockPieceUI(pieceId, lockedBy) {
        const pieceElement = document.querySelector(`[data-piece-id="${pieceId}"]`);
        if (pieceElement) {
            pieceElement.classList.add("locked");
            pieceElement.setAttribute("data-locked-by", lockedBy);
    
            if (lockedBy !== playerRole) {
                pieceElement.style.opacity = "0.5";
            }
        } 
    }

    function unlockPieceUI(pieceId) {
        const pieceElement = document.querySelector(`[data-piece-id="${pieceId}"]`);
        if (pieceElement) {
            pieceElement.classList.remove("locked");
            pieceElement.removeAttribute("data-locked-by");
            pieceElement.style.opacity = "1";
    
            console.log(`🔓 Piece ${pieceId} unlocked`);
        } 
    }
    
    function startGameTimer() {
        if (gameTimerInterval) {
            clearInterval(gameTimerInterval);
        }
    
        gameTimerInterval = setInterval(updateGameTimer, 1000);
    }
    
    function updateGameTimer() {
        const elapsedTime = Math.floor((Date.now() - gameStartTime) / 1000);
        const minutes = String(Math.floor(elapsedTime / 60)).padStart(2, "0");
        const seconds = String(elapsedTime % 60).padStart(2, "0");
        document.getElementById("game-timer").textContent = `${minutes}:${seconds}`;
    }

    function checkPuzzleCompletion() {
        const allCorrect = piecesData.every(piece => piece.is_correct);
        console.log("🔎 Checking puzzle completion:", allCorrect);
    
        if (allCorrect) {
            showCompletionModal(data.elapsed_time, data.moves_taken);

            socket.send(JSON.stringify({ type: "puzzle_completed", room_id: roomId }));
        }
    }
    


    function showCompletionModal(completionTime = 0, movesTaken = 0) {
        // Avoid duplicate modals
        if (document.getElementById("completion-modal")) {
            console.log("Modal already displayed.");
            return;
        }
    
        document.querySelectorAll(".piece").forEach(piece => {
            piece.style.pointerEvents = "none";
        });
    
        console.log('💡 Display Completion Modal');
    
        const audio = new Audio('/static/sounds/puzzle_Complete.mp3');

        audio.play();
    
        const modalHtml = `
            <div id="completion-modal" class="modal-overlay">
                <div class="modal-content animate-modal">
                    <h2>🎉 Puzzle Completed! 🎉</h2>
                    <p>Great teamwork! The puzzle is now complete.</p>
                    <p><strong>⏳ Time Taken:</strong> ${completionTime} seconds</p>
                    <p><strong>🔢 Moves Taken:</strong> ${movesTaken}</p>
                    <button id="view-leaderboard">🏆 View Leaderboard</button>
                    <button id="return-home">🏠 Return to Dashboard</button>
                </div>
            </div>
        `;
    
        document.body.insertAdjacentHTML("beforeend", modalHtml);
    
        document.getElementById("return-home").addEventListener("click", () => {
            window.location.href = "/user/dashboard";
        });
    
        document.getElementById("view-leaderboard").addEventListener("click", () => {
            window.location.href = "/jigsaw/leaderboard"; 
        });
        
        confetti({
            particleCount: 200,
            spread: 90,
            origin: { y: 0.6 }
        });
    }

    initializeWebSocket();

    function handlePieceRemove(pieceId) {
        // Remove the piece from the grid for everyone
        removePieceFromGrid(pieceId);
    
        // Re-add the piece to the sidebar, making it available again
        const piecesGrid = document.getElementById("pieces-grid");
        const pieceElement = document.createElement("div");
        pieceElement.classList.add("piece");
        pieceElement.dataset.pieceId = pieceId;
        pieceElement.style.backgroundImage = `url('${pieceImages[pieceId]}')`;
    
        pieceElement.addEventListener("click", () => {
            if (selectedPiece) selectedPiece.classList.remove("selected");
            selectedPiece = pieceElement;
            pieceElement.classList.add("selected");
        });
    
        piecesGrid.appendChild(pieceElement);
    }
    


    // Load initial game state
    function loadGameState(pieces, chatMessages) {
        pieces.forEach((piece) => {
            console.log("🔍 Checking Piece:", piece);
    
            if (!piece.image_url || piece.image_url.trim() === "") {
                return;  
            }
            addPieceToSidebar(piece.id, piece.image_url);
        });
    
        chatMessages.forEach((msg) => {
            appendChatMessage(msg.user__username, msg.message);
        });
    }
    
    function addPieceToSidebar(pieceId, imageUrl) {
        const piecesGrid = document.getElementById("pieces-grid");
        const pieceElement = document.createElement("div");
        pieceElement.classList.add("piece");
        pieceElement.dataset.pieceId = pieceId;
        pieceElement.style.backgroundImage = `url('${imageUrl}')`;

        pieceElement.addEventListener("click", () => {
            if (selectedPiece) selectedPiece.classList.remove("selected");
            selectedPiece = pieceElement;
            pieceElement.classList.add("selected");
        });
        piecesGrid.appendChild(pieceElement);
    }

    // Append a new chat message
    function appendChatMessage(username, message) {
        const messageElement = document.createElement("div");
        messageElement.classList.add("chat-message");
        messageElement.innerHTML = `<span class="username">${username}</span>: ${message}`;
        chatBox.appendChild(messageElement);
        chatBox.scrollTop = chatBox.scrollHeight; // Auto-scroll to the bottom
    }

    // Send a chat message
    sendChatButton.addEventListener("click", () => {
        const message = chatInput.value.trim();
        if (message) {
            socket.send(
                JSON.stringify({
                    type: "chat_message",
                    message: message,
                    username: username,
                })
            );
            chatInput.value = ""; // Clear input
        }
    });

    chatInput.addEventListener("keypress", (event) => {
        if (event.key === "Enter") {
            sendChatButton.click();
        }
    });

    function loadPuzzlePieces(pieces) {
        const piecesGrid = document.getElementById("pieces-grid");

        pieces.forEach((piece) => {
            if (piece.is_placed) {
                placePieceOnGrid(piece.id, piece.x, piece.y, piece.image_url);
            } else {
                const pieceElement = document.createElement("div");
                pieceElement.classList.add("piece");
                pieceElement.dataset.pieceId = piece.id;
                pieceElement.style.backgroundImage = `url('${piece.image_url}')`;

                pieceElement.addEventListener("click", () => {
                    if (selectedPiece) selectedPiece.classList.remove("selected");
                    selectedPiece = pieceElement;
                    pieceElement.classList.add("selected");
                });

                piecesGrid.appendChild(pieceElement);
            }
        });
    }

    // Place a piece on the grid
    function placePiece(square, gridX, gridY) {
        if (selectedPiece) {
            const pieceId = selectedPiece.dataset.pieceId;
    
            const newX = gridX * baseGridSize;
            const newY = gridY * baseGridSize;
    
            console.log(`🛠 Placing piece ${pieceId} at grid (${gridX}, ${gridY}) -> (${newX}, ${newY}) with base size: ${baseGridSize}`);
    
            placePieceOnGrid(pieceId, newX, newY);
            sendMove(pieceId, newX, newY);
    
            selectedPiece.remove();
            selectedPiece = null;
        }
    }


    function placePieceOnGrid(pieceId, x, y, imageUrl = pieceImages[pieceId]) {
        // Update the piece's position in the UI
        const pieceElement = document.querySelector(`[data-piece-id="${pieceId}"]`);
        if (pieceElement) {
            pieceElement.style.left = `${x}px`;
            pieceElement.style.top = `${y}px`;
        }
    
        // Update the piece's position in piecesData
        const piece = piecesData.find(p => p.id === pieceId);
        if (piece) {
            piece.x = x;
            piece.y = y;
        } else {
        }
    
        // Load and create an image node using Konva
        const imageObj = new Image();
        imageObj.src = imageUrl;
    
        imageObj.onload = () => {
            if (!layer) {
                return;
            }
    
            // Create a Konva Image node
            const imageNode = new Konva.Image({
                x: x,
                y: y,
                width: baseGridSize, 
                height: baseGridSize,
                image: imageObj,
                id: `piece-${pieceId}`,
            });
    
            imageNode.on("contextmenu", (e) => {
                e.evt.preventDefault();
                removePiece(pieceId);
            });
    
            layer.add(imageNode);
            layer.draw();
    
            checkPiecePosition(pieceId, x, y);
        };
    
        imageObj.onerror = () => {
        };
    }
    

    function checkPiecePosition(pieceId, x, y) {
        const piece = piecesData.find(p => p.id === pieceId);
        if (piece) {
            // Calculate which grid cell the piece is in
            const currentGridX = Math.floor(x / baseGridSize);
            const currentGridY = Math.floor(y / baseGridSize);

            // The backend already provides grid positions in grid coordinates
            const expectedGridX = piece.grid_x;
            const expectedGridY = piece.grid_y;

            if (currentGridX === expectedGridX && currentGridY === expectedGridY) {
                piece.is_correct = true;
                highlightPiece(pieceId, "green");
            } else {
                piece.is_correct = false;
                highlightPiece(pieceId, "red");
            }

            // Check if all pieces are in the correct position
            checkPuzzleCompletion();
        }
    }

    function highlightPiece(pieceId, color) {
        const pieceElement = document.querySelector(`[data-piece-id="${pieceId}"]`);
        if (pieceElement) {
            console.log(`🔹 Highlighting piece ${pieceId} with ${color}`);
            pieceElement.style.border = `2px solid ${color}`;
        } 
    }
    
    function removePiece(pieceId) {
        if (document.getElementById("completion-modal")) {
            return;
        }
    
        removePieceFromGrid(pieceId);
    
        socket.send(
            JSON.stringify({
                type: "piece_remove",
                piece_id: pieceId,
                player_role: playerRole,
            })
        );
    }
    

    function removePieceFromGrid(pieceId) {
        const piece = layer.findOne(`#piece-${pieceId}`);
        if (piece) {
            piece.destroy();
            layer.draw();
        }
    }

    // Send WebSocket messages
    function sendMove(pieceId, newX, newY) {
        socket.send(
            JSON.stringify({
                type: "piece_move",
                piece_id: pieceId,
                new_x: newX,
                new_y: newY,
                player_role: playerRole,
                base_grid_size: baseGridSize,
            })
        );
    }

    function sendLock(pieceId) {
        if (!socket || socket.readyState !== WebSocket.OPEN) {
            return;
        }
    
        socket.send(JSON.stringify({
            type: "piece_lock",
            piece_id: pieceId,
            player_role: playerRole
        }));
    }

    function sendUnlock(pieceId) {
        const pieceElement = document.querySelector(`[data-piece-id="${pieceId}"]`);
        if (!pieceElement) {
            return;
        }
    
        pieceElement.removeAttribute("data-locked-by");
        pieceElement.classList.remove("selected"); // Remove highlight
    
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({
                type: "piece_unlock",
                piece_id: pieceId
            }));
        }
    }
    document.addEventListener("click", (event) => {
        const clickedPiece = event.target.closest('.piece');
        if (!clickedPiece) return;
    
        const pieceId = clickedPiece.dataset.pieceId;
        const lockedBy = clickedPiece.getAttribute("data-locked-by");
    
        if (lockedBy && lockedBy !== playerRole) {
            return;
        }
    
        if (lastLockedPiece && lastLockedPiece !== clickedPiece) {
            sendUnlock(lastLockedPiece.dataset.pieceId);
            lastLockedPiece.classList.remove("locked"); // Remove locked class
        }
    
        selectedPiece = clickedPiece;
        clickedPiece.classList.add("locked"); // Mark as locked
        lastLockedPiece = clickedPiece; // Store as last locked piece
    
        console.log(`🔒 Locking piece: ${pieceId}`);
        sendLock(pieceId);
    });



    // Initialize the game
    createGrid();
    loadPuzzlePieces(piecesData);
});

    
document.getElementById("toggle-chat").addEventListener("click", () => {
    document.getElementById("chat-container").classList.toggle("collapsed");
    });


document.addEventListener("DOMContentLoaded", () => {
    const previewButton = document.getElementById("preview-button");
    const modal = document.getElementById("puzzle-preview-modal");
    const modalImg = document.getElementById("puzzle-preview-image");
    const closeBtn = modal.querySelector(".close");

    previewButton.addEventListener("click", () => {
        if (puzzleImageUrl) {
            modal.style.display = "block";
            modalImg.src = puzzleImageUrl;
        }
    });

    closeBtn.addEventListener("click", () => {
        modal.style.display = "none";
    });

    // Close modal when clicking outside the image
    modal.addEventListener("click", (event) => {
        if (event.target === modal) {
            modal.style.display = "none";
        }
    });
});