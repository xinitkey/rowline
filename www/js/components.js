/**
 * Theme Toggle (Expand) - Dark/Light mode switch
 */
class ThemeToggle {
    constructor() {
        this.storageKey = 'theme';
        this.toggleBtn = null;
        
        // Use MutationObserver to detect when the header (and button) is injected
        this.observer = new MutationObserver(() => this.tryInit());
        this.observer.observe(document.body, { childList: true, subtree: true });

        // Try to init immediately
        this.tryInit();
    }

    tryInit() {
        if (this.toggleBtn) return; // Already initialized

        this.toggleBtn = document.querySelector('.theme-toggle');
        if (this.toggleBtn) {
            this.init();
            this.observer.disconnect(); // Stop observing
        }
    }

    init() {
        // Load saved theme or detect system preference
        const savedTheme = localStorage.getItem(this.storageKey);
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        
        if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
            this.setDarkMode(true);
        }

        // Bind click event
        this.toggleBtn.addEventListener('click', () => this.toggle());

        // Listen for system theme changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!localStorage.getItem(this.storageKey)) {
                this.setDarkMode(e.matches);
            }
        });
    }

    toggle() {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        this.setDarkMode(!isDark);
        localStorage.setItem(this.storageKey, isDark ? 'light' : 'dark');
    }

    setDarkMode(enabled) {
        const root = document.documentElement;
        if (enabled) {
            root.setAttribute('data-theme', 'dark');
            this.toggleBtn.classList.add('theme-toggle--toggled');
        } else {
            root.removeAttribute('data-theme');
            this.toggleBtn.classList.remove('theme-toggle--toggled');
        }
    }
}

// Initialize theme toggle when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => new ThemeToggle());
} else {
    new ThemeToggle();
}

/**
 * Component Loader
 * Loads header and footer dynamically and handles active state
 */
async function loadComponents() {
    try {
        // Determine base path based on current page location
        const isInSubfolder = window.location.pathname.includes('/html/');
        const basePath = isInSubfolder ? '../components/' : 'components/';
        
        // Load Header
        const headerResponse = await fetch(basePath + 'header.html');
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
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('nav a');
        
        navLinks.forEach(link => {
            const linkPath = link.getAttribute('href');
            // Check if paths match (handle root path and clean URLs)
            if (linkPath === currentPath || 
                (linkPath === '/' && (currentPath === '/' || currentPath === '/index.html'))) {
                link.classList.add('active');
            }
        });
        
        // Dispatch event to notify that header is ready (for ThemeToggle)
        document.dispatchEvent(new Event('headerLoaded'));

        // Load Footer
        const footerResponse = await fetch(basePath + 'footer.html');
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
