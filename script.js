/* ============================================================
   HAMMER & PIXELS - Interactive Scripts
   Scroll reveals, navigation, form validation
   Purposeful, smooth interactions -- not flashy
   ============================================================ */

(function () {
    'use strict';

    /* ---- NAVBAR SCROLL EFFECT ---- */
    var navbar = document.getElementById('navbar');

    function handleNavScroll() {
        var scrollY = window.scrollY;
        if (scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    }

    window.addEventListener('scroll', handleNavScroll, { passive: true });
    handleNavScroll();


    /* ---- MOBILE HAMBURGER MENU ---- */
    var hamburger = document.getElementById('hamburger');
    var navMenu = document.getElementById('navMenu');

    if (hamburger && navMenu) {
        hamburger.addEventListener('click', function () {
            var isOpen = navMenu.classList.toggle('open');
            hamburger.classList.toggle('active');
            hamburger.setAttribute('aria-expanded', isOpen);
            document.body.style.overflow = isOpen ? 'hidden' : '';
        });

        // Close menu when a link is clicked
        navMenu.querySelectorAll('a').forEach(function (link) {
            link.addEventListener('click', function () {
                navMenu.classList.remove('open');
                hamburger.classList.remove('active');
                hamburger.setAttribute('aria-expanded', 'false');
                document.body.style.overflow = '';
            });
        });

        // Close on Escape key
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && navMenu.classList.contains('open')) {
                navMenu.classList.remove('open');
                hamburger.classList.remove('active');
                hamburger.setAttribute('aria-expanded', 'false');
                document.body.style.overflow = '';
                hamburger.focus();
            }
        });
    }


    /* ---- SMOOTH SCROLL FOR ANCHOR LINKS ---- */
    document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
        anchor.addEventListener('click', function (e) {
            var href = this.getAttribute('href');
            if (href === '#') return;
            var target = document.querySelector(href);
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });


    /* ---- SCROLL REVEAL ---- */
    function initScrollReveal() {
        var elements = document.querySelectorAll('[data-reveal]');
        if (!elements.length) return;

        // Respect reduced motion preference
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            elements.forEach(function (el) {
                el.classList.add('revealed');
            });
            return;
        }

        var observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    var el = entry.target;
                    var delay = parseInt(el.getAttribute('data-delay') || '0', 10);
                    setTimeout(function () {
                        el.classList.add('revealed');
                    }, delay);
                    observer.unobserve(el);
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -60px 0px'
        });

        elements.forEach(function (el) {
            observer.observe(el);
        });
    }

    initScrollReveal();


    /* ---- FORM VALIDATION & SUBMISSION FEEDBACK ---- */
    var form = document.querySelector('.contact-form');
    if (form) {
        var submitBtn = form.querySelector('.btn-submit');

        form.addEventListener('submit', function (e) {
            var requiredFields = form.querySelectorAll('[required]');
            var isValid = true;

            requiredFields.forEach(function (field) {
                // Remove any prior error state
                field.classList.remove('field-error');

                if (!field.value.trim()) {
                    isValid = false;
                    field.classList.add('field-error');
                }

                // Basic email check
                if (field.type === 'email' && field.value.trim()) {
                    var emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                    if (!emailPattern.test(field.value.trim())) {
                        isValid = false;
                        field.classList.add('field-error');
                    }
                }
            });

            if (!isValid) {
                e.preventDefault();
                // Focus first error field
                var firstError = form.querySelector('.field-error');
                if (firstError) firstError.focus();
            } else {
                // Visual feedback while submitting
                if (submitBtn) {
                    submitBtn.disabled = true;
                    submitBtn.querySelector('span').textContent = 'Sending...';
                }
            }
        });

        // Clear error state on input
        form.querySelectorAll('input, textarea, select').forEach(function (field) {
            field.addEventListener('input', function () {
                this.classList.remove('field-error');
            });
        });
    }


    /* ---- ACTIVE NAV LINK HIGHLIGHTING ---- */
    function initActiveNavTracking() {
        var sections = document.querySelectorAll('section[id]');
        var navLinks = document.querySelectorAll('.nav-menu a[href^="#"]');

        if (!sections.length || !navLinks.length) return;

        var sectionObserver = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    var id = entry.target.getAttribute('id');
                    navLinks.forEach(function (link) {
                        link.classList.remove('active');
                        if (link.getAttribute('href') === '#' + id) {
                            link.classList.add('active');
                        }
                    });
                }
            });
        }, {
            threshold: 0.3,
            rootMargin: '-80px 0px -40% 0px'
        });

        sections.forEach(function (section) {
            sectionObserver.observe(section);
        });
    }

    initActiveNavTracking();


    /* ---- PORTFOLIO CARD HOVER DEPTH ---- */
    function initPortfolioInteraction() {
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

        var cards = document.querySelectorAll('.portfolio-card');
        cards.forEach(function (card) {
            card.addEventListener('mouseenter', function () {
                // Subtle scale on the mockup content
                var mockup = this.querySelector('.mockup-content');
                if (mockup) {
                    mockup.style.transition = 'transform 0.4s ease';
                    mockup.style.transform = 'scale(1.02)';
                }
            });
            card.addEventListener('mouseleave', function () {
                var mockup = this.querySelector('.mockup-content');
                if (mockup) {
                    mockup.style.transform = 'scale(1)';
                }
            });
        });
    }

    initPortfolioInteraction();

})();
