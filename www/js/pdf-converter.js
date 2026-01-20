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
        console.log('updateOperationUI called, operation:', operation);
        
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
            console.log('Setting split options to block');
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
            console.log('splitOptions display set to block');
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
        
        // Show appropriate button for current operation
        showConvertButton();
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
    function showFileInfo(files) {
        // Remove existing info
        const existing = document.getElementById('fileInfo');
        if (existing) existing.remove();

        const operation = document.querySelector('input[name="operation"]:checked').value;
        const isMultiple = operation === 'merge';
        
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

        if (isMultiple) {
            const totalSize = Array.from(files).reduce((sum, file) => sum + file.size, 0);
            info.innerHTML = `
                <div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                    <strong>📄 ${files.length} files selected</strong>
                    <span style="color: #666; margin-left: 0.5rem;">(${formatFileSize(totalSize)} total)</span>
                </div>
                <button class="remove-file-btn" type="button" title="Remove files" style="background: none; border: none; color: #999; cursor: pointer; font-size: 1.2rem;">
                    ✕
                </button>
            `;
        } else {
            const file = files[0];
            info.innerHTML = `
                <div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                    <strong>📄 ${file.name}</strong>
                    <span style="color: #666; margin-left: 0.5rem;">(${formatFileSize(file.size)})</span>
                </div>
                <button class="remove-file-btn" type="button" title="Remove file" style="background: none; border: none; color: #999; cursor: pointer; font-size: 1.2rem;">
                    ✕
                </button>
            `;
        }

        uploadContainer.appendChild(info);

        // Add remove button handler
        const removeBtn = info.querySelector('.remove-file-btn');
        removeBtn.addEventListener('click', () => {
            const fileInput = operation === 'merge' ? pdfFiles : pdfFile;
            fileInput.value = '';
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

        const operation = document.querySelector('input[name="operation"]:checked').value;
        const btn = document.createElement('button');
        btn.id = 'convertPdfBtn';
        btn.type = 'button';
        btn.className = 'convert-btn';
        btn.textContent = operation === 'convert' ? 'Convert to PDF' :
                         operation === 'split' ? 'Split PDF' : 'Merge PDFs';
        btn.style.marginTop = '1rem';
        btn.addEventListener('click', handleConvert);
        
        uploadContainer.appendChild(btn);
    }

    /**
     * Show split result with download links
     */
    function showSplitResult(result) {
        // Clear existing content
        resultSection.innerHTML = `
            <h2>Split Result</h2>
            <p>${result.message}</p>
            <div class="file-list">
                ${result.files.map(file => `
                    <div class="file-item">
                        <a href="${file.url}" download="${file.filename}" class="download-link">
                            📄 ${file.filename} (${formatFileSize(file.size)})
                        </a>
                    </div>
                `).join('')}
            </div>
        `;
        resultSection.style.display = 'block';
    }

    /**
     * Handle conversion
     */
    async function handleConvert() {
        const operation = document.querySelector('input[name="operation"]:checked').value;
        const fileInput = operation === 'merge' ? pdfFiles : pdfFile;
        
        if (!fileInput.files || fileInput.files.length === 0) {
            showError('Please select a file');
            return;
        }

        const formData = new FormData();
        
        if (operation === 'merge') {
            // Add all files for merge
            for (let file of fileInput.files) {
                formData.append('files', file);
            }
        } else {
            // Single file for convert or split
            formData.append('file', fileInput.files[0]);
            
            // Add pages parameter for split
            if (operation === 'split' && pagesInput.value.trim()) {
                formData.append('pages', pagesInput.value.trim());
            }
        }

        const convertBtn = document.getElementById('convertPdfBtn');
        if (convertBtn) {
            convertBtn.disabled = true;
            convertBtn.textContent = operation === 'convert' ? 'Converting...' : 
                                   operation === 'split' ? 'Splitting...' : 'Merging...';
        }

        try {
            resultSection.style.display = 'none';
            hideError();

            // Create AbortController for timeout handling
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 600000); // 10 minutes timeout

            // Choose the correct API endpoint
            const endpoint = operation === 'convert' ? '/api/convert-to-pdf' :
                           operation === 'split' ? '/api/split-pdf' : '/api/merge-pdf';

            const response = await fetch(endpoint, {
                method: 'POST',
                body: formData,
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                let errorMsg = operation === 'convert' ? 'Conversion failed' :
                             operation === 'split' ? 'Split failed' : 'Merge failed';
                try {
                    const error = await response.json();
                    errorMsg = error.detail || errorMsg;
                } catch (e) {
                    errorMsg = `${response.status}: ${response.statusText}`;
                }
                throw new Error(errorMsg);
            }

            if (operation === 'split') {
                // For split operation, show download links for individual files
                const result = await response.json();
                showSplitResult(result);
            } else {
                // For convert and merge, download the file directly
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                downloadLink.href = url;
                
                // Set appropriate filename
                if (operation === 'convert') {
                    const file = fileInput.files[0];
                    downloadLink.download = file.name.replace(/\.[^/.]+$/, '') + '.pdf';
                } else if (operation === 'merge') {
                    downloadLink.download = 'merged.pdf';
                }
                
                resultSection.style.display = 'block';
            }

        } catch (err) {
            let message = 'Error: ' + err.message;
            if (err.name === 'AbortError') {
                message = 'Error: Operation timed out. The file(s) may be too large or complex. Please try with smaller file(s).';
            }
            showError(message);
        } finally {
            if (convertBtn) {
                convertBtn.disabled = false;
                convertBtn.textContent = operation === 'convert' ? 'Convert to PDF' :
                                       operation === 'split' ? 'Split PDF' : 'Merge PDFs';
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
        showFileInfo([file]);

        console.log(`✓ File selected: ${file.name} (${formatFileSize(file.size)})`);
    });

    // Handle multiple file selection for merge
    pdfFiles.addEventListener('change', function() {
        if (!this.files || this.files.length === 0) {
            return;
        }

        // Validate file count
        if (this.files.length < 2) {
            showError('Please select at least 2 PDF files to merge');
            pdfFiles.value = '';
            return;
        }

        // Validate file sizes (max 100MB each)
        const maxSize = 100 * 1024 * 1024;
        for (let file of this.files) {
            if (file.size > maxSize) {
                showError('One or more files are too large. Maximum size: 100MB per file');
                pdfFiles.value = '';
                return;
            }
        }

        // Clear previous results and errors
        resultSection.style.display = 'none';
        hideError();

        // Show file info
        showFileInfo(Array.from(this.files));

        console.log(`✓ ${this.files.length} files selected for merge`);
    });

    // Handle operation selection
    operationRadios.forEach(radio => {
        radio.addEventListener('change', updateOperationUI);
    });

    // Initialize UI
    updateOperationUI();

    // Drag and Drop functionality
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadContainer.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
        }, false);
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
        const operation = document.querySelector('input[name="operation"]:checked').value;

        if (files.length > 0) {
            if (operation === 'merge') {
                pdfFiles.files = files;
                const event = new Event('change', { bubbles: true });
                pdfFiles.dispatchEvent(event);
            } else {
                pdfFile.files = files;
                const event = new Event('change', { bubbles: true });
                pdfFile.dispatchEvent(event);
            }
        }
    }, false);

    // Handle form submission
    uploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        await handleConvert();
    });
});
