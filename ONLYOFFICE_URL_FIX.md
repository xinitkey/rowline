# OnlyOffice API Integration Fix

## Проблема
OnlyOffice Document Server ConvertService API возвращал XML ошибку -8 (неверный формат запроса) при попытках конвертации DOCX в PDF.

### Предыдущие попытки:
1. **Data URL подход** - использование base64 data URL в JSON запросе
   - Результат: OnlyOffice не поддерживает data URLs (RFC 2397)
   - Ошибка: JSON parse error

2. **Multipart upload подход** - загрузка файла через multipart/form-data
   - Результат: OnlyOffice ConvertService не поддерживает прямую загрузку файлов
   - Ответ: `<?xml version="1.0"?><FileResult><Error>-8</Error></FileResult>`
   - Ошибка -8 = неверный формат запроса

## Решение
OnlyOffice ConvertService API требует JSON запрос с полем `url`, содержащим **публично доступный HTTP URL** для загрузки файла.

### Реализация:

1. **Создан endpoint для раздачи временных файлов:**
   ```python
   @app.get("/temp-files/{file_id}")
   async def serve_temp_file(file_id: str)
   ```
   - Регистрирует загруженные файлы в `temp_files_storage`
   - Отдает файлы по UUID для OnlyOffice
   - Автоматически очищает файлы старше 5 минут

2. **Обновлена функция `_convert_via_onlyoffice()`:**
   - Добавлен параметр `public_url`
   - Использует правильный JSON формат:
     ```json
     {
       "async": false,
       "filetype": "docx",
       "key": "unique-uuid",
       "outputtype": "pdf",
       "url": "http://localhost:8000/temp-files/{file_id}"
     }
     ```
   - Отправляет `Content-Type: application/json`

3. **Обновлен endpoint `/api/convert-to-pdf`:**
   - Регистрирует файл в `temp_files_storage` перед конвертацией
   - Генерирует публичный URL: `http://localhost:8000/temp-files/{uuid}`
   - Передает URL через переменную окружения `TEMP_FILE_URL`
   - Очищает регистрацию после конвертации

4. **Обновлена функция `docx_to_pdf()`:**
   - Читает `TEMP_FILE_URL` из окружения
   - Передает public_url в `_convert_via_onlyoffice()`

## Настройка для production (rowline.me)

В переменных окружения systemd службы добавить:
```ini
Environment="PUBLIC_URL=http://rowline.me"
```

Или если OnlyOffice работает на том же сервере:
```ini
Environment="PUBLIC_URL=http://localhost:8000"
```

## Как это работает:

1. Клиент загружает DOCX файл на `/api/convert-to-pdf`
2. FastAPI сохраняет файл в `temp/{uuid}/filename.docx`
3. FastAPI регистрирует файл: `temp_files_storage[file_id] = {path, created_at}`
4. FastAPI генерирует URL: `http://localhost:8000/temp-files/{file_id}`
5. FastAPI вызывает `any_to_pdf()` с `TEMP_FILE_URL` в окружении
6. `docx_to_pdf()` вызывает `_convert_via_onlyoffice()` с public_url
7. OnlyOffice получает JSON с URL
8. **OnlyOffice сам скачивает файл** с `/temp-files/{file_id}`
9. OnlyOffice конвертирует и возвращает URL результата
10. Python скачивает PDF с URL от OnlyOffice
11. FastAPI удаляет регистрацию из `temp_files_storage`
12. FastAPI возвращает PDF клиенту

## Важно:

- OnlyOffice должен иметь доступ к `PUBLIC_URL`
- Если OnlyOffice в Docker на том же сервере - используйте `http://172.17.0.1:8000` (gateway Docker)
- Если на разных серверах - используйте внешний домен `http://rowline.me`
- Временные файлы очищаются автоматически через 5 минут
- Для локальной разработки достаточно `http://localhost:8000`

## Тестирование:

```bash
# На сервере Ubuntu
cd /home/xml-converter
sudo systemctl restart xml-converter

# Проверить логи
sudo journalctl -u xml-converter -f

# Тестовый запрос
curl -X POST http://localhost:8000/api/convert-to-pdf \
  -F "file=@test.docx" \
  -o output.pdf
```

## Коммиты:
- `a157907` - feat: add temp file serving endpoint for OnlyOffice API
- `b183de7` - fix: add missing os import in api.py
