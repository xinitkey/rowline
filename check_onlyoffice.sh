#!/bin/bash
echo "=== Проверка OnlyOffice Document Server ==="
echo ""

echo "1. Проверка Docker контейнера:"
sudo docker ps | grep onlyoffice
echo ""

echo "2. Проверка healthcheck:"
curl -v http://localhost:8080/healthcheck
echo ""
echo ""

echo "3. Проверка переменных окружения службы:"
sudo systemctl show xml-converter | grep Environment
echo ""

echo "4. Проверка статуса службы:"
sudo systemctl status xml-converter --no-pager
echo ""

echo "5. Последние логи службы:"
sudo journalctl -u xml-converter -n 50 --no-pager
