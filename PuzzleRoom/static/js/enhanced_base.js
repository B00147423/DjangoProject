document.addEventListener('DOMContentLoaded', function() {
    // Smooth scrolling for navigation links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });

    // Auto-scroll testimonials
    const testimonialSlider = document.querySelector('.testimonial-slider');
    let scrollPosition = 0;
    const testimonialWidth = testimonialSlider.querySelector('.testimonial').offsetWidth;

    function autoScroll() {
        scrollPosition += testimonialWidth;
        if (scrollPosition >= testimonialSlider.scrollWidth) {
            scrollPosition = 0;
        }
        testimonialSlider.scrollTo({
            left: scrollPosition,
            behavior: 'smooth'
        });
    }

    setInterval(autoScroll, 5000); // Auto-scroll every 5 seconds
});

