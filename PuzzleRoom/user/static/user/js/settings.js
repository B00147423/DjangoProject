

document.addEventListener('DOMContentLoaded', function() {
    const passwordWarnings = document.querySelectorAll('.password-warning');
    
    passwordWarnings.forEach(warning => {
        const tooltip = document.createElement('div');
        tooltip.className = 'password-tooltip';
        tooltip.textContent = 'Password must be at least 8 characters long and include uppercase, lowercase, numbers, and special characters.';
        warning.appendChild(tooltip);

        warning.addEventListener('mouseover', function() {
            tooltip.style.display = 'block';
        });

        warning.addEventListener('mouseout', function() {
            tooltip.style.display = 'none';
        });
    });
});
