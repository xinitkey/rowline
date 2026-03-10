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
     * Format file size for display (same implementation as XLSX converter)
     */
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

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
        
        // Update label 'for' attribute to point to correct input
        label.setAttribute('for', fileInput.id);
        
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
        const convertBtn = document.getElementById('convertBtn');
        if (convertBtn) convertBtn.remove();
        resultSection.style.display = 'none';
        hideError();

        // Reset merge files when changing operation
        if (operation !== 'merge') {
            currentMergeFiles = [];
            pdfFiles.value = '';
        }
    }
    /**
     * Move file up in merge list
     */
    function moveFileUp(index) {
        if (index <= 0) return;
        
        const dt = new DataTransfer();
        const currentFiles = Array.from(pdfFiles.files);
        
        // Swap files
        [currentFiles[index - 1], currentFiles[index]] = [currentFiles[index], currentFiles[index - 1]];
        
        currentFiles.forEach(file => {
            dt.items.add(file);
        });
        
        pdfFiles.files = dt.files;
        currentMergeFiles = Array.from(dt.items);
        showFileInfo(currentFiles);
    }

    /**
     * Move file down in merge list
     */
    function moveFileDown(index) {
        const currentFiles = Array.from(pdfFiles.files);
        if (index >= currentFiles.length - 1) return;
        
        const dt = new DataTransfer();
        
        // Swap files
        [currentFiles[index], currentFiles[index + 1]] = [currentFiles[index + 1], currentFiles[index]];
        
        currentFiles.forEach(file => {
            dt.items.add(file);
        });
        
        pdfFiles.files = dt.files;
        currentMergeFiles = Array.from(dt.items);
        showFileInfo(currentFiles);
    }

    /**
     * Remove specific file from merge list
     */
    function removeFileFromMerge(index) {
        // Create new FileList without the removed file
        const dt = new DataTransfer();
        const currentFiles = Array.from(pdfFiles.files);
        
        currentFiles.forEach((file, i) => {
            if (i !== index) {
                dt.items.add(file);
            }
        });
        
        pdfFiles.files = dt.files;
        currentMergeFiles = Array.from(dt.items);
        
        // Update UI
        if (pdfFiles.files.length === 0) {
            const existing = document.getElementById('fileInfo');
            if (existing) existing.remove();
            const convertBtn = document.getElementById('convertBtn');
            if (convertBtn) convertBtn.remove();
            resultSection.style.display = 'none';
            hideError();
        } else if (pdfFiles.files.length === 1) {
            showError('Please select at least 2 PDF files to merge');
            pdfFiles.value = '';
            currentMergeFiles = [];
            const existing = document.getElementById('fileInfo');
            if (existing) existing.remove();
            const convertBtn = document.getElementById('convertBtn');
            if (convertBtn) convertBtn.remove();
        } else {
            showFileInfo(Array.from(pdfFiles.files));
        }
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
        
        // Update tracked files for merge mode
        if (isMultiple) {
            currentMergeFiles = files;
        }
        
        const info = document.createElement('div');
        info.id = 'fileInfo';
        info.className = 'file-selected';
        
        // Apply styles
        info.style.marginTop = '1rem';
        info.style.maxWidth = '100%';

        if (isMultiple) {
            // Create a list of files for merge operation
            info.innerHTML = '<div style="font-weight: bold; margin-bottom: 0.5rem;">📄 Selected files for merge (drag to reorder or use buttons):</div>';
            
            const fileList = document.createElement('div');
            fileList.style.display = 'flex';
            fileList.style.flexDirection = 'column';
            fileList.style.gap = '0.5rem';
            
            Array.from(files).forEach((file, index) => {
                const fileItem = document.createElement('div');
                fileItem.style.display = 'flex';
                fileItem.style.alignItems = 'center';
                fileItem.style.justifyContent = 'space-between';
                fileItem.style.padding = '0.75rem 1rem';
                fileItem.style.backgroundColor = '#e3f2fd';
                fileItem.style.borderRadius = '8px';
                fileItem.style.fontSize = '0.9rem';
                fileItem.draggable = true;
                fileItem.className = 'merge-file-item';
                fileItem.setAttribute('data-index', index);
                
                const fileNameDiv = document.createElement('div');
                fileNameDiv.style.overflow = 'hidden';
                fileNameDiv.style.textOverflow = 'ellipsis';
                fileNameDiv.style.whiteSpace = 'nowrap';
                fileNameDiv.style.flex = '1';
                fileNameDiv.innerHTML = `
                    <strong>${index + 1}. ${file.name}</strong>
                    <span style="color: #666; margin-left: 0.5rem;">(${formatFileSize(file.size)})</span>
                `;
                
                const buttonsDiv = document.createElement('div');
                buttonsDiv.style.display = 'flex';
                buttonsDiv.style.gap = '0.5rem';
                buttonsDiv.style.marginLeft = '1rem';
                buttonsDiv.style.flexShrink = '0';
                
                // Move up button
                const upBtn = document.createElement('button');
                upBtn.type = 'button';
                upBtn.title = 'Move up';
                upBtn.className = 'move-up-btn';
                upBtn.innerHTML = '⬆️';
                upBtn.style.background = 'none';
                upBtn.style.border = 'none';
                upBtn.style.cursor = index === 0 ? 'not-allowed' : 'pointer';
                upBtn.style.fontSize = '1.1rem';
                upBtn.style.opacity = index === 0 ? '0.4' : '1';
                upBtn.disabled = index === 0;
                upBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    moveFileUp(index);
                });
                
                // Move down button
                const downBtn = document.createElement('button');
                downBtn.type = 'button';
                downBtn.title = 'Move down';
                downBtn.className = 'move-down-btn';
                downBtn.innerHTML = '⬇️';
                downBtn.style.background = 'none';
                downBtn.style.border = 'none';
                downBtn.style.cursor = index === files.length - 1 ? 'not-allowed' : 'pointer';
                downBtn.style.fontSize = '1.1rem';
                downBtn.style.opacity = index === files.length - 1 ? '0.4' : '1';
                downBtn.disabled = index === files.length - 1;
                downBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    moveFileDown(index);
                });
                
                // Remove button
                const removeBtn = document.createElement('button');
                removeBtn.type = 'button';
                removeBtn.className = 'remove-file-btn';
                removeBtn.setAttribute('data-index', index);
                removeBtn.title = 'Remove this file';
                removeBtn.innerHTML = '✕';
                removeBtn.style.background = 'none';
                removeBtn.style.border = 'none';
                removeBtn.style.color = '#999';
                removeBtn.style.cursor = 'pointer';
                removeBtn.style.fontSize = '1.2rem';
                
                buttonsDiv.appendChild(upBtn);
                buttonsDiv.appendChild(downBtn);
                buttonsDiv.appendChild(removeBtn);
                
                fileItem.appendChild(fileNameDiv);
                fileItem.appendChild(buttonsDiv);
                
                // Drag and drop within merge list
                fileItem.addEventListener('dragstart', (e) => {
                    e.dataTransfer.effectAllowed = 'move';
                    e.dataTransfer.setData('text/plain', index);
                    fileItem.style.opacity = '0.5';
                });
                
                fileItem.addEventListener('dragend', (e) => {
                    fileItem.style.opacity = '1';
                });
                
                fileItem.addEventListener('dragover', (e) => {
                    e.preventDefault();
                    e.dataTransfer.dropEffect = 'move';
                    fileItem.style.borderTop = '2px solid #007acc';
                });
                
                fileItem.addEventListener('dragleave', (e) => {
                    fileItem.style.borderTop = 'none';
                });
                
                fileItem.addEventListener('drop', (e) => {
                    e.preventDefault();
                    fileItem.style.borderTop = 'none';
                    
                    const sourceIndex = parseInt(e.dataTransfer.getData('text/plain'));
                    if (sourceIndex === index) return;
                    
                    const dt = new DataTransfer();
                    const currentFiles = Array.from(pdfFiles.files);
                    
                    // Remove from source and insert at target
                    const [movedFile] = currentFiles.splice(sourceIndex, 1);
                    currentFiles.splice(index, 0, movedFile);
                    
                    currentFiles.forEach(file => {
                        dt.items.add(file);
                    });
                    
                    pdfFiles.files = dt.files;
                    currentMergeFiles = Array.from(dt.items);
                    showFileInfo(currentFiles);
                });
                
                fileList.appendChild(fileItem);
            });
            
            info.appendChild(fileList);
        } else {
            const file = files[0];

            // Use the same visual style as XLSX converter: a rounded pill with file name and size
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
                        <strong>📄 ${file.name}</strong>
                        <span style="color: #666; margin-left: 0.5rem;">(${formatFileSize(file.size)})</span>
                    </div>
                </div>
                <button class="remove-file-btn" type="button" title="Remove file">
                    ✕
                </button>
            `;
        }

        uploadContainer.appendChild(info);

        // Add remove button handlers
        const removeBtns = info.querySelectorAll('.remove-file-btn');
        removeBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                if (isMultiple) {
                    // Remove specific file from merge list
                    const index = parseInt(e.target.getAttribute('data-index'));
                    removeFileFromMerge(index);
                } else {
                    // Remove single file
                    const fileInput = operation === 'merge' ? pdfFiles : pdfFile;
                    fileInput.value = '';
                    info.remove();
                    const convertBtn = document.getElementById('convertBtn');
                    if (convertBtn) convertBtn.remove();
                    resultSection.style.display = 'none';
                    hideError();
                }
            });
        });

        // Show convert button
        showConvertButton();
    }

    /**
     * Show convert button
     */
    function showConvertButton() {
        // Remove existing button
        const existing = document.getElementById('convertBtn');
        if (existing) existing.remove();

        const operation = document.querySelector('input[name="operation"]:checked').value;
        const btn = document.createElement('button');
        btn.id = 'convertBtn';
        btn.type = 'button';
        btn.className = 'convert-btn visible';
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
            <div id="pdfViewerContainer" style="display:none; margin-top: 1rem;">
                <h3>PDF Preview</h3>
                <iframe id="pdfViewer" width="100%" height="600px" style="border: 1px solid #ccc;"></iframe>
            </div>
            <p>${result.message}</p>
            <div style="margin-bottom: 1rem;">
                <a href="/download-zip/${result.session_id}" class="download-link zip-download" style="background: #28a745; margin-right: 1rem;">
                    📦 Download All as ZIP
                </a>
            </div>
            <div class="file-list">
                ${result.files.map((file, index) => `
                    <div class="file-item">
                        <a href="${file.url}" class="download-link file-download" data-index="${index}" data-url="${file.url}" data-filename="${file.filename}" target="_blank">
                            📄 ${file.filename} (${formatFileSize(file.size)})
                        </a>
                        <button class="preview-btn" onclick="loadPdfPreview('${file.url}')" style="margin-left: 10px; background: #007acc; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer;">Preview</button>
                    </div>
                `).join('')}
            </div>
        `;

        // Add click handlers for download links
        const zipLink = resultSection.querySelector('.zip-download');
        if (zipLink) {
            zipLink.addEventListener('click', function(e) {
                e.preventDefault();
                window.location.href = this.href;
            });
        }

        const fileLinks = resultSection.querySelectorAll('.file-download');
        fileLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const url = this.getAttribute('data-url');
                const filename = this.getAttribute('data-filename');
                
                fetch(url)
                    .then(res => res.blob())
                    .then(blob => {
                        const blobUrl = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = blobUrl;
                        a.download = filename;
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        setTimeout(() => window.URL.revokeObjectURL(blobUrl), 100);
                    });
            });
        });

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

        // Check file count limit for merge
        if (operation === 'merge') {
            if (fileInput.files.length < 2) {
                showError('Please select at least 2 PDF files to merge');
                return;
            }
            if (fileInput.files.length > 25) {
                showError('Maximum 25 PDF files allowed for merging');
                return;
            }
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

        const convertBtn = document.getElementById('convertBtn');
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
                // Check if response is JSON (multiple files) or blob (single file/error)
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    const result = await response.json();
                    showSplitResult(result);
                } else {
                    // Single file or error - download directly
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    downloadLink.href = url;
                    downloadLink.download = 'split_result.pdf';
                    downloadLink.textContent = 'Download Split PDF';
                    downloadLink.style.display = 'inline-block';

                    // Display PDF preview for single split result
                    const pdfViewer = document.getElementById('pdfViewer');
                    const pdfViewerContainer = document.getElementById('pdfViewerContainer');
                    pdfViewer.src = url;
                    pdfViewerContainer.style.display = 'block';

                    // Add click handler to force download
                    downloadLink.onclick = function(e) {
                        e.preventDefault();
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = 'split_result.pdf';
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        // Clean up blob URL after download
                        setTimeout(() => window.URL.revokeObjectURL(url), 100);
                    };

                    resultSection.style.display = 'block';
                }
            } else {
                // For convert and merge, download the file directly
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);

                // Set appropriate filename
                let filename;
                if (operation === 'convert') {
                    const file = fileInput.files[0];
                    filename = file.name.replace(/\.[^/.]+$/, '') + '.pdf';
                } else {
                    filename = 'merged.pdf';
                }

                downloadLink.href = url;
                downloadLink.download = filename;

                // Display PDF preview
                const pdfViewer = document.getElementById('pdfViewer');
                const pdfViewerContainer = document.getElementById('pdfViewerContainer');
                pdfViewer.src = url;
                pdfViewerContainer.style.display = 'block';

                // Add click handler to force download
                downloadLink.onclick = function(e) {
                    e.preventDefault();
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = filename;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    // Clean up blob URL after download
                    setTimeout(() => window.URL.revokeObjectURL(url), 100);
                };

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
     * Load PDF preview when clicking on preview button
     */
    function loadPdfPreview(url) {
        const pdfViewer = document.getElementById('pdfViewer');
        const pdfViewerContainer = document.getElementById('pdfViewerContainer');
        pdfViewer.src = url;
        pdfViewerContainer.style.display = 'block';
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

    // Track current files for merge mode
    let currentMergeFiles = [];

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

        const newFiles = Array.from(this.files);
        
        // Combine existing files with newly selected files
        const dt = new DataTransfer();
        
        // Add existing files
        currentMergeFiles.forEach(file => {
            dt.items.add(file);
        });
        
        // Add newly selected files
        newFiles.forEach(file => {
            dt.items.add(file);
        });
        
        // Update the tracked list and input
        currentMergeFiles = Array.from(dt.items);
        pdfFiles.files = dt.files;
        const allFiles = Array.from(pdfFiles.files);

        // Validate file count
        if (allFiles.length > 25) {
            showError('Maximum 25 PDF files allowed for merging');
            currentMergeFiles = [];
            pdfFiles.value = '';
            return;
        }

        // Show warning if less than 2 files, but don't clear selection
        if (allFiles.length < 2) {
            showError('Please select at least 2 PDF files to merge.');
        }

        // Validate file sizes (max 100MB each)
        const maxSize = 100 * 1024 * 1024;
        for (let file of allFiles) {
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
        showFileInfo(allFiles);

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
