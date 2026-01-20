# 🚀 Полное руководство по развертыванию на Ubuntu Server

## ⚡ Специальная настройка для вашего сервера (2 CPU cores, 2GB RAM)

### 🎯 Характеристики вашего сервера:
- **CPU**: 2 ядра QEMU Virtual @ 2.45 GHz
- **RAM**: 2GB (текущее использование ~27%)
- **Disk**: 40GB (текущее использование ~18%)
- **OS**: Ubuntu 24.04.3 LTS

### 📊 Рекомендуемая конфигурация для вашего железа:

```bash
# Оптимальные настройки для 2 ядер CPU и 2GB RAM
export UVICORN_WORKERS=2          # 2 воркера (по количеству ядер)
export MAX_WORKERS=16             # 16 потоков на воркер (I/O операции)
export PROCESS_POOL_SIZE=2        # 2 процесса (не перегружать CPU)
export MAX_CONCURRENT_OPERATIONS=4 # 4 одновременные операции (экономить RAM)
```

### 🚀 Быстрый старт на вашем сервере:

```bash
# 1. Обновление системы
sudo apt update && sudo apt upgrade -y

# 2. Установка зависимостей
sudo apt install -y python3 python3-pip wkhtmltopdf libmagic1 git

# 3. Клонирование проекта
cd /var/www
git clone https://github.com/your-repo/rowline.me.git
cd rowline.me

# 4. Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# 5. Установка Python пакетов
pip install -r requirements.txt

# 6. Настройка переменных окружения
cat > .env << 'EOF'
UVICORN_WORKERS=2
MAX_WORKERS=16
PROCESS_POOL_SIZE=2
MAX_CONCURRENT_OPERATIONS=4
EOF

# 7. Загрузка переменных и запуск
export $(cat .env | xargs)
python main.py --host 0.0.0.0 --port 8000 --workers 2
```

### 💡 Почему эти настройки оптимальны:

| Параметр | Значение | Обоснование |
|----------|----------|-------------|
| **UVICORN_WORKERS** | 2 | Ровно по количеству ядер CPU |
| **MAX_WORKERS** | 16 | Достаточно для I/O операций, не жрет много памяти |
| **PROCESS_POOL_SIZE** | 2 | Минимум для CPU-bound задач |
| **MAX_CONCURRENT_OPERATIONS** | 4 | Ограничение для стабильности с 2GB RAM |

### 📈 Ожидаемая производительность:
- **Одновременные пользователи**: 10-20
- **Файлы в минуту**: 20-50 (зависит от размера)
- **CPU использование**: 60-80% при пиковой нагрузке
- **RAM использование**: 800MB-1.2GB при нагрузке

### ⚠️ Важные замечания:
- **Мониторьте память**: При 2GB RAM следите за использованием
- **Ограничение файлов**: Максимум 100MB на файл
- **Swap**: При необходимости добавьте 1-2GB swap
- **Бэкапы**: Регулярно бэкапьте `/var/www/rowline.me/temp/`

---

## 📋 Общие системные требования

### Системные требования:
- **Ubuntu 20.04 LTS или новее** (рекомендуется 22.04 LTS)
- **Процессор**: 4+ ядер (рекомендуется 8+ для высокой нагрузки)
- **Оперативная память**: 8GB+ (рекомендуется 16GB+)
- **Диск**: 50GB+ SSD/NVMe (рекомендуется 100GB+)
- **Сеть**: Стабильное интернет-соединение

### Проверка системных ресурсов:
```bash
# Проверка CPU
lscpu | grep -E "CPU\(s\)|Model name|Thread"

# Проверка памяти
free -h

# Проверка диска
df -h

# Проверка Ubuntu версии
lsb_release -a
```

---

## 🛠️ Шаг 1: Подготовка сервера

### 1.1 Обновление системы
```bash
# Обновление пакетов
sudo apt update
sudo apt upgrade -y
sudo apt autoremove -y
sudo apt autoclean

# Установка базовых утилит
sudo apt install -y curl wget git htop iotop ncdu ufw fail2ban
```

### 1.2 Настройка фаервола
```bash
# Включение UFW
sudo ufw enable

# Разрешение SSH (важно!)
sudo ufw allow ssh
sudo ufw allow 22/tcp

# Разрешение HTTP и HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Проверка статуса
sudo ufw status
```

### 1.3 Создание пользователя для приложения
```bash
# Создание пользователя
sudo adduser pdfuser

# Добавление в sudo группу (опционально, для администрирования)
sudo usermod -aG sudo pdfuser

# Переключение на нового пользователя
su - pdfuser

# Генерация SSH ключей (рекомендуется)
ssh-keygen -t ed25519 -C "pdf-converter-server"
```

### 1.4 Установка Python и системных зависимостей
```bash
# Установка Python 3.10+ (если не установлен)
sudo apt install -y python3 python3-pip python3-venv python3-dev

# Проверка версии Python
python3 --version
pip3 --version

# Установка системных библиотек для PDF и изображений
sudo apt install -y \
    wkhtmltopdf \
    libmagic1 \
    libmagic-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    libxcb1-dev \
    libx11-xcb-dev \
    libxcb-render0-dev \
    libxcb-shm0-dev \
    libxrender1 \
    libxrandr2 \
    libxss1 \
    libasound2-dev \
    libgtk-3-dev \
    libgconf-2-4

# Установка Node.js для дополнительных инструментов (опционально)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

---

## 📦 Шаг 2: Развертывание приложения

### 2.1 Клонирование и настройка проекта
```bash
# Переход в домашнюю директорию
cd ~

# Клонирование репозитория
git clone https://github.com/your-repo/pdf-converter.git
cd pdf-converter

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Обновление pip
pip install --upgrade pip

# Установка зависимостей
pip install -r requirements.txt

# Проверка установки
python main.py --help
```

### 2.2 Настройка переменных окружения
```bash
# Копирование шаблона
cp .env.example .env

# Редактирование конфигурации
nano .env
```

**Содержимое .env файла:**
```bash
# Производительность (адаптируйте под ваш сервер)
UVICORN_WORKERS=8
MAX_WORKERS=128
PROCESS_POOL_SIZE=16
MAX_CONCURRENT_OPERATIONS=64

# Сеть
HOST=127.0.0.1
PORT=8000

# Безопасность
SECRET_KEY=your-super-secret-key-here-change-this
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Логирование
LOG_LEVEL=INFO
LOG_FILE=/var/log/pdf-converter/app.log

# Временные файлы
TEMP_DIR=/tmp/pdf-converter
CLEANUP_INTERVAL=1800
```

### 2.3 Создание необходимых директорий
```bash
# Создание директорий для логов и временных файлов
sudo mkdir -p /var/log/pdf-converter
sudo mkdir -p /tmp/pdf-converter

# Настройка прав доступа
sudo chown -R pdfuser:pdfuser /var/log/pdf-converter
sudo chown -R pdfuser:pdfuser /tmp/pdf-converter

# Создание директории для SSL сертификатов (если используете HTTPS)
sudo mkdir -p /etc/ssl/pdf-converter
```

### 2.3 Оптимизация для сервера с 2GB RAM

```bash
# Проверка текущего состояния памяти
free -h

# Настройка swappiness (меньше использовать swap)
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf

# Оптимизация для низкой памяти
echo 'vm.vfs_cache_pressure=50' | sudo tee -a /etc/sysctl.conf
echo 'vm.dirty_ratio=10' | sudo tee -a /etc/sysctl.conf
echo 'vm.dirty_background_ratio=5' | sudo tee -a /etc/sysctl.conf

# Применение настроек
sudo sysctl -p

# Добавление 1GB swap (рекомендуется для 2GB RAM)
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Проверка swap
free -h
swapon -s
```

### 2.4 Мониторинг ресурсов на вашем сервере

```bash
# Установка инструментов мониторинга
sudo apt install -y htop iotop ncdu sysstat

# Мониторинг в реальном времени
htop

# Мониторинг дискового I/O
iotop

# Анализ использования диска
ncdu /var/www/rowline.me

# Системные метрики каждые 5 секунд
iostat -x 5

# Проверка температуры (если поддерживается)
sensors
```

### 2.5 Тестирование приложения
```bash
# Активация виртуального окружения
source venv/bin/activate

# Тестовый запуск
python main.py --host 127.0.0.1 --port 8000 --workers 1

# Проверка в другом терминале
curl http://127.0.0.1:8000/api/health

# Остановка (Ctrl+C)
```

---

## 🌐 Шаг 3: Настройка Nginx Reverse Proxy

### 3.1 Установка и базовая настройка Nginx
```bash
# Установка Nginx
sudo apt install -y nginx

# Проверка статуса
sudo systemctl status nginx
sudo systemctl enable nginx

# Создание конфигурации сайта
sudo nano /etc/nginx/sites-available/pdf-converter
```

### 3.2 Конфигурация Nginx
```nginx
# /etc/nginx/sites-available/pdf-converter
upstream pdf_app {
    # Для балансировки нагрузки между несколькими процессами
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    # Добавьте больше портов если используете несколько воркеров
}

server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # Логи
    access_log /var/log/nginx/pdf-converter.access.log;
    error_log /var/log/nginx/pdf-converter.error.log;

    # Безопасность
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Размер файлов
    client_max_body_size 500M;
    client_body_timeout 300s;
    client_header_timeout 60s;

    # Прокси настройки
    location / {
        proxy_pass http://pdf_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Таймауты для больших файлов
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;

        # WebSocket поддержка (если понадобится в будущем)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Статические файлы (оптимизация)
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # Сжатие
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/xml+rss
        application/json;
}
```

### 3.3 Активация конфигурации
```bash
# Создание символической ссылки
sudo ln -s /etc/nginx/sites-available/pdf-converter /etc/nginx/sites-enabled/

# Удаление дефолтной конфигурации
sudo rm /etc/nginx/sites-enabled/default

# Проверка конфигурации
sudo nginx -t

# Перезагрузка Nginx
sudo systemctl reload nginx

# Проверка статуса
sudo systemctl status nginx
```

---

## 🔒 Шаг 4: Настройка SSL (Let's Encrypt)

### 4.1 Установка Certbot
```bash
# Установка Certbot
sudo apt install -y certbot python3-certbot-nginx

# Получение сертификата
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Тестирование автоматического обновления
sudo certbot renew --dry-run
```

### 4.2 Настройка автоматического обновления
```bash
# Проверка таймера systemd
sudo systemctl status certbot.timer
sudo systemctl enable certbot.timer
```

---

## ⚙️ Шаг 5: Настройка SystemD Service

### 5.1 Создание сервиса (адаптировано для вашего сервера)

```bash
sudo nano /etc/systemd/system/pdf-converter.service
```

**Оптимизированная конфигурация для 2 ядер CPU и 2GB RAM:**
```ini
[Unit]
Description=PDF Converter Web Service (Optimized for 2CPU/2GB)
After=network.target
Requires=network.target

[Service]
Type=simple
User=pdfuser
Group=pdfuser
WorkingDirectory=/var/www/rowline.me
Environment="PATH=/var/www/rowline.me/venv/bin"
EnvironmentFile=/var/www/rowline.me/.env

# Запуск с оптимизацией для вашего железа
ExecStart=/var/www/rowline.me/venv/bin/python main.py --host 127.0.0.1 --port 8000 --workers 2
ExecReload=/bin/kill -s HUP $MAINPID

# Перезапуск при сбое
Restart=always
RestartSec=5

# Лимиты ресурсов (оптимизировано для 2GB RAM)
LimitNOFILE=1024
LimitNPROC=256
MemoryLimit=1.5G
MemoryHigh=1.2G

# Безопасность
NoNewPrivileges=yes
PrivateTmp=yes
ProtectHome=yes
ProtectSystem=strict
ReadWritePaths=/var/www/rowline.me/temp /tmp

[Install]
WantedBy=multi-user.target
```

### 5.2 Настройка лимитов памяти

```bash
# Создание файла с лимитами
sudo nano /etc/security/limits.d/pdf-converter.conf

# Содержимое файла:
pdfuser soft nofile 1024
pdfuser hard nofile 2048
pdfuser soft nproc 256
pdfuser hard nproc 512
```

### 5.3 Управление сервисом
```bash
# Перезагрузка конфигурации systemd
sudo systemctl daemon-reload

# Запуск сервиса
sudo systemctl start pdf-converter

# Проверка статуса
sudo systemctl status pdf-converter

# Включение автозапуска
sudo systemctl enable pdf-converter

# Просмотр логов
sudo journalctl -u pdf-converter -f
```

---

## 📊 Шаг 6: Мониторинг и оптимизация

### 6.1 Настройка логирования
```bash
# Создание директории для логов
sudo mkdir -p /var/log/pdf-converter

# Настройка ротации логов
sudo nano /etc/logrotate.d/pdf-converter

# Содержимое /etc/logrotate.d/pdf-converter
/var/log/pdf-converter/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 pdfuser pdfuser
    postrotate
        systemctl reload pdf-converter
    endscript
}
```

### 6.2 Мониторинг производительности
```bash
# Установка инструментов мониторинга
sudo apt install -y htop iotop ncdu sysstat

# Мониторинг в реальном времени
htop

# I/O мониторинг
iotop

# Дисковое использование
ncdu /

# Системные метрики
iostat -x 1
vmstat 1
```

### 6.3 Настройка лимитов системы
```bash
# Увеличение лимитов
sudo nano /etc/security/limits.conf

# Добавить в конец файла:
pdfuser soft nofile 65536
pdfuser hard nofile 65536
pdfuser soft nproc 4096
pdfuser hard nproc 4096

# Настройка sysctl для высокой нагрузки
sudo nano /etc/sysctl.conf

# Добавить:
net.core.somaxconn = 65536
net.ipv4.tcp_max_syn_backlog = 65536
net.ipv4.ip_local_port_range = 1024 65535
```

---

## 🔧 Шаг 7: Оптимизация производительности

### 7.1 Настройка для разных конфигураций серверов

**Для 4-ядерного сервера:**
```bash
UVICORN_WORKERS=4
MAX_WORKERS=64
PROCESS_POOL_SIZE=8
MAX_CONCURRENT_OPERATIONS=32
```

**Для 8-ядерного сервера:**
```bash
UVICORN_WORKERS=8
MAX_WORKERS=128
PROCESS_POOL_SIZE=16
MAX_CONCURRENT_OPERATIONS=64
```

**Для 16-ядерного сервера:**
```bash
UVICORN_WORKERS=16
MAX_WORKERS=256
PROCESS_POOL_SIZE=32
MAX_CONCURRENT_OPERATIONS=128
```

### 7.2 Оптимизация Nginx
```nginx
# Дополнительные оптимизации в nginx.conf
worker_processes auto;
worker_rlimit_nofile 65536;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    # Буферы
    client_body_buffer_size 128k;
    client_max_body_size 500M;

    # Таймауты
    keepalive_timeout 65;
    send_timeout 60;

    # Кэширование
    open_file_cache max=200000 inactive=20s;
    open_file_cache_valid 30s;
    open_file_cache_min_uses 2;
    open_file_cache_errors on;
}
```

### 7.3 Оптимизация Python
```bash
# Установка PyPy для повышения производительности (опционально)
# pip install pypy3
# Заменить python на pypy3 в сервисном файле

# Профилирование производительности
pip install py-spy

# Запуск профилирования
py-spy top --pid $(pgrep -f "python main.py")
```

---

## 🚨 Шаг 8: Troubleshooting

### 8.1 Распространенные проблемы

**Проблема: Сервис не запускается**
```bash
# Проверка логов
sudo journalctl -u pdf-converter -n 50

# Проверка файла сервиса
sudo systemctl status pdf-converter

# Ручной запуск для диагностики
cd /home/pdfuser/pdf-converter
source venv/bin/activate
python main.py --host 127.0.0.1 --port 8000
```

**Проблема: Nginx возвращает 502 Bad Gateway**
```bash
# Проверка доступности приложения
curl http://127.0.0.1:8000/api/health

# Проверка Nginx логов
sudo tail -f /var/log/nginx/error.log

# Проверка конфигурации upstream
sudo nginx -t
sudo systemctl reload nginx
```

**Проблема: Высокое использование CPU/памяти**
```bash
# Мониторинг процессов
ps aux --sort=-%cpu | head -10
ps aux --sort=-%mem | head -10

# Настройка лимитов в .env
MAX_CONCURRENT_OPERATIONS=32  # Уменьшить
UVICORN_WORKERS=4            # Уменьшить
```

**Проблема: Временные файлы накапливаются**
```bash
# Проверка использования диска
df -h /tmp

# Очистка вручную
sudo find /tmp/pdf-converter -type f -mtime +1 -delete

# Проверка настроек очистки в коде
```

### 8.2 Мониторинг и алерты
```bash
# Установка мониторинга
sudo apt install -y prometheus-node-exporter

# Проверка здоровья
curl -f http://localhost:8000/api/health || echo "Service is down"

# Настройка cron для регулярных проверок
crontab -e

# Добавить:
*/5 * * * * curl -f http://localhost:8000/api/health > /dev/null || systemctl restart pdf-converter
```

---

## 📈 Шаг 9: Масштабирование

### 9.1 Горизонтальное масштабирование
```bash
# Запуск нескольких экземпляров на разных портах
python main.py --host 127.0.0.1 --port 8001
python main.py --host 127.0.0.1 --port 8002

# Обновление Nginx upstream
upstream pdf_app {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}
```

### 9.2 Кэширование
```bash
# Установка Redis для кэширования
sudo apt install -y redis-server

# Настройка в приложении (будущая функция)
# CACHE_URL=redis://localhost:6379
```

### 9.3 Резервное копирование
```bash
# Создание скрипта резервного копирования
sudo nano /usr/local/bin/backup-pdf-converter.sh

#!/bin/bash
BACKUP_DIR="/var/backups/pdf-converter"
mkdir -p $BACKUP_DIR

# Бэкап конфигурации и логов
tar -czf $BACKUP_DIR/config-$(date +%Y%m%d).tar.gz \
    /home/pdfuser/pdf-converter/.env \
    /etc/nginx/sites-available/pdf-converter \
    /etc/systemd/system/pdf-converter.service

# Очистка старых бэкапов (старше 30 дней)
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

---

## 🎯 Финальная проверка

### Проверка работоспособности:
```bash
# Проверка всех компонентов
curl -I https://your-domain.com
curl https://your-domain.com/api/health

# Проверка SSL
openssl s_client -connect your-domain.com:443 -servername your-domain.com

# Проверка производительности
ab -n 100 -c 10 https://your-domain.com/api/health
```

### Мониторинг после развертывания:
```bash
# Статус всех сервисов
sudo systemctl status nginx pdf-converter

# Мониторинг ресурсов
htop

# Проверка логов
sudo journalctl -u pdf-converter -f
sudo tail -f /var/log/nginx/pdf-converter.access.log
```

---

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи: `sudo journalctl -u pdf-converter -n 100`
2. Проверьте Nginx логи: `sudo tail -f /var/log/nginx/error.log`
3. Проверьте системные ресурсы: `htop`
4. Перезапустите сервисы: `sudo systemctl restart pdf-converter nginx`

**Готово! 🎉 Ваш PDF-конвертер теперь работает на максимальной производительности Ubuntu сервера!**