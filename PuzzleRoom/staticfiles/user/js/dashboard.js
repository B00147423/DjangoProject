document.addEventListener('DOMContentLoaded', function() {
    // Modal handling
    function toggleModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = modal.style.display === "block" ? "none" : "block";
        }
    }

    // Close modal when clicking outside
    window.onclick = function(event) {
        if (event.target.classList.contains('modal')) {
            event.target.style.display = "none";
        }
    };

    // Close modal when pressing escape key
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            const modals = document.querySelectorAll('.modal');
            modals.forEach(modal => {
                modal.style.display = 'none';
            });
        }
    });

    // Add click event listeners to all modal close buttons
    const closeButtons = document.querySelectorAll('.close');
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const modal = button.closest('.modal');
            if (modal) {
                modal.style.display = 'none';
            }
        });
    });

    // Make modal functions globally available
    window.toggleModal = toggleModal;
});
