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


async function showFileInfo(file) {
    const container = document.querySelector('.upload-container');
    if (!container) return;

    // Remove existing info
    const existing = document.getElementById('fileInfo');
    if (existing) existing.remove();

    const info = document.createElement('div');
    info.id = 'fileInfo';
    info.className = 'file-selected';
    
    // Apply flex styles to align text and close button
    info.style.display = 'inline-flex';
    info.style.alignItems = 'center';
    info.style.justifyContent = 'space-between';
    info.style.maxWidth = '100%';
    info.style.gap = '10px';
    info.style.marginTop = '1rem';
    info.style.padding = '0.5rem 1rem';
    info.style.backgroundColor = '#c9c9c9';
    info.style.borderRadius = '999px';
    info.style.fontSize = '0.9rem';

    info.innerHTML = `
        <div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; display: flex; align-items: center; gap: 0.5rem;">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="flex-shrink: 0;">
                <path d="M14 2H6C4.9 2 4 2.9 4 4V20C4 21.1 4.9 22 6 22H18C19.1 22 20 21.1 20 20V8L14 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M14 2V8H20" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                <strong>${file.name}</strong>
                <span style="color: #666; margin-left: 0.5rem;">(${this.formatFileSize(file.size)})</span>
            </div>
        </div>
        <button class="remove-file-btn" type="button" title="Delete file">
            ✕
        </button>
    `;

    // Style the remove button
    const btn = info.querySelector('.remove-file-btn');
    btn.style.background = 'none';
    btn.style.border = 'none';
    btn.style.cursor = 'pointer';
    btn.style.color = '#999';
    btn.style.fontSize = '1.2rem';
    btn.style.padding = '0';
    btn.style.display = 'inline-flex';
    btn.style.alignItems = 'center';
    btn.style.flexShrink = '0';

    btn.addEventListener('click', (e) => {
        e.stopPropagation(); // Prevent bubbling
        this.clearSelectedFile();
    });

    container.appendChild(info);
}