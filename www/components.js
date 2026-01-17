/**
 * Component Loader
 * Loads header and footer dynamically and handles active state
 */
async function loadComponents() {
    try {
        // Load Header
        const headerResponse = await fetch('header.html');
        if (!headerResponse.ok) throw new Error('Failed to load header');
        const headerHtml = await headerResponse.text();
        
        const headerPlaceholder = document.getElementById('header-placeholder');
        if (headerPlaceholder) {
            headerPlaceholder.outerHTML = headerHtml;
        } else {
             // Fallback: insert at the beginning of body
             document.body.insertAdjacentHTML('afterbegin', headerHtml);
        }

        // Highlight active link based on current page
        const currentPath = window.location.pathname.split('/').pop() || 'index.html';
        const navLinks = document.querySelectorAll('nav a');
        
        navLinks.forEach(link => {
            const linkPath = link.getAttribute('href');
            // Check if exact match or if currentPath is empty/index.html and link is index.html
            if (linkPath === currentPath) {
                link.classList.add('active');
            }
        });
        
        // Dispatch event to notify that header is ready (for ThemeToggle)
        document.dispatchEvent(new Event('headerLoaded'));

        // Load Footer
        const footerResponse = await fetch('footer.html');
        if (!footerResponse.ok) throw new Error('Failed to load footer');
        const footerHtml = await footerResponse.text();
        
        const footerPlaceholder = document.getElementById('footer-placeholder');
        if (footerPlaceholder) {
            footerPlaceholder.outerHTML = footerHtml;
        } else {
             document.body.insertAdjacentHTML('beforeend', footerHtml);
        }

    } catch (error) {
        console.error('Error loading components:', error);
    }
}

// Start loading when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadComponents);
} else {
    loadComponents();
}
