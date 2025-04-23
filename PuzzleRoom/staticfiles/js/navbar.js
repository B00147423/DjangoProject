//C:\Users\beka\OneDrive\Desktop\Year4DjangoMajor-Project\DjangoProject\PuzzleRoom\static\js\navbar.js
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM Content Loaded');
    
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    
    console.log('Toggle button:', sidebarToggle);
    console.log('Sidebar:', sidebar);

    // Set initial state from localStorage
    const isSidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    if (isSidebarCollapsed && window.innerWidth > 768) {
        sidebar.classList.add('collapsed');
    }

    function toggleSidebar(e) {
        console.log('Toggle clicked');
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        if (window.innerWidth <= 768) {
            console.log('Mobile toggle');
            sidebar.classList.toggle('active');
        } else {
            console.log('Desktop toggle');
            sidebar.classList.toggle('collapsed');
            localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
        }
    }

    if (sidebarToggle && sidebar) {
        console.log('Adding click listener to toggle button');
        // Handle click on toggle button
        sidebarToggle.addEventListener('click', toggleSidebar);

        // Handle keyboard shortcuts
        document.addEventListener('keydown', function(e) {
            // Alt + S to toggle sidebar
            if (e.altKey && e.key.toLowerCase() === 's') {
                e.preventDefault();
                toggleSidebar();
            }
            // Escape to close sidebar on mobile
            if (e.key === 'Escape' && window.innerWidth <= 768) {
                sidebar.classList.remove('active');
            }
        });

        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', function(event) {
            if (window.innerWidth <= 768) {
                const isClickInsideSidebar = sidebar.contains(event.target) || sidebarToggle.contains(event.target);
                if (!isClickInsideSidebar && sidebar.classList.contains('active')) {
                    sidebar.classList.remove('active');
                }
            }
        });

        // Handle window resize
        let resizeTimer;
        window.addEventListener('resize', function() {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(function() {
                if (window.innerWidth > 768) {
                    sidebar.classList.remove('active');
                    if (localStorage.getItem('sidebarCollapsed') === 'true') {
                        sidebar.classList.add('collapsed');
                    }
                } else {
                    sidebar.classList.remove('collapsed');
                }
            }, 250);
        });
    } else {
        console.error('Could not find sidebar or toggle button!');
    }

    // Add active class to current page link
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-links a').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
            link.closest('.nav-item')?.classList.add('active');
        }
    });
});