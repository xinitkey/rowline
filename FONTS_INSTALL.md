# Установка OnlyOffice Document Server для конвертации DOCX

OnlyOffice обеспечивает отличную совместимость с Microsoft Office документами, включая правильное отображение текста в фигурах и SmartArt.

## Установка через Docker (рекомендуется)

```bash
# Установить Docker
sudo apt-get update
sudo apt-get install -y docker.io
sudo systemctl start docker
sudo systemctl enable docker

# Запустить OnlyOffice Document Server
sudo docker run -i -t -d -p 8080:80 \
  --name onlyoffice-documentserver \
  --restart=always \
  onlyoffice/documentserver

# Проверить статус
sudo docker ps | grep onlyoffice
curl http://localhost:8080/healthcheck
```

## Настройка URL OnlyOffice (если используете другой порт)

### Вариант 1: Поддомен (рекомендуется для внешнего доступа)

```bash
# 1. Добавить A-запись в DNS для docs.rowline.me -> IP сервера

# 2. Скопировать nginx конфигурацию
sudo cp nginx-onlyoffice.conf /etc/nginx/sites-available/onlyoffice
sudo ln -s /etc/nginx/sites-available/onlyoffice /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 3. Настроить SSL (если нужен HTTPS)
sudo certbot --nginx -d docs.rowline.me

# 4. Установить переменную окружения в systemd service
sudo nano /etc/systemd/system/xml-converter.service
```

Добавить в секцию `[Service]`:
```ini
Environment="ONLYOFFICE_URL=https://docs.rowline.me"
```

```bash
sudo systemctl daemon-reload
sudo systemctl restart xml-converter.service
```

### Вариант 2: Подпапка на основном домене

```bash
# 1. Добавить location блок в /etc/nginx/sites-available/rowline.me
# См. nginx-onlyoffice.conf (Вариант 2)

sudo nginx -t
sudo systemctl reload nginx

# 2. Установить переменную окружения
sudo nano /etc/systemd/system/xml-converter.service
```

Добавить:
```ini
Environment="ONLYOFFICE_URL=https://rowline.me/onlyoffice"
```

```bash
sudo systemctl daemon-reload
sudo systemctl restart xml-converter.service
```

### Вариант 3: Только внутренний доступ (по умолчанию)

Если OnlyOffice нужен только для Python приложения (не для внешних пользователей):

```bash
# Не требуется настройка nginx
# Python обращается напрямую к localhost:8080
# Переменная окружения не нужна - используется значение по умолчанию

# Просто запустить OnlyOffice Docker:
sudo docker run -i -t -d -p 127.0.0.1:8080:80 \
  --name onlyoffice-documentserver \
  --restart=always \
  onlyoffice/documentserver
```

**Рекомендация:** Используйте Вариант 3 (localhost) для безопасности, если OnlyOffice нужен только для конвертации файлов внутри приложения.

## Проверка работы

```bash
# Проверить доступность API
curl -X POST http://localhost:8080/ConvertService.ashx \
  -H "Content-Type: application/json" \
  -d '{"filetype":"docx","outputtype":"pdf","key":"test","url":"https://example.com/test.docx"}'
```

## Альтернатива: Установка без Docker

```bash
# Добавить репозиторий OnlyOffice
sudo apt-get install -y software-properties-common
sudo add-apt-repository ppa:onlyoffice/onlyoffice

# Установить OnlyOffice
sudo apt-get update
sudo apt-get install -y onlyoffice-documentserver

# Настроить и запустить
sudo /usr/bin/documentserver-prepare4migration.sh
sudo systemctl start ds-docservice
```

---

# Установка Microsoft шрифтов на Ubuntu (альтернативное решение)

Если не используете OnlyOffice, установка Microsoft шрифтов улучшит конвертацию через LibreOffice.

## Решение 1: Установка msttcorefonts

```bash
# Установить основные Microsoft шрифты
sudo apt-get update
sudo apt-get install -y ttf-mscorefonts-installer

# Принять лицензию во время установки (Tab -> Enter)

# Обновить кэш шрифтов
sudo fc-cache -f -v

# Перезапустить сервис
sudo systemctl restart xml-converter.service
```

## Решение 2: Установка дополнительных шрифтов Windows (рекомендуется)

```bash
# Установить Calibri, Arial, Times New Roman и другие
sudo apt-get install -y fonts-crosextra-carlito fonts-crosextra-caladea

# Или загрузить шрифты Windows вручную:
sudo mkdir -p /usr/share/fonts/truetype/msfonts
cd /usr/share/fonts/truetype/msfonts

# Скопировать .ttf файлы из Windows: C:\Windows\Fonts\
# Особенно важны: Arial, Calibri, Times New Roman, Verdana

# После копирования:
sudo fc-cache -f -v
sudo systemctl restart xml-converter.service
```

## Решение 3: Использовать OnlyOffice (лучшая совместимость с DOCX)

```bash
# Установить OnlyOffice Document Server (требует Docker)
sudo apt-get install -y docker.io
sudo docker pull onlyoffice/documentserver

# Запустить OnlyOffice
sudo docker run -i -t -d -p 8080:80 onlyoffice/documentserver

# Обновить код для использования OnlyOffice API вместо LibreOffice
```

## Проверка установленных шрифтов

```bash
# Проверить доступные шрифты
fc-list | grep -i arial
fc-list | grep -i calibri
fc-list | grep -i "times new roman"
```
