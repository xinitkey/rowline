# Установка Microsoft шрифтов на Ubuntu для правильной конвертации DOCX

Проблема с текстом на фигурах в DOCX связана с отсутствием оригинальных Microsoft шрифтов на Linux сервере.

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
