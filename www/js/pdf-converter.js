/**
 * PDF Converter Script
 * Handles file upload and PDF conversion
 */

document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const pdfFile = document.getElementById('pdfFile');
    const pdfFiles = document.getElementById('pdfFiles');
    const uploadContainer = document.querySelector('.upload-container');
    const resultSection = document.getElementById('resultSection');
    const errorSection = document.getElementById('errorSection');
    const downloadLink = document.getElementById('downloadLink');
    const errorMessage = document.getElementById('errorMessage');
    const operationRadios = document.querySelectorAll('input[name="operation"]');
    const splitOptions = document.getElementById('splitOptions');
    const pagesInput = document.getElementById('pages');

    /**
     * Update UI based on selected operation
     */
    function updateOperationUI() {
        const operation = document.querySelector('input[name="operation"]:checked').value;
        const label = uploadContainer.querySelector('.btn-upload');
        const fileInput = operation === 'merge' ? pdfFiles : pdfFile;
        const otherInput = operation === 'merge' ? pdfFile : pdfFiles;
        
        // Update file input
        otherInput.style.display = 'none';
        fileInput.style.display = '';
        fileInput.required = true;
        otherInput.required = false;
        
        // Update label and accept attribute
        if (operation === 'convert') {
            label.innerHTML = `
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M14 2H6C4.9 2 4 2.9 4 4V20C4 21.1 4.9 22 6 22H18C19.1 22 20 21.1 20 20V8L14 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M14 2V8H20" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M12 18V12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M9 15H15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                Choose Files
            `;
            fileInput.accept = ".pdf,.html,.htm,.xml,.xlsx,.xls,.docx,.jpg,.jpeg,.png,.bmp,.tif,.tiff,.txt,.py,.log,.md";
            splitOptions.style.display = 'none';
        } else if (operation === 'split') {
            label.innerHTML = `
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M14 2H6C4.9 2 4 2.9 4 4V20C4 21.1 4.9 22 6 22H18C19.1 22 20 21.1 20 20V8L14 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M14 2V8H20" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M12 18V12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M9 15H15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                Choose PDF File
            `;
            fileInput.accept = ".pdf";
            splitOptions.style.display = 'block';
        } else if (operation === 'merge') {
            label.innerHTML = `
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M14 2H6C4.9 2 4 2.9 4 4V20C4 21.1 4.9 22 6 22H18C19.1 22 20 21.1 20 20V8L14 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M14 2V8H20" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M12 18V12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M9 15H15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                Choose PDF Files
            `;
            fileInput.accept = ".pdf";
            splitOptions.style.display = 'none';
        }
        
        // Clear current file selection
        const existing = document.getElementById('fileInfo');
        if (existing) existing.remove();
        const convertBtn = document.getElementById('convertPdfBtn');
        if (convertBtn) convertBtn.remove();
        resultSection.style.display = 'none';
        hideError();
    }
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /**
     * Show file information below upload area
     */
    function showFileInfo(file) {
        // Remove existing info
        const existing = document.getElementById('fileInfo');
        if (existing) existing.remove();

        const info = document.createElement('div');
        info.id = 'fileInfo';
        info.className = 'file-selected';
        
        // Apply styles
        info.style.display = 'flex';
        info.style.alignItems = 'center';
        info.style.justifyContent = 'space-between';
        info.style.maxWidth = '100%';
        info.style.gap = '10px';
        info.style.marginTop = '1rem';
        info.style.padding = '0.5rem 1rem';
        info.style.backgroundColor = '#e3f2fd';
        info.style.borderRadius = '999px';
        info.style.fontSize = '0.9rem';

        info.innerHTML = `
            <div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                <strong>📄 ${file.name}</strong>
                <span style="color: #666; margin-left: 0.5rem;">(${formatFileSize(file.size)})</span>
            </div>
            <button class="remove-file-btn" type="button" title="Remove file" style="background: none; border: none; color: #999; cursor: pointer; font-size: 1.2rem;">
                ✕
            </button>
        `;

        uploadContainer.appendChild(info);

        // Add remove button handler
        const removeBtn = info.querySelector('.remove-file-btn');
        removeBtn.addEventListener('click', () => {
            pdfFile.value = '';
            info.remove();
            const convertBtn = document.getElementById('convertPdfBtn');
            if (convertBtn) convertBtn.remove();
            resultSection.style.display = 'none';
            errorSection.style.display = 'none';
        });

        // Show convert button
        showConvertButton();
    }

    /**
     * Show convert button
     */
    function showConvertButton() {
        // Remove existing button
        const existing = document.getElementById('convertPdfBtn');
        if (existing) existing.remove();

        const btn = document.createElement('button');
        btn.id = 'convertPdfBtn';
        btn.type = 'button';
        btn.className = 'convert-btn';
        btn.textContent = 'Convert to PDF';
        btn.style.marginTop = '1rem';
        btn.addEventListener('click', handleConvert);
        
        uploadContainer.appendChild(btn);
    }

    /**
     * Handle conversion
     */
    async function handleConvert() {
        if (!pdfFile.files || pdfFile.files.length === 0) {
            showError('Please select a file');
            return;
        }

        const file = pdfFile.files[0];
        const formData = new FormData();
        formData.append('file', file);

        const convertBtn = document.getElementById('convertPdfBtn');
        if (convertBtn) {
            convertBtn.disabled = true;
            convertBtn.textContent = 'Converting...';
        }

        try {
            resultSection.style.display = 'none';
            hideError();

            // Create AbortController for timeout handling
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 600000); // 10 minutes timeout

            const response = await fetch('/api/convert-to-pdf', {
                method: 'POST',
                body: formData,
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                let errorMsg = 'Conversion failed';
                try {
                    const error = await response.json();
                    errorMsg = error.detail || errorMsg;
                } catch (e) {
                    errorMsg = `${response.status}: ${response.statusText}`;
                }
                throw new Error(errorMsg);
            }

            // Download the result
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            downloadLink.href = url;
            downloadLink.download = file.name.replace(/\.[^/.]+$/, '') + '.pdf';
            
            resultSection.style.display = 'block';

        } catch (err) {
            let message = 'Error: ' + err.message;
            if (err.name === 'AbortError') {
                message = 'Error: Conversion timed out. The file may be too large or complex. Please try with a smaller file.';
            }
            showError(message);
        } finally {
            if (convertBtn) {
                convertBtn.disabled = false;
                convertBtn.textContent = 'Convert to PDF';
            }
        }
    }

    /**
     * Show error message
     */
    function showError(message) {
        errorMessage.textContent = message;
        errorSection.style.display = 'block';
        resultSection.style.display = 'none';
    }

    /**
     * Hide error section
     */
    function hideError() {
        errorSection.style.display = 'none';
    }

    // Handle file selection
    pdfFile.addEventListener('change', function() {
        if (!this.files || this.files.length === 0) {
            return;
        }

        const file = this.files[0];

        // Validate file size (max 100MB)
        const maxSize = 100 * 1024 * 1024;
        if (file.size > maxSize) {
            showError('File is too large. Maximum size: 100MB');
            pdfFile.value = '';
            return;
        }

        // Clear previous results and errors
        resultSection.style.display = 'none';
        hideError();

        // Show file info
        showFileInfo(file);

        console.log(`✓ File selected: ${file.name} (${formatFileSize(file.size)})`);
    });

    // Drag and Drop functionality
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadContainer.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
        }, false);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        uploadContainer.addEventListener(eventName, () => {
            uploadContainer.classList.add('highlight');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        uploadContainer.addEventListener(eventName, () => {
            uploadContainer.classList.remove('highlight');
        }, false);
    });

    uploadContainer.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;

        if (files.length > 0) {
            pdfFile.files = files;
            // Trigger the selection handler manually
            const event = new Event('change', { bubbles: true });
            pdfFile.dispatchEvent(event);
        }
    }, false);

    // Handle form submission
    uploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        await handleConvert();
    });
});
