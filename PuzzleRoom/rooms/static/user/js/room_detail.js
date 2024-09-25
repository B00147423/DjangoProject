document.addEventListener('DOMContentLoaded', function () {
    const dropArea = document.getElementById('dropArea');
    const puzzlePieces = document.querySelectorAll('.puzzle-piece');
    const roomName = dropArea.getAttribute('data-room-name'); 

    let draggedPiece = null;

    const socket = new WebSocket(`ws://${window.location.host}/ws/room/${roomName}/`)

    socket.onopen = () =>{
        console.log('WebSocket connection established.');
    }

    socket.onmessage = (event) =>{
        const data = JSON.parse(event.data);
        const piece = document.getElementById(`piece-${data.piece_id}`);
        const targetCell = document.querySelector(`[data-row='${data.row}'][data-col='${data.col}']`);
        
        if (targetCell && piece) {
            targetCell.appendChild(piece);
            piece.style.position = 'absolute';
            piece.style.left = '0';
            piece.style.top = '0';
        }
    };

    socket.onclose= () =>{
        console.log('WebSocket connection closed.');
    }

    // Allow pieces to be dragged
    puzzlePieces.forEach(piece => {
        piece.addEventListener('dragstart', function (e) {
            draggedPiece = e.target;
            e.dataTransfer.setData('text/plain', e.target.dataset.pieceIndex);
        });
    });

    dropArea.addEventListener('dragover', function(e){
        e.preventDefault();
    });

    dropArea.addEventListener('drop', function(e) {
        e.preventDefault();

        const pieceIndex = e.dataTransfer.getData('text/plain');
        const droppedPiece = document.querySelector(`[data-piece-index='${pieceIndex}']`);

        const targetRow =e.target.getAttribute('data-row');
        const targetCol =e.target.getAttribute('data-col');

        if(socket.readyState === WebSocket.OPEN){
            socket.send(JSON.strringify({
                'piece_id': pieceIndex,
                'col_target': targetCol,
                'row_target': targetRow
            }))
        }

         // Snap the piece in place
        e.target.appendChild(droppedPiece);
        droppedPiece.style.position = 'absolute';
        droppedPiece.style.left = '0';
        droppedPiece.style.top = '0';
    });  
});
