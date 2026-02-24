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
    }

    // Initialize carousels
    document.querySelectorAll('.v2-carousel').forEach(initCarousel);
});

// SCROLL-DRIVEN ANIMATION ENGINE
// Replaces IntersectionObserver with direct scroll calculation
function attachObservers() {
    const cards = document.querySelectorAll('.project-card');

    // Config: Where the animation starts and ends (percent of viewport height)
    // 0.6 = Start expanding when top of card is at 60% of screen height (Almost middle)
    // 0.2 = Fully expanded when top of card is at 20% of screen height
    const startTrigger = 0.60;
    const endTrigger = 0.20;

    // Cache viewport height to prevent iOS Safari layout thrashing
    // (In iOS Safari, window.innerHeight changes as you scroll and the address bar shrinks/grows)
    let viewportHeight = window.innerHeight;

    // Add a debounced resize listener to update viewportHeight
    let resizeTimer;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
            viewportHeight = window.innerHeight;
            onScroll(); // Force a recalculation with new height
        }, 200);
    });

    function onScroll() {
        // Use cached height instead of reading window.innerHeight on every frame
        // This is a critical performance fix for Apple devices
        const currentViewportHeight = viewportHeight;

        cards.forEach(card => {
            const rect = card.getBoundingClientRect();
            const barContent = card.querySelector('.bar-content');
            const fullContent = card.querySelector('.full-content');

            // Calculate progress based on position
            // "top" decreases as we scroll down
            const startPoint = currentViewportHeight * startTrigger;
            const endPoint = currentViewportHeight * endTrigger;

            // Normalize progress (0 to 1)
            // 0 = at startPoint (Closed)
            // 1 = at endPoint (Open)
            let progress = (startPoint - rect.top) / (startPoint - endPoint);

            // Clamp progress
            progress = Math.max(0, Math.min(1, progress));

            // -- APPLY STYLES --

            // 1. DYNAMIC MARGIN (Wrapper)
            // Closed: 16px (1rem) -> Open: 140px (~15vh)
            // This pushes the next project down as this one opens
            const wrapper = card.closest('.sticky-wrapper');
            if (wrapper) {
                const minMargin = 15; // Set to 15px per request
                const maxMargin = 70;
                const currentMargin = minMargin + (maxMargin - minMargin) * progress;
                wrapper.style.marginBottom = `${currentMargin}px`;
            }

            // Height: 80px -> 80vh
            const minHeight = 80; // px
            // On mobile viewports we need giving the card more height so content isn't clipped
            const isMobile = window.innerWidth <= 768;
            // Provide at least 550px of height on mobile, but don't stretch excessively long
            const maxHeight = isMobile ? Math.max(currentViewportHeight * 0.85, 550) : currentViewportHeight * 0.8;
            const currentHeight = minHeight + (maxHeight - minHeight) * progress;
            card.style.height = `${currentHeight}px`;

            // Width: 90vw (always constant now per request)
            card.style.width = '90vw';

            // Border Radius: Constant 32px
            card.style.borderRadius = '32px';

            // Background: Fade
            const opacity = 0.1 + (0.05 * progress);
            card.style.background = `rgba(255, 255, 255, ${opacity})`;

            // Content Visibility
            // Initial Bar: Fade Out as we open
            if (barContent) {
                barContent.style.opacity = 1 - progress * 2; // Fade out quickly
                barContent.style.pointerEvents = progress > 0.5 ? 'none' : 'all';
            }

            // Full Content: Fade In as we open
            if (fullContent) {
                // Delay fade in slightly
                const contentProgress = Math.max(0, (progress - 0.3) / 0.7);
                fullContent.style.opacity = contentProgress;
                fullContent.style.pointerEvents = progress > 0.8 ? 'all' : 'none';
            }
        });
    }

    // Attach listener
    window.addEventListener('scroll', () => {
        window.requestAnimationFrame(onScroll);
    }, { passive: true }); // passive flag improves scroll performance on mobile

    // Initial call
    onScroll();
}

// Carousel Navigation Logic
function initCarousel(carousel) {
    const track = carousel.querySelector('.v2-carousel-track');
    // Store current index on the DOM element for simplicity
    track.dataset.currentIndex = 0;
}

window.moveCarousel = function (button, direction) {
    // Prevent default anchor behavior if applicable
    event.preventDefault();

    const carousel = button.closest('.v2-carousel');
    const track = carousel.querySelector('.v2-carousel-track');
    const items = track.querySelectorAll('.carousel-item');
    const totalItems = items.length;

    if (totalItems <= 1) return; // Nothing to slide

    let currentIndex = parseInt(track.dataset.currentIndex || 0);

    currentIndex += direction;

    // Bounds checking (loop around or stop at edges)
    // Let's stop at edges for a cleaner feel
    if (currentIndex < 0) {
        currentIndex = 0; // Or totalItems - 1 to loop
    } else if (currentIndex >= totalItems) {
        currentIndex = totalItems - 1; // Or 0 to loop
    }

    track.dataset.currentIndex = currentIndex;

    // Calculate translation percentage
    // Each item is 100% of the track's parent width
    const translateX = -(currentIndex * 100);
    track.style.transform = `translateX(${translateX}%)`;

    // Optional: Update button visibility based on bounds
    const prevBtn = carousel.querySelector('.carousel-prev');
    const nextBtn = carousel.querySelector('.carousel-next');

    if (prevBtn) prevBtn.style.opacity = currentIndex === 0 ? '0.2' : '1';
    if (nextBtn) nextBtn.style.opacity = currentIndex === totalItems - 1 ? '0.2' : '1';
};

// Helper to generic HTML
const createProjectHTML = (p) => {
    // Resolve images
    let mainImg = null;
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

    if (p.gallery && p.gallery.length > 0) {
        mainImg = p.gallery[0];

        if (p.gallery.length > 1) {
            let slides = '';
            for (let i = 1; i < p.gallery.length; i++) {
                slides += `<div class="carousel-item"><img src="${p.gallery[i]}" alt="Project Image"></div>`;
            }

            galleryHtml = `
            <div class="v2-half-img v2-carousel">
                <div class="v2-carousel-track" data-current-index="0">
                    ${slides}
                </div>
                <button class="carousel-btn carousel-prev" onclick="moveCarousel(this, -1)">
                    <svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
                </button>
                <button class="carousel-btn carousel-next" onclick="moveCarousel(this, 1)">
                    <svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
                </button>
            </div>
            `;
        }
    } else if (p.image) {
        mainImg = p.image;
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
                    
                    <!-- LEFT COLUMN: Main Feature Image (Rounded) -->
                    <div class="col-left">
                         ${mainImg ? `<img src="${mainImg}" class="main-feature-img" alt="Main">` : `<div class="placeholder-box">${p.mainImageText || 'IMG'}</div>`}
                         ${p.companyLogo ? `<img src="${p.companyLogo}" class="project-company-logo" alt="Company Logo">` : ''}
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
                        </div>
                    </div>
                </div>
            </div>
        </article>
    </div>
`};
