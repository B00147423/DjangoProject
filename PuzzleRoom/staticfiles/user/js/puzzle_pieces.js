// C:\Users\beka\OneDrive\Desktop\Year4DjangoMajor-Project\DjangoProject\PuzzleRoom\rooms\static\user\js\puzzle_pieces.js

document.addEventListener('DOMContentLoaded', () => {
    const pieces = document.querySelectorAll('.puzzle-piece');
    const dropArea = document.getElementById('dropArea');
    const roomId = dropArea.getAttribute('data-room-id');  // Fetch roomId from data attribute
    const csrftoken = document.querySelector('[name=csrf-token]').content;  // Fetch CSRF token from meta tag

    // Handle drag and drop functionality
    pieces.forEach(piece => {
        piece.addEventListener('dragstart', handleDragStart);
    });

    dropArea.addEventListener('dragover', handleDragOver);
    dropArea.addEventListener('drop', handleDrop);

    function handleDragStart(e) {
        e.dataTransfer.setData('text/plain', e.target.id);
    }

    function handleDragOver(e) {
        e.preventDefault();
    }

    // Here’s the handleDrop function
    function handleDrop(e) {
        e.preventDefault();
        const pieceId = e.dataTransfer.getData('text/plain');
        const draggedElement = document.getElementById(pieceId);
        dropArea.appendChild(draggedElement);

        // Collect the new positions of all pieces
        const newPositions = [];
        document.querySelectorAll('.puzzle-piece').forEach(piece => {
            newPositions.push(piece.src);
        });

        // Send the updated positions to the backend
        fetch(`/rooms/save-puzzle-state/${roomId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken,
            },
            body: JSON.stringify({ pieces: newPositions })
        }).then(response => response.json())
          .then(data => {
              if (data.status === 'success') {
                  console.log('Puzzle state saved successfully');
              } else {
                  console.error('Error saving puzzle state');
              }
          });
    }
});
