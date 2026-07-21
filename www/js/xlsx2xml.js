/**
 * XLSX to XML Converter - Frontend JavaScript
 * Handles file upload, conversion requests and file download.
 */

class XlsxConverter {
    constructor() {
        // API endpoints
        this.apiBase = '/api';
        this.endpoints = {
            convert: `${this.apiBase}/convert`,
            templates: `${this.apiBase}/templates`,
            uploadTemplate: `${this.apiBase}/upload-template`,
            health: `${this.apiBase}/health`
        };

        // Default conversion settings
        this.settings = {
            mode: 'fill',          // 'fill' or 'convert'
            template: null,        // Template filename
            sheetName: null,       // Specific sheet name (null = all sheets)
            codeCol: 6,            // Column with code (1-based, F=6)
            dataStartCol: 7,       // Data start column (G=7)
            dataEndCol: 12,        // Data end column (L=12)
            startRow: 9            // First data row
        };

        // State
        this.selectedFile = null;
        this.templates = [];
        this.isConverting = false;

        // Initialize when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }

    /**
     * Initialize the converter
     */
    async init() {
        this.bindElements();
        this.bindEvents();
        await this.loadTemplates();
        await this.checkApiHealth();
    }

    /**
     * Helper to truncate text
     */
    truncateText(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    /**
     * Bind DOM elements
     */
    bindElements() {
        this.form = document.getElementById('uploadForm');
        this.fileInput = document.getElementById('xlsxFile');
        this.uploadContainer = document.querySelector('.upload-container'); 
        this.resultSection = document.getElementById('resultSection');
        this.errorSection = document.getElementById('errorSection');
        this.errorMessage = document.getElementById('errorMessage');
        this.downloadLink = document.getElementById('downloadLink');
        this.submitBtn = document.getElementById('submitBtn');

        // Create progress indicator if not exists
        if (!document.getElementById('progressSection')) {
            this.createProgressSection();
        }
        this.progressSection = document.getElementById('progressSection');
        this.progressText = document.getElementById('progressText');
    }

    /**
     * Create progress section dynamically
     */
    createProgressSection() {
        const section = document.createElement('section');
        section.id = 'progressSection';
        section.style.display = 'none';
        section.innerHTML = `
            <div class="progress-container">
                <div class="spinner"></div>
                <p id="progressText">Converting...</p>
            </div>
        `;
        
        // Insert after form
        if (this.form && this.form.parentNode) {
            this.form.parentNode.insertBefore(section, this.form.nextSibling);
        }
        
        // Add spinner styles if not present
        if (!document.getElementById('converter-styles')) {
            const style = document.createElement('style');
            style.id = 'converter-styles';
            style.textContent = `
/* Progress container styled like description-container */
.progress-container {
  background-color: #E3E2E2;
  border: 0 solid #9ca3cd;
  border-radius: 50px;
  padding: 2rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin-top: 1rem;
  margin-bottom: 1rem;
  gap: 1rem;              /* spacing between inner elements */
}
[data-theme="dark"] .progress-container {
    background-color: #24283b; }

/* Spinner */
.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #43DDCB;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

/* Spinner animation */
@keyframes spin {
  0%   { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Result block */
#resultSection {
  background-color: #CCE3D6;
  padding: 1.5rem;
  border-radius: 50px;
  margin-top: 1rem;
  margin-bottom: 1rem;
  text-align: center;
}

[data-theme="dark"] #resultSection {
    background-color: #24283b;



/* Error block */
#errorSection {
  background-color: rgb(231, 191, 197);
  padding: 1.5rem;
  border-radius: 50px;
  margin-top: 1rem;
  margin-bottom: 1rem;
  text-align: center;
}

/* Selected file info */
.file-selected {
  margin-top: 0;
  padding: 0.5rem 1rem;
  background-color: rgb(201, 201, 201);
  border-radius: 999px;
  display: inline-block;
  font-size: 0.9rem;
}

/* Template select */
.template-select {
  margin-top: 0;
  padding: 0.5rem 0.75rem;
  font-size: 1rem;
  border: 2px solid #9ca3cd;
  border-radius: 999px;
  width: 100%;
  max-width: 400px;
  text-overflow: ellipsis;
  white-space: nowrap;
  overflow: hidden;
  background-color: #ffffff;
}

/* Disabled convert button */
.convert-btn:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}
            `;
            document.head.appendChild(style);
        }
    }

    /**
     * Bind event listeners
     */
    bindEvents() {
        // File selection
        if (this.fileInput) {
            this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        }

        // Form submission
        if (this.form) {
            this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        }

        // Drag and Drop
        if (this.uploadContainer) {
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                this.uploadContainer.addEventListener(eventName, (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                }, false);
            });

            ['dragenter', 'dragover'].forEach(eventName => {
                this.uploadContainer.addEventListener(eventName, () => {
                    this.uploadContainer.classList.add('highlight');
                }, false);
            });

            ['dragleave', 'drop'].forEach(eventName => {
                this.uploadContainer.addEventListener(eventName, () => {
                    this.uploadContainer.classList.remove('highlight');
                }, false);
            });

            this.uploadContainer.addEventListener('drop', (e) => this.handleDrop(e), false);
        }
    }

    /**
     * Handle dropped files
     */
    handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;

        if (files.length > 0) {
            // Assign the dropped file to the file input
            if (this.fileInput) {
                this.fileInput.files = files;
                // Trigger the selection handler manually since programmatic assignment doesn't fire 'change'
                this.handleFileSelect({ target: this.fileInput });
            }
        }
    }

    /**
     * Check API health
     */
    async checkApiHealth() {
        try {
            const response = await fetch(this.endpoints.health);
            if (response.ok) {
                console.log('✓ API is healthy');
                return true;
            }
        } catch (error) {
            console.warn('⚠ API is not available:', error.message);
        }
        return false;
    }

    /**
     * Load available templates from server
     */
    async loadTemplates() {
        try {
            const response = await fetch(this.endpoints.templates);
            if (response.ok) {
                const data = await response.json();
                this.templates = data.templates || [];
                console.log(`✓ Loaded ${this.templates.length} templates`);
                this.renderTemplateSelector();
            }
        } catch (error) {
            console.warn('⚠ Could not load templates:', error.message);
        }
    }

    /**
     * Render template selector dropdown
     */
    renderTemplateSelector() {
        // Only render on index page, not on templates page
        if (window.location.pathname.includes('/html/templates')) {
            return;
        }
        
        const container = document.querySelector('.upload-container');
        if (!container) return;

        // Remove existing selector if any
        const existing = document.getElementById('templateSelector');
        if (existing) existing.remove();

        // Create selector
        const wrapper = document.createElement('div');
        wrapper.id = 'templateSelector';
        wrapper.style.marginTop = '1rem';
        wrapper.style.width = '100%';
        wrapper.style.textAlign = 'center';

        if (this.templates.length > 0) {
            wrapper.innerHTML = `
                <label for="templateSelect" style="display: block; margin-bottom: 0.5rem; color: #555;">
                    Select an XML template:
                </label>
                <select id="templateSelect" class="template-select">
                    <option value="">- Without a template -</option>
                    ${this.templates.map(t => 
                        `<option value="${t.filename}" title="${t.name}">${this.truncateText(t.name, 30)}</option>`
                    ).join('')}
                </select>
            `;
        } else {
            wrapper.innerHTML = `
                <p style="color: #888; font-size: 0.9rem;">
                    No templates found. Files will be converted without a template.
                </p>
            `;
        }

        container.appendChild(wrapper);

        // Bind template change event
        const select = document.getElementById('templateSelect');
        if (select) {
            select.addEventListener('change', (e) => {
                this.settings.template = e.target.value || null;
                this.settings.mode = e.target.value ? 'fill' : 'convert';
                console.log(`Mode: ${this.settings.mode}, Template: ${this.settings.template}`);
            });
        }
    }

    /**
     * Handle file selection
     */
    handleFileSelect(event) {
        const files = event.target.files;
        if (!files || files.length === 0) {
            this.selectedFile = null;
            return;
        }

        const file = files[0];
        
        // Validate file type
        if (!file.name.toLowerCase().endsWith('.xlsx')) {
            this.showError('Please select a .xlsx file');
            this.fileInput.value = '';
            this.selectedFile = null;
            return;
        }

        // Validate file size (max 100MB)
        const maxSize = 100 * 1024 * 1024;
        if (file.size > maxSize) {
            this.showError('File is too large. Maximum size: 100MB');
            this.fileInput.value = '';
            this.selectedFile = null;
            return;
        }

        this.selectedFile = file;
        this.hideError();
        this.hideResult();
        
        // Show selected file info
        this.showFileInfo(file);
        
        // Show convert button
        this.showConvertButton();

        console.log(`✓ File selected: ${file.name} (${this.formatFileSize(file.size)})`);
    }

    /**
     * Show selected file info
     */
    showFileInfo(file) {
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

    /**
     * Clear selected file and reset UI
     */
    clearSelectedFile() {
        this.selectedFile = null;
        if (this.fileInput) {
            this.fileInput.value = '';
        }

        const info = document.getElementById('fileInfo');
        if (info) info.remove();

        this.hideConvertButton();

        console.log('File selection cleared');
    }

    /**
     * Show convert button
     */
    showConvertButton() {
        const container = document.querySelector('.upload-container');
        if (!container) return;

        // Remove existing button
        const existing = document.getElementById('convertBtn');
        if (existing) existing.remove();

        const btn = document.createElement('button');
        btn.id = 'convertBtn';
        btn.type = 'button';
        btn.className = 'convert-btn visible';
        btn.textContent = 'Convert';
        btn.addEventListener('click', () => this.convert());

        container.appendChild(btn);
    }

    /**
     * Hide convert button
     */
    hideConvertButton() {
        const existing = document.getElementById('convertBtn');
        if (existing) existing.remove();
    }

    /**
     * Handle form submission
     */
    async handleSubmit(event) {
        event.preventDefault();
        await this.convert();
    }

    /**
     * Perform the conversion
     */
    async convert() {
        if (!this.selectedFile) {
            this.showError('Please select a file to convert');
            return;
        }

        if (this.isConverting) {
            return;
        }

        this.isConverting = true;
        this.hideError();
        this.hideResult();
        this.showProgress('Uploading and converting file...');
        
        // Disable convert button
        const convertBtn = document.getElementById('convertBtn');
        if (convertBtn) {
            convertBtn.disabled = true;
            convertBtn.textContent = 'Converting...';
        }

        try {
            const formData = new FormData();
            formData.append('file', this.selectedFile);
            formData.append('mode', this.settings.mode);
            
            if (this.settings.template) {
                formData.append('template', this.settings.template);
            }
            if (this.settings.sheetName) {
                formData.append('sheet_name', this.settings.sheetName);
            }
            formData.append('code_col', this.settings.codeCol);
            formData.append('data_start_col', this.settings.dataStartCol);
            formData.append('data_end_col', this.settings.dataEndCol);
            formData.append('start_row', this.settings.startRow);

            const response = await fetch(this.endpoints.convert, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `Server error: ${response.status}`);
            }

            // Check if response is JSON (multiple files) or blob (single file)
            const contentType = response.headers.get('content-type');
            console.log(`[JS] Convert response content-type: ${contentType}`);
            if (contentType && contentType.includes('application/json')) {
                // Multiple files - show download links
                const data = await response.json();
                console.log(`[JS] Convert result:`, data);
                this.showMultipleResults(data.files, data.message, data.session_id);
                console.log(`✓ Conversion complete: ${data.message}`);
            } else {
                // Single file - direct download
                // Get filename from Content-Disposition header
                const contentDisposition = response.headers.get('Content-Disposition');
                let filename = 'converted.xml';
                if (contentDisposition) {
                    const match = contentDisposition.match(/filename="?([^";\n]+)"?/);
                    if (match) {
                        filename = match[1];
                    }
                }

                // Create blob and download link
                const blob = await response.blob();
                const url = URL.createObjectURL(blob);

                this.showResult(url, filename);
                console.log(`✓ Conversion complete: ${filename}`);
            }

        } catch (error) {
            console.error('Conversion error:', error);
            this.showError(error.message || 'Error during conversion');
        } finally {
            this.isConverting = false;
            this.hideProgress();
            
            // Re-enable convert button
            if (convertBtn) {
                convertBtn.disabled = false;
                convertBtn.textContent = 'Convert';
            }
        }
    }

    /**
     * Show progress indicator
     */
    showProgress(message = 'Processing...') {
        if (this.progressSection) {
            this.progressSection.style.display = 'block';
        }
        if (this.progressText) {
            this.progressText.textContent = message;
        }
    }

    /**
     * Hide progress indicator
     */
    hideProgress() {
        if (this.progressSection) {
            this.progressSection.style.display = 'none';
        }
    }

    /**
     * Show conversion result
     */
    showResult(downloadUrl, filename) {
        if (this.resultSection) {
            this.resultSection.style.display = 'block';
        }
        if (this.downloadLink) {
            this.downloadLink.href = downloadUrl;
            this.downloadLink.download = filename;
            this.downloadLink.textContent = `Download ${filename}`;
            this.downloadLink.className = 'btn-upload';
            this.downloadLink.style.display = 'inline-flex';
        }
    }

    /**
     * Show multiple conversion results
     */
    showMultipleResults(files, message, sessionId) {
        if (this.resultSection) {
            this.resultSection.style.display = 'block';
        }
        if (this.downloadLink) {
            // Clear existing content
            this.downloadLink.innerHTML = '';
            
            // Add message
            const messageDiv = document.createElement('div');
            messageDiv.textContent = message;
            messageDiv.style.marginBottom = '1rem';
            messageDiv.style.fontWeight = 'bold';
            this.downloadLink.appendChild(messageDiv);
            
            // Add ZIP download button if sessionId provided
            if (sessionId) {
                const zipButton = document.createElement('a');
                zipButton.href = `/download-zip/${sessionId}`;
                zipButton.textContent = '📦 Download All as ZIP';
                zipButton.className = 'download-link';
                zipButton.style.background = '#28a745';
                zipButton.style.marginRight = '1rem';
                zipButton.style.marginBottom = '1rem';
                zipButton.style.display = 'inline-block';
                this.downloadLink.appendChild(zipButton);
            }
            
            // Add file list
            const fileList = document.createElement('div');
            fileList.className = 'file-list';
            
            files.forEach(file => {
                const fileItem = document.createElement('div');
                fileItem.className = 'file-item';
                
                const link = document.createElement('a');
                link.href = file.url;
                link.textContent = file.filename;
                link.className = 'download-link';
                link.target = '_blank';
                
                const size = document.createElement('span');
                size.textContent = ` (${this.formatFileSize(file.size)})`;
                size.style.color = '#666';
                
                fileItem.appendChild(link);
                fileItem.appendChild(size);
                fileList.appendChild(fileItem);
            });
            
            this.downloadLink.appendChild(fileList);
            this.downloadLink.style.display = 'block';
        }
    }

    /**
     * Hide result section
     */
    hideResult() {
        if (this.resultSection) {
            this.resultSection.style.display = 'none';
        }
    }

    /**
     * Show error message
     */
    showError(message) {
        if (this.errorSection) {
            this.errorSection.style.display = 'block';
        }
        if (this.errorMessage) {
            this.errorMessage.textContent = message;
        }
    }

    /**
     * Hide error section
     */
    hideError() {
        if (this.errorSection) {
            this.errorSection.style.display = 'none';
        }
    }

    /**
     * Format file size for display
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /**
     * Update conversion settings
     */
    updateSettings(newSettings) {
        this.settings = { ...this.settings, ...newSettings };
    }
}

// Initialize converter
const converter = new XlsxConverter();

// Export for external use
window.XlsxConverter = XlsxConverter;
window.converter = converter;
