/**
 * Convert video to GIF with optional parameters
 * @param {File|Blob} videoFile - video file object
 * @param {Object} options - conversion options
 * @param {number} options.start - start time in seconds (optional)
 * @param {number} options.end - end time in seconds (optional)
 * @param {number} options.fps - frames per second (optional, 15-30 recommended)
 * @param {number} options.width - output width in pixels (optional)
 * @param {string} url - API endpoint URL, e.g., "http://localhost:8000/api/video-to-gif"
 * @returns {Promise<Blob>} - GIF file as blob
 */
async function convertVideoToGif(videoFile, options = {}, url) {
  const formData = new FormData();
  
  // Add video file
  formData.append('file', videoFile);
  
  // Add optional parameters
  if (options.start !== undefined && options.start !== null) {
    formData.append('start', options.start);
  }
  if (options.end !== undefined && options.end !== null) {
    formData.append('end', options.end);
  }
  if (options.fps !== undefined && options.fps !== null) {
    formData.append('fps', options.fps);
  }
  if (options.width !== undefined && options.width !== null) {
    formData.append('width', options.width);
  }

  const resp = await fetch(url, {
    method: 'POST',
    body: formData, // multipart/form-data
  });

  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`Conversion failed: ${resp.status} ${text}`);
  }

  // Get file from response and return as blob
  return await resp.blob();
}

/**
 * Отправка одного видео файла на бэкенд (FastAPI/Flask и т.п.)
 * @param {File|Blob} videoFile - объект файла (video/mp4, video/webm и т.д.)
 * @param {string} url - адрес эндпоинта, например "http://localhost:8000/upload"
 * @returns {Promise<any>} - JSON ответ сервера
 */
async function uploadVideo(videoFile, url) {
  const formData = new FormData();
  // "file" — имя поля, которое ожидает бэкенд
  formData.append('file', videoFile);

  const resp = await fetch(url, {
    method: 'POST',
    body: formData, // multipart/form-data, заголовок выставится автоматически
  });

  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`Upload failed: ${resp.status} ${text}`);
  }

  return resp.json();
}

// Handle file selection
document.getElementById('videoFile').addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
      const videoPreview = document.getElementById('videoPreview');
      const videoFileName = document.getElementById('videoFileName');
      const videoPreviewContainer = document.getElementById('videoPreviewContainer');
      const convertBtn = document.getElementById('convertBtn');

      // Create object URL and set video source
      const videoUrl = URL.createObjectURL(file);
      videoPreview.src = videoUrl;

      // Show file name and size
      const fileSizeMB = (file.size / (1024 * 1024)).toFixed(2);
      videoFileName.textContent = `File: ${file.name} (${fileSizeMB} MB)`;

      // Show preview container and convert button
      videoPreviewContainer.style.display = 'block';
      convertBtn.style.display = 'block';
    }
});

// Handle form submission
document.getElementById('uploadForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const videoFile = document.getElementById('videoFile').files[0];
    if (!videoFile) {
        showError('Please select a video file.');
        return;
    }

    // Hide previous sections
    document.getElementById('resultSection').style.display = 'none';
    document.getElementById('errorSection').style.display = 'none';
    document.getElementById('progressSection').style.display = 'block';

    try {
        // Get options from form
        const options = {
            start: document.getElementById('startTime').value ? parseFloat(document.getElementById('startTime').value) : null,
            end: document.getElementById('endTime').value ? parseFloat(document.getElementById('endTime').value) : null,
            fps: document.getElementById('fps').value ? parseInt(document.getElementById('fps').value) : null,
            width: document.getElementById('width').value ? parseInt(document.getElementById('width').value) : null
        };

        // Validate options
        if (options.start !== null && options.end !== null && options.start > options.end) {
            throw new Error('Start time must be less than end time');
        }

        // Update progress
        updateProgress(0.3, 'Starting conversion...');

        // Call the conversion function from gif.js
        const gifBlob = await convertVideoToGif(videoFile, options, '/api/video-to-gif');

        updateProgress(0.9, 'Processing result...');

        // Create download link
        const gifUrl = URL.createObjectURL(gifBlob);
        const downloadLink = document.getElementById('downloadLink');
        downloadLink.href = gifUrl;
        downloadLink.download = `${videoFile.name.split('.')[0]}.gif`;

        // Display preview
        const gifPreview = document.getElementById('gifPreview');
        gifPreview.src = gifUrl;

        // Show result section
        document.getElementById('progressSection').style.display = 'none';
        document.getElementById('resultSection').style.display = 'block';

        updateProgress(1, 'Done!');

    } catch (error) {
        document.getElementById('progressSection').style.display = 'none';
        showError(error.message || 'Conversion failed. Please try again.');
    }
});

function updateProgress(progress, text) {
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    progressBar.style.width = (progress * 100) + '%';
    progressText.textContent = text;
}

function showError(message) {
    document.getElementById('errorMessage').textContent = message;
    document.getElementById('errorSection').style.display = 'block';
}