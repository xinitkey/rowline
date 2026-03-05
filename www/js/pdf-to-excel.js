/**
 * PDF to Excel Converter - Frontend Script
 */

document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const pdfFile = document.getElementById('pdfFile');
    const uploadContainer = document.querySelector('.upload-container');
    const resultSection = document.getElementById('resultSection');
    const analysisSection = document.getElementById('analysisSection');
    const errorSection = document.getElementById('errorSection');
    const downloadLink = document.getElementById('downloadLink');
    const errorMessage = document.getElementById('errorMessage');
    const resultMessage = document.getElementById('resultMessage');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const pagesInput = document.getElementById('pages');
    const pdfPreviewContainer = document.getElementById('pdfPreviewContainer');
    const pdfViewer = document.getElementById('pdfViewer');
    const flavorSelect = document.getElementById('flavor');

    /**
     * Format file size for display
     */
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
        
        // Use the same visual style as other converters: a rounded pill
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

        uploadContainer.appendChild(info);

        // Add remove button handler
        const removeBtn = info.querySelector('.remove-file-btn');
        removeBtn.addEventListener('click', () => {
            pdfFile.value = '';
            info.remove();
            const convertBtn = document.getElementById('convertBtn');
            if (convertBtn) convertBtn.remove();
            // Hide analyze button
            if (analyzeBtn) analyzeBtn.style.display = 'none';
            resultSection.style.display = 'none';
            analysisSection.style.display = 'none';
            hidePdfPreview();
            hideError();
        });

        // Show convert and analyze buttons
        showButtons();
    }

    /**
     * Show convert and analyze buttons
     */
    function showButtons() {
        // Remove existing buttons
        const existingConvert = document.getElementById('convertBtn');
        const existingAnalyze = document.getElementById('analyzeBtn');

        if (!existingConvert) {
            const convertBtn = document.createElement('button');
            convertBtn.id = 'convertBtn';
            convertBtn.type = 'button';
            convertBtn.className = 'convert-btn visible';
            convertBtn.textContent = 'Convert to Excel';
            convertBtn.style.marginTop = '1rem';
            convertBtn.addEventListener('click', handleConvert);

            uploadContainer.appendChild(convertBtn);
        }

        // Show analyze button
        if (analyzeBtn) {
            analyzeBtn.style.display = 'block';
        }
    }

    /**
     * Show analysis results
     */
    function showAnalysisResults(info) {
        analysisSection.style.display = 'block';
        
        if (info.error) {
            document.getElementById('analysisContent').innerHTML = `
                <p style="color: #666;">${info.error}</p>
            `;
            return;
        }

        const tableCount = info.table_count || 0;
        const flavor = info.flavor || 'unknown';
        const tables = info.tables || [];

        let html = `
            <div class="analysis-summary">
                <p><strong>Tables detected:</strong> ${tableCount}</p>
                <p><strong>Recommended mode:</strong> ${flavor}</p>
            </div>
        `;

        if (tables.length > 0) {
            html += `
                <table class="analysis-table" style="width: 100%; border-collapse: collapse; margin-top: 1rem;">
                    <thead>
                        <tr style="background: #f5f5f5;">
                            <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Table #</th>
                            <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Page</th>
                            <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Rows</th>
                            <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Columns</th>
                            <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Accuracy</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            tables.forEach(table => {
                html += `
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 8px;">${table.table_number}</td>
                        <td style="border: 1px solid #ddd; padding: 8px;">${table.page}</td>
                        <td style="border: 1px solid #ddd; padding: 8px;">${table.rows}</td>
                        <td style="border: 1px solid #ddd; padding: 8px;">${table.columns}</td>
                        <td style="border: 1px solid #ddd; padding: 8px;">${table.accuracy ? table.accuracy + '%' : 'N/A'}</td>
                    </tr>
                `;
            });

            html += `
                    </tbody>
                </table>
            `;
        } else if (tableCount === 0) {
            html += `<p style="color: #666; margin-top: 1rem;">No tables detected. Try converting anyway with different settings.</p>`;
        }

        document.getElementById('analysisContent').innerHTML = html;
    }

    /**
     * Handle PDF analysis
     */
    async function handleAnalyze() {
        if (!pdfFile.files || pdfFile.files.length === 0) {
            showError('Please select a PDF file first');
            return;
        }

        const file = pdfFile.files[0];
        const analyzeBtnEl = document.getElementById('analyzeBtn');
        
        analyzeBtnEl.disabled = true;
        analyzeBtnEl.textContent = 'Analyzing...';

        const formData = new FormData();
        formData.append('file', file);
        formData.append('pages', '1'); // Just analyze first page

        try {
            analysisSection.style.display = 'none';
            hideError();

            const response = await fetch('/api/analyze-pdf', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                let errorMsg = 'Analysis failed';
                try {
                    const error = await response.json();
                    errorMsg = error.detail || errorMsg;
                } catch (e) {
                    errorMsg = `${response.status}: ${response.statusText}`;
                }
                throw new Error(errorMsg);
            }

            const info = await response.json();
            showAnalysisResults(info);

            // Auto-select recommended flavor
            if (info.flavor) {
                flavorSelect.value = info.flavor;
            }

        } catch (err) {
            showError('Error: ' + err.message);
        } finally {
            analyzeBtnEl.disabled = false;
            analyzeBtnEl.textContent = '🔍 Analyze PDF First';
        }
    }

    /**
     * Handle conversion
     */
    async function handleConvert() {
        if (!pdfFile.files || pdfFile.files.length === 0) {
            showError('Please select a PDF file');
            return;
        }

        const file = pdfFile.files[0];
        const pages = pagesInput.value || 'all';
        const flavor = flavorSelect.value;

        const convertBtn = document.getElementById('convertBtn');
        if (convertBtn) {
            convertBtn.disabled = true;
            convertBtn.textContent = 'Converting...';
        }

        const formData = new FormData();
        formData.append('file', file);
        formData.append('pages', pages);
        formData.append('flavor', flavor);

        try {
            resultSection.style.display = 'none';
            hideError();

            // Create AbortController for timeout handling
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 600000); // 10 minutes timeout

            const response = await fetch('/api/pdf-to-excel', {
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

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            downloadLink.href = url;
            downloadLink.download = file.name.replace(/\.[^/.]+$/, '') + '.xlsx';
            
            resultMessage.textContent = `Successfully converted ${file.name} to Excel format.`;
            resultSection.style.display = 'block';

        } catch (err) {
            let message = 'Error: ' + err.message;
            if (err.name === 'AbortError') {
                message = 'Error: Operation timed out. The file may be too large or complex. Please try with a smaller file or specific page ranges.';
            }
            showError(message);
        } finally {
            if (convertBtn) {
                convertBtn.disabled = false;
                convertBtn.textContent = 'Convert to Excel';
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
        analysisSection.style.display = 'none';
    }

    /**
     * Hide error section
     */
    function hideError() {
        errorSection.style.display = 'none';
    }

    /**
     * Show PDF preview
     */
    function showPdfPreview(file) {
        const fileUrl = URL.createObjectURL(file);
        pdfViewer.src = fileUrl;
        pdfPreviewContainer.style.display = 'block';
    }

    /**
     * Hide PDF preview
     */
    function hidePdfPreview() {
        pdfPreviewContainer.style.display = 'none';
        if (pdfViewer.src) {
            URL.revokeObjectURL(pdfViewer.src);
            pdfViewer.src = '';
        }
    }

    // Handle file selection
    pdfFile.addEventListener('change', function() {
        if (!this.files || this.files.length === 0) {
            return;
        }

        const file = this.files[0];

        // Validate file type
        if (!file.name.toLowerCase().endsWith('.pdf')) {
            showError('Please select a valid PDF file');
            pdfFile.value = '';
            return;
        }

        // Validate file size (max 100MB)
        const maxSize = 100 * 1024 * 1024;
        if (file.size > maxSize) {
            showError('File is too large. Maximum size: 100MB');
            pdfFile.value = '';
            return;
        }

        // Clear previous results and errors
        resultSection.style.display = 'none';
        analysisSection.style.display = 'none';
        hideError();

        // Show file info
        showFileInfo(file);

        // Show PDF preview
        showPdfPreview(file);

        console.log(`✓ File selected: ${file.name} (${formatFileSize(file.size)})`);
    });

    // Handle analyze button
    analyzeBtn.addEventListener('click', handleAnalyze);

    // Handle form submission
    uploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        await handleConvert();
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
            const event = new Event('change', { bubbles: true });
            pdfFile.dispatchEvent(event);
        }
    }, false);
});
