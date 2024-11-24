//C:\Users\beka\OneDrive\Desktop\Year4DjangoMajor-Project\DjangoProject\PuzzleRoom\rooms\static\user\js\CreateRoom.js
document.addEventListener('DOMContentLoaded', () => {
    const createRoomForm = document.getElementById('createRoomForm');
    const createRoomBtn = document.getElementById('createRoomBtn');
    const dragArea = document.getElementById('dragArea');
    const fileInput = document.getElementById('fileInput');
    const imagePreview = document.getElementById('imagePreview');

    // Handle drag-and-drop events
    dragArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        dragArea.classList.add('active');
    });

    dragArea.addEventListener('dragleave', () => {
        dragArea.classList.remove('active');
    });

    dragArea.addEventListener('drop', (e) => {
        e.preventDefault();
        dragArea.classList.remove('active');
        fileInput.files = e.dataTransfer.files;
        displayImagePreview(fileInput.files[0]);  // Show the preview
    });

    // Open file input when clicking the browse link
    document.getElementById('browseLink').onclick = (e) => {
        e.preventDefault();
        fileInput.click();
    };

    // Handle file input change for image preview
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            displayImagePreview(file);  // Show the preview
        }
    });

    // Function to display the selected image preview
    function displayImagePreview(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            imagePreview.src = e.target.result;
            imagePreview.style.display = 'block';  // Show the preview
        };
        reader.readAsDataURL(file);  // Read the file as a data URL
    }

    // Handle form submission
    createRoomBtn.onclick = (e) => {
        e.preventDefault();
        const csrftoken = document.querySelector('[name=csrf-token]').content;

        const formData = new FormData(createRoomForm);
        formData.append('puzzleImage', fileInput.files[0]);

        fetch('/sliding_puzzle/create-room/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                console.log('Room created with ID:', data.room_id);
                window.location.href = `/sliding_puzzle/${data.room_id}/`;  // Redirect the user to the room
            } else {
                console.error('Error creating room:', data.error);
            }
        });
    };
});
