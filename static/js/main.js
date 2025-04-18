// Main JavaScript file for enhanced UI interactions

document.addEventListener('DOMContentLoaded', function() {
    // Reveal animations on scroll
    const revealElements = document.querySelectorAll('.reveal');
    
    function checkReveal() {
        revealElements.forEach(element => {
            const elementTop = element.getBoundingClientRect().top;
            const windowHeight = window.innerHeight;
            if (elementTop < windowHeight - 100) {
                element.classList.add('active');
            }
        });
    }

    // Initial check and scroll listener
    checkReveal();
    window.addEventListener('scroll', checkReveal, { passive: true });

    // Accordion functionality
    const accordionItems = document.querySelectorAll('.accordion-item');
    
    accordionItems.forEach(item => {
        const header = item.querySelector('.accordion-header');
        if (header) {
            header.addEventListener('click', () => {
                // Close all other items
                accordionItems.forEach(otherItem => {
                    if (otherItem !== item && otherItem.classList.contains('active')) {
                        otherItem.classList.remove('active');
                    }
                });
                // Toggle current item
                item.classList.toggle('active');
            });
        }
    });

    // Custom file input enhancement
    const fileInputs = document.querySelectorAll('.custom-file-input input[type="file"]');
    
    fileInputs.forEach(input => {
        const wrapper = input.closest('.custom-file-input');
        const fileNameDisplay = wrapper.querySelector('.file-name');
        
        input.addEventListener('change', (e) => {
            if (input.files.length > 0) {
                wrapper.classList.add('has-file');
                if (fileNameDisplay) {
                    fileNameDisplay.textContent = input.files[0].name;
                }
            } else {
                wrapper.classList.remove('has-file');
                if (fileNameDisplay) {
                    fileNameDisplay.textContent = '';
                }
            }
        });
    });

    // Page loader
    const pageLoader = document.querySelector('.page-loader');
    if (pageLoader) {
        window.addEventListener('load', () => {
            setTimeout(() => {
                pageLoader.classList.add('loaded');
                // Remove from DOM after transition ends
                setTimeout(() => {
                    pageLoader.remove();
                }, 500);
            }, 300);
        });
    }

    // Tooltips initialization
    const tooltips = document.querySelectorAll('.tooltip');
    tooltips.forEach(tooltip => {
        // Mobile-friendly tooltip handling
        ['click', 'touchstart'].forEach(evt => {
            tooltip.addEventListener(evt, e => {
                e.preventDefault();
                e.stopPropagation();
                tooltip.classList.toggle('active');
            });
        });

        // Hide tooltip when clicking elsewhere
        document.addEventListener('click', e => {
            if (!tooltip.contains(e.target)) {
                tooltip.classList.remove('active');
            }
        });
    });

    // ScrollSpy navigation
    const scrollSpyInit = () => {
        const sections = document.querySelectorAll('[data-scrollspy]');
        const navLinks = document.querySelectorAll('.scroll-nav-link');
        
        if (sections.length && navLinks.length) {
            window.addEventListener('scroll', () => {
                let current = '';
                
                sections.forEach(section => {
                    const sectionTop = section.offsetTop;
                    const sectionHeight = section.clientHeight;
                    if (window.pageYOffset >= sectionTop - 100) {
                        current = section.getAttribute('id');
                    }
                });
                
                navLinks.forEach(link => {
                    link.classList.remove('active');
                    if (link.getAttribute('href').slice(1) === current) {
                        link.classList.add('active');
                    }
                });
            });
        }
    };
    
    scrollSpyInit();

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]:not([href="#"])').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 80,
                    behavior: 'smooth'
                });
                
                // Update URL without page reload
                history.pushState(null, null, targetId);
            }
        });
    });

    // Dark mode toggle (if implemented)
    const darkModeToggle = document.querySelector('.dark-mode-toggle');
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', () => {
            document.body.classList.toggle('dark-mode');
            // Store preference in localStorage
            const isDarkMode = document.body.classList.contains('dark-mode');
            localStorage.setItem('darkMode', isDarkMode ? 'enabled' : 'disabled');
        });

        // Check for saved user preference
        if (localStorage.getItem('darkMode') === 'enabled') {
            document.body.classList.add('dark-mode');
        }
    }

    // Form validation enhancement
    const forms = document.querySelectorAll('form[data-validate]');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    // Add error class to parent for styling
                    field.closest('.form-group')?.classList.add('has-error');
                    
                    // Create or update error message
                    let errorMsg = field.parentNode.querySelector('.error-message');
                    if (!errorMsg) {
                        errorMsg = document.createElement('div');
                        errorMsg.className = 'error-message';
                        field.parentNode.appendChild(errorMsg);
                    }
                    errorMsg.textContent = 'This field is required';
                } else {
                    field.closest('.form-group')?.classList.remove('has-error');
                    const errorMsg = field.parentNode.querySelector('.error-message');
                    if (errorMsg) errorMsg.remove();
                }
            });
            
            if (!isValid) {
                e.preventDefault();
            }
        });
    });
});

// Page transition effect for navigation
document.addEventListener('click', function(e) {
    const link = e.target.closest('a');
    if (link && !link.getAttribute('href').startsWith('#') && 
        !link.getAttribute('href').startsWith('javascript:') && 
        !e.ctrlKey && !e.metaKey) {
        
        e.preventDefault();
        document.body.classList.add('page-transition-out');
        
        setTimeout(() => {
            window.location.href = link.href;
        }, 300);
    }
});