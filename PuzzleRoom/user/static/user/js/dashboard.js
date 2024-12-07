    function toggleModal(modalId) {
        var modal = document.getElementById(modalId);
        modal.style.display = modal.style.display === "block" ? "none" : "block";
    }

    window.onclick = function(event) {
        if (event.target.className === 'modal') {
            event.target.style.display = "none";
        }
    };
