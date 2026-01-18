# Инструкция по обновлению на сервере Ubuntu

## 1. Подготовка

Убедитесь что OnlyOffice Document Server запущен:
```bash
sudo docker ps | grep onlyoffice
curl http://localhost:8080/healthcheck
```

## 2. Обновление кода

```bash
cd /home/xml-converter
git pull origin main
```

## 3. Настройка переменных окружения

Для Docker OnlyOffice на том же сервере OnlyOffice должен иметь доступ к FastAPI.
Docker контейнеры имеют доступ к хост-машине через IP `172.17.0.1` (шлюз Docker).

Отредактируйте systemd unit:
```bash
sudo nano /etc/systemd/system/xml-converter.service
```

Добавьте переменную окружения в секцию `[Service]`:
```ini
Environment="PUBLIC_URL=http://172.17.0.1:8000"
```

Полный пример секции `[Service]`:
```ini
[Service]
Type=simple
User=root
WorkingDirectory=/home/xml-converter
Environment="PYTHONUNBUFFERED=1"
Environment="ONLYOFFICE_URL=http://localhost:8080"
Environment="PUBLIC_URL=http://172.17.0.1:8000"
ExecStart=/usr/bin/python3 -m uvicorn src.api:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
```

## 4. Перезапуск службы

```bash
# Перезагрузить конфигурацию systemd
sudo systemctl daemon-reload

# Перезапустить службу
sudo systemctl restart xml-converter

# Проверить статус
sudo systemctl status xml-converter

# Следить за логами
sudo journalctl -u xml-converter -f
```

## 5. Проверка работы

### Проверка endpoint для временных файлов:

Создайте тестовый файл:
```bash
echo "test content" > /tmp/test.txt
```

В другом терминале запустите сервер (если еще не запущен) и проверьте:
```bash
# Проверка health
curl http://localhost:8000/api/health

# Попытка получить несуществующий файл (должно вернуть 404)
curl -v http://localhost:8000/temp-files/nonexistent-id
```

### Тестирование конвертации DOCX:

```bash
# Загрузите тестовый DOCX файл
curl -X POST http://localhost:8000/api/convert-to-pdf \
  -F "file=@/path/to/test.docx" \
  -o output.pdf

# Проверьте результат
file output.pdf
ls -lh output.pdf
```

## 6. Мониторинг логов

В логах должны появиться примерно такие сообщения:

```
🔍 Attempting OnlyOffice conversion using: http://localhost:8080
✅ OnlyOffice healthcheck passed
🌐 Public file URL: http://172.17.0.1:8000/temp-files/uuid-here
🔄 Sending conversion request to OnlyOffice
📋 Request data: {"async": false, "filetype": "docx", ...}
📥 OnlyOffice response status: 200
📦 OnlyOffice response JSON: {"endConvert": true, "fileUrl": "...", ...}
⬇️ Downloading PDF from: http://localhost:8080/cache/files/.../output.pdf
✅ PDF saved: /home/xml-converter/temp/uuid/file.pdf (12345 bytes)
✅ Converted via OnlyOffice Document Server
```

## 7. Устранение проблем

### Проблема: OnlyOffice не может скачать файл

**Симптомы:** Ошибка "Unable to download file" или timeout

**Решение:**
```bash
# Проверьте что OnlyOffice может достучаться до FastAPI
sudo docker exec -it <onlyoffice-container-id> bash
curl http://172.17.0.1:8000/api/health

# Если не работает, проверьте firewall
sudo iptables -L -n | grep 8000
sudo ufw status

# Разрешите доступ из Docker сети
sudo iptables -I INPUT -i docker0 -p tcp --dport 8000 -j ACCEPT
```

### Проблема: Все еще ошибка -8

**Проверьте:**
1. PUBLIC_URL установлен правильно
2. OnlyOffice может достучаться до этого URL
3. Файл существует в момент запроса OnlyOffice

```bash
# Проверьте переменные окружения службы
sudo systemctl show xml-converter | grep Environment
```

### Проблема: Файлы не очищаются

**Проверьте:**
```bash
# Посмотрите количество временных файлов
ls -la /home/xml-converter/temp/*/

# При необходимости очистите вручную
find /home/xml-converter/temp/ -type f -mmin +10 -delete
```

## 8. Альтернативная конфигурация: публичный домен

Если OnlyOffice на другом сервере или нужен публичный доступ:

```ini
Environment="PUBLIC_URL=http://rowline.me"
```

Убедитесь что nginx проксирует `/temp-files/*`:
```nginx
location /temp-files/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

## Коммиты
- `a157907` - feat: add temp file serving endpoint for OnlyOffice API
- `b183de7` - fix: add missing os import in api.py
- `532b49a` - test: add OnlyOffice API request format validation
