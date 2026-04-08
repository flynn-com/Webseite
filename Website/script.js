// Basic animation on scroll
document.addEventListener('DOMContentLoaded', () => {

    const projectContainer = document.querySelector('.spacer-bottom');
    if (projectContainer) {
        // Load projects from static data.js file
        const projects = window.initialProjects || [];

        // Sort by number just in case
        // Sort Descending because we use 'afterend' (prepend behavior)
        // This ensures #01 is at the TOP physically in the DOM
        projects.sort((a, b) => b.number - a.number);

        // Inject HTML
        // Insert AFTER the title, or before spacer if title not found
        const title = document.querySelector('.project-section-title');
        const target = title ? title : projectContainer;
        const position = title ? 'afterend' : 'beforebegin';

        projects.forEach(p => {
            const html = createProjectHTML(p);
            target.insertAdjacentHTML(position, html);
        });

        // Re-run observer attachment after injection
        attachObservers();

        // Preload all project images silently in the background
        // so they are cached before the user opens a card
        preloadProjectImages(projects);
    }

    // Initialize carousels
    document.querySelectorAll('.v2-carousel').forEach(initCarousel);
});

// Preloads all project gallery images in the background after page load
// Uses requestIdleCallback (or setTimeout fallback) to not block the main thread
function preloadProjectImages(projects) {
    const allImages = [];

    projects.forEach(p => {
        if (p.gallery && p.gallery.length > 0) {
            // Add all gallery images to the preload queue
            p.gallery.forEach(src => allImages.push(src));
        }
        if (p.companyLogo) allImages.push(p.companyLogo);
    });

    // Preload in small batches using idle time, so it doesn't compete with
    // critical resources (background image, fonts, CSS)
    let idx = 0;
    const BATCH_SIZE = 3; // Load 3 images per idle callback

    function loadNextBatch() {
        const end = Math.min(idx + BATCH_SIZE, allImages.length);
        for (; idx < end; idx++) {
            const img = new Image();
            img.src = allImages[idx];
        }
        if (idx < allImages.length) {
            if ('requestIdleCallback' in window) {
                requestIdleCallback(loadNextBatch, { timeout: 2000 });
            } else {
                setTimeout(loadNextBatch, 100);
            }
        }
    }

    // Start after a short delay so the page renders first
    if ('requestIdleCallback' in window) {
        requestIdleCallback(loadNextBatch, { timeout: 1500 });
    } else {
        setTimeout(loadNextBatch, 500);
    }
}

// SCROLL-DRIVEN ANIMATION ENGINE
// Replaces IntersectionObserver with direct scroll calculation
function attachObservers() {
    const cards = document.querySelectorAll('.project-card');

    // Pre-cache all DOM references once — avoids repeated querySelector on every frame
    const cardElements = Array.from(cards).map(card => ({
        card,
        barContent: card.querySelector('.bar-content'),
        fullContent: card.querySelector('.full-content'),
        wrapper: card.closest('.sticky-wrapper')
    }));

    // Set constant styles once during setup — never touch them again in the scroll loop
    cardElements.forEach(({ card }) => {
        card.style.width = '90vw';
        card.style.borderRadius = '32px';
    });

    // Cache viewport dimensions and breakpoint flags
    // Recalculated only on resize/orientationchange, not on every scroll frame
    let viewportHeight = window.innerHeight;
    let isMobile = window.innerWidth <= 768;
    let isTablet = window.innerWidth > 768 && window.innerWidth <= 1200;

    function updateViewport() {
        viewportHeight = window.innerHeight;
        isMobile = window.innerWidth <= 768;
        isTablet = window.innerWidth > 768 && window.innerWidth <= 1200;
        onScroll();
    }

    // Debounced resize listener
    let resizeTimer;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(updateViewport, 200);
    });

    // iOS Safari: orientationchange fires before innerHeight updates — add a small delay
    window.addEventListener('orientationchange', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(updateViewport, 300);
    });

    // rAF deduplication flag — prevents queuing multiple frames per scroll burst
    let rafScheduled = false;

    function onScroll() {
        rafScheduled = false;

        const startPoint = viewportHeight * 0.60;
        const endPoint   = viewportHeight * 0.20;
        const minHeight  = 80;
        const maxHeight  = isMobile
            ? Math.max(viewportHeight * 0.88, 560)
            : isTablet
                ? Math.max(viewportHeight * 0.85, 620)
                : viewportHeight * 0.8;

        // PHASE 1 — Batch all layout reads (getBoundingClientRect)
        // Reading everything before any write prevents forced reflows between cards
        const rects = cardElements.map(({ card }) => card.getBoundingClientRect());

        // PHASE 2 — Batch all style writes
        cardElements.forEach(({ card, barContent, fullContent, wrapper }, i) => {
            const rect = rects[i];

            let progress = (startPoint - rect.top) / (startPoint - endPoint);
            progress = Math.max(0, Math.min(1, progress));

            if (wrapper) {
                wrapper.style.marginBottom = `${15 + 55 * progress}px`;
            }

            card.style.height = `${minHeight + (maxHeight - minHeight) * progress}px`;
            card.style.overflow = (isMobile && progress >= 0.98) ? 'visible' : 'hidden';
            card.style.background = `rgba(255,255,255,${0.1 + 0.05 * progress})`;

            if (barContent) {
                barContent.style.opacity = Math.max(0, 1 - progress * 2);
                barContent.style.pointerEvents = progress > 0.5 ? 'none' : 'all';
            }

            if (fullContent) {
                fullContent.style.opacity = Math.max(0, (progress - 0.3) / 0.7);
                fullContent.style.pointerEvents = progress > 0.8 ? 'all' : 'none';
            }
        });
    }

    // Scroll listener with passive flag + rAF deduplication
    window.addEventListener('scroll', () => {
        if (!rafScheduled) {
            rafScheduled = true;
            window.requestAnimationFrame(onScroll);
        }
    }, { passive: true });

    // Initial call
    onScroll();
}

// Carousel Navigation Logic
function initCarousel(carousel) {
    const track = carousel.querySelector('.v2-carousel-track');
    // Store current index on the DOM element for simplicity
    track.dataset.currentIndex = 0;
}

window.moveCarousel = function (button, direction, e) {
    // Stop click from bubbling up to the card
    if (e) { e.preventDefault(); e.stopPropagation(); }

    const carousel = button.closest('.v2-carousel');
    const track = carousel.querySelector('.v2-carousel-track');
    const items = track.querySelectorAll('.carousel-item');
    const totalItems = items.length;

    if (totalItems <= 1) return; // Nothing to slide

    let currentIndex = parseInt(track.dataset.currentIndex || 0);

    currentIndex += direction;

    // Wrap-around looping
    if (currentIndex < 0) {
        currentIndex = totalItems - 1;
    } else if (currentIndex >= totalItems) {
        currentIndex = 0;
    }

    track.dataset.currentIndex = currentIndex;

    // Calculate translation percentage
    const translateX = -(currentIndex * 100);
    track.style.transform = `translateX(${translateX}%)`;

    // Update button opacity
    const prevBtn = carousel.querySelector('.carousel-prev');
    const nextBtn = carousel.querySelector('.carousel-next');

    if (prevBtn) prevBtn.style.opacity = currentIndex === 0 ? '0.2' : '1';
    if (nextBtn) nextBtn.style.opacity = currentIndex === totalItems - 1 ? '0.2' : '1';
};

// Helper to generic HTML
const createProjectHTML = (p) => {
    // Resolve images
    let mainImg = p.companyLogo || null; // Left column is now company logo
    let startImg = p.image || null;      // Right column "Startbild"
    let galleryHtml = '';

    // Build Project Capability Icons
    let iconsHtml = '';
    let iconList = '';
    if (p.hasPhoto) {
        iconList += `<div class="p-cap-icon" title="Photography">
                        <div class="icon-circle"><svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path><circle cx="12" cy="13" r="4"></circle></svg></div>
                        <span class="icon-label">Photo</span>
                     </div>`;
    }
    if (p.hasVideo) {
        iconList += `<div class="p-cap-icon" title="Videography">
                        <div class="icon-circle"><svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><polygon points="23 7 16 12 23 17 23 7"></polygon><rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect></svg></div>
                        <span class="icon-label">Video</span>
                     </div>`;
    }
    if (p.hasDesign) {
        iconList += `<div class="p-cap-icon" title="Design">
                        <div class="icon-circle"><svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19l7-7 3 3-7 7-3-3z"></path><path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z"></path><path d="M2 2l7.586 7.586"></path><circle cx="11" cy="11" r="2"></circle></svg></div>
                        <span class="icon-label">Design</span>
                     </div>`;
    }

    if (iconList) {
        iconsHtml = `<div class="project-capabilities">${iconList}</div>`;
    }

    // Build Gallery/Carousel
    if (p.gallery && p.gallery.length > 0) {
        let slides = '';
        p.gallery.forEach((img, i) => {
            const imgLoading = (i === 0) ? 'eager' : 'lazy';
            slides += `<div class="carousel-item"><img src="${img}" alt="${p.title} - Galeriebild ${i+1}" loading="${imgLoading}" decoding="async"></div>`;
        });

        galleryHtml = `
        <div class="v2-half-img v2-carousel">
            <div class="v2-carousel-track" data-current-index="0">
                ${slides}
            </div>
            <button class="carousel-btn carousel-prev" onclick="moveCarousel(this, -1, event)">
                <svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
            </button>
            <button class="carousel-btn carousel-next" onclick="moveCarousel(this, 1, event)">
                <svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
            </button>
        </div>
        `;
    }

    return `
    <div class="sticky-wrapper">
        <article class="project-card">
            <!-- Bar State -->
            <div class="bar-content">
                <span class="bar-number">${p.number}</span>
                <span class="bar-title">${p.title}</span>
                <span class="bar-icon">→</span>
            </div>

            <!-- Expanded State -->
            <div class="full-content">
                <div class="card-grid-v2">
                    
                    <!-- LEFT COLUMN: Startbild (Large) with Logo Overlay -->
                    <div class="col-left">
                         ${p.image ? `<img src="${p.image}" class="main-feature-img" alt="${p.title}" loading="eager" decoding="async">` : `<div class="placeholder-box">IMG</div>`}
                         ${p.companyLogo ? `<img src="${p.companyLogo}" class="project-company-logo" alt="${p.title} Logo" loading="lazy" decoding="async">` : ''}
                    </div>
                    
                    <!-- RIGHT COLUMN: Content -->
                    <div class="col-right">
                        <header class="v2-header">
                            <div class="v2-number">${p.bigNumber}</div>
                            <div class="v2-details">${p.headerDetails}</div>
                        </header>
                        
                        <div class="title-row-v2">
                            <div class="v2-title">${p.title}</div>
                            <a href="single_project.html?id=${p.id}" class="btn-view-project">
                                VIEW 
                                <svg class="view-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
                                    <line x1="10" y1="12" x2="22" y2="12"></line>
                                    <polyline points="16 6 22 12 16 18"></polyline>
                                </svg>
                            </a>
                        </div>
                        
                        <div class="v2-desc">
                            ${p.shortDescription || "No short description."}
                        </div>
                        
                        ${iconsHtml}
                        
                        <div class="v2-secondary-area">
                             ${galleryHtml}
                             
                             <a href="single_project.html?id=${p.id}" class="btn-view-project btn-view-mobile">
                                 VIEW 
                                 <svg class="view-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
                                     <line x1="10" y1="12" x2="22" y2="12"></line>
                                     <polyline points="16 6 22 12 16 18"></polyline>
                                 </svg>
                             </a>
                        </div>
                    </div>
                </div>
            </div>
        </article>
    </div>
`};

