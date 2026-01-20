# 🚀 Подробный гайд настройки PDF Converter на вашем Ubuntu сервере

## 📊 Характеристики вашего сервера:
- **CPU**: 2 ядра QEMU Virtual @ 2.45 GHz
- **RAM**: 2GB (текущее использование ~27%)
- **Disk**: 40GB (текущее использование ~18%)
- **OS**: Ubuntu 24.04.3 LTS
- **IP**: 104.207.95.72

## ⚡ Рекомендуемая конфигурация для максимальной производительности:

| Параметр | Значение | Обоснование |
|----------|----------|-------------|
| **UVICORN_WORKERS** | 2 | Ровно по количеству ядер CPU |
| **MAX_WORKERS** | 16 | Достаточно для I/O операций |
| **PROCESS_POOL_SIZE** | 2 | Минимум для CPU-bound задач |
| **MAX_CONCURRENT_OPERATIONS** | 4 | Экономит память (2GB RAM) |

## 🛠️ Пошаговая настройка

### Шаг 1: Подготовка сервера
```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка необходимого ПО
sudo apt install -y python3 python3-pip python3-venv wkhtmltopdf libmagic1 git htop iotop ncdu ufw

# Настройка фаервола
sudo ufw --force enable
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw status
```

### Шаг 2: Оптимизация системы для 2GB RAM
```bash
# Настройка swappiness (меньше использовать swap)
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
echo 'vm.vfs_cache_pressure=50' | sudo tee -a /etc/sysctl.conf
echo 'vm.dirty_ratio=10' | sudo tee -a /etc/sysctl.conf
echo 'vm.dirty_background_ratio=5' | sudo tee -a /etc/sysctl.conf

# Применение настроек
sudo sysctl -p

# Добавление 1GB swap файла
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Проверка swap
free -h
swapon -s
```

### Шаг 3: Настройка проекта
```bash
# Создание директории для проекта
sudo mkdir -p /var/www
sudo chown root:root /var/www

# Клонирование проекта (уже сделано)
cd /var/www/rowline.me

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Создание файла с переменными окружения
cat > .env << 'EOF'
UVICORN_WORKERS=2
MAX_WORKERS=16
PROCESS_POOL_SIZE=2
MAX_CONCURRENT_OPERATIONS=4
EOF

# Проверка переменных
cat .env
```

### Шаг 4: Создание SystemD сервиса
```bash
# Создание файла сервиса
sudo nano /etc/systemd/system/pdf-converter.service
```

**Содержимое /etc/systemd/system/pdf-converter.service:**
```ini
[Unit]
Description=PDF Converter Web Service (Optimized for 2CPU/2GB)
After=network.target
Requires=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/var/www/rowline.me
Environment="PATH=/var/www/rowline.me/venv/bin"
EnvironmentFile=/var/www/rowline.me/.env

# Запуск с оптимизацией для вашего железа
ExecStart=/var/www/rowline.me/venv/bin/python main.py --host 0.0.0.0 --port 8000 --workers 2
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

[Install]
WantedBy=multi-user.target
```

```bash
# Перезагрузка systemd и запуск сервиса
sudo systemctl daemon-reload
sudo systemctl enable pdf-converter
sudo systemctl start pdf-converter

# Проверка статуса
sudo systemctl status pdf-converter
```

### Шаг 5: Настройка Nginx (опционально)
```bash
# Установка Nginx
sudo apt install -y nginx

# Создание конфигурации
sudo nano /etc/nginx/sites-available/pdf-converter
```

**Содержимое /etc/nginx/sites-available/pdf-converter:**
```nginx
server {
    listen 80;
    server_name 104.207.95.72;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Таймауты для больших файлов
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        client_max_body_size 100M;
    }
}
```

```bash
# Активация конфигурации
sudo ln -s /etc/nginx/sites-available/pdf-converter /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

## 📊 Мониторинг и тестирование

### Проверка работы:
```bash
# Проверка API
curl http://127.0.0.1:8000/api/health
curl http://104.207.95.72/api/health

# Проверка процессов
ps aux | grep python

# Мониторинг ресурсов
htop
free -h
df -h
```

### Просмотр логов:
```bash
# Логи приложения
sudo journalctl -u pdf-converter -f

# Системные логи
tail -f /var/log/syslog
```

### Мониторинг производительности:
```bash
# Использование CPU и памяти
top -p $(pgrep -f "python main.py")

# Дисковый I/O
iotop

# Анализ дискового пространства
ncdu /var/www/rowline.me
```

## 🔧 Управление сервисом

### Обычные операции:
```bash
# Перезапуск
sudo systemctl restart pdf-converter

# Остановка
sudo systemctl stop pdf-converter

# Просмотр статуса
sudo systemctl status pdf-converter

# Просмотр логов
sudo journalctl -u pdf-converter -n 50
```

### При проблемах:
```bash
# Полная остановка и очистка
sudo systemctl stop pdf-converter
sudo pkill -f "python main.py"
sudo rm -rf /var/www/rowline.me/temp/*

# Перезапуск
sudo systemctl start pdf-converter
```

## 📈 Ожидаемая производительность

### На вашем сервере:
- **Одновременные пользователи**: 5-10
- **Файлы в минуту**: 15-30 (зависит от размера)
- **CPU использование**: 40-70% при нагрузке
- **RAM использование**: 600MB-1.4GB при нагрузке

### Ограничения:
- Максимум 100MB на файл
- Максимум 25 PDF файлов для объединения
- Ограничение в 4 одновременные операции

## 🚨 Важные замечания

### Мониторинг памяти:
- Следите за использованием RAM (не более 1.5GB)
- При необходимости увеличьте swap до 2GB
- Очищайте временные файлы регулярно

### Безопасность:
- Регулярно обновляйте систему: `sudo apt update && sudo apt upgrade`
- Настройте SSL сертификат для HTTPS
- Ограничьте доступ к серверу по IP если возможно

### Резервное копирование:
```bash
# Резервная копия настроек
tar -czf backup_$(date +%Y%m%d).tar.gz /var/www/rowline.me/.env /etc/systemd/system/pdf-converter.service /etc/nginx/sites-available/pdf-converter
```

## 🎯 Быстрый чек-лист готовности

- [ ] Система обновлена
- [ ] Swap настроен (1GB)
- [ ] Проект установлен в /var/www/rowline.me
- [ ] Виртуальное окружение создано
- [ ] Зависимости установлены
- [ ] Переменные окружения настроены
- [ ] SystemD сервис создан и запущен
- [ ] Nginx настроен (опционально)
- [ ] API доступно по http://104.207.95.72/api/health
- [ ] Мониторинг настроен (htop, journalctl)

**🎉 Готово!** Ваш PDF Converter оптимизирован для работы на сервере с 2 ядрами CPU и 2GB RAM.</content>
<parameter name="filePath">c:\Users\FYM\python\rowline.me\UBUNTU_SETUP_GUIDE.md