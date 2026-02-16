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
