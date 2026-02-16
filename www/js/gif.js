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
