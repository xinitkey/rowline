# XLSX to XML Converter

Конвертер файлов Excel (XLSX) в формат XML на Python с поддержкой PDF операций.

## 📋 Возможности

- ✅ Конвертация одного листа или всех листов XLSX → XML
- ✅ Конвертация различных форматов в PDF
- ✅ Разделение и объединение PDF файлов
- ✅ Сохранение в один файл или отдельные файлы
- ✅ Настраиваемые имена XML элементов
- ✅ Автоматическая обработка типов данных (даты, числа, boolean)
- ✅ CLI интерфейс и веб-API (FastAPI)
- ✅ Поддержка кириллицы
- ✅ Высокая производительность с многопоточностью и асинхронностью

## 🚀 Установка

```bash
# Клонируйте репозиторий
cd xml_converter

# Установите зависимости
pip install -r requirements.txt
```

## ⚡ Производительность и масштабируемость

### Настройка для максимальной производительности (Ubuntu/Linux)

Проект автоматически адаптируется к платформе:

- **Windows**: 1 процесс + большой пул потоков
- **Linux/Ubuntu**: Многопроцессная архитектура + потоки + процессы

#### Переменные окружения для тонкой настройки:

```bash
# Копируем пример конфигурации
cp .env.example .env

# Загружаем переменные
export $(cat .env | xargs)

# Или устанавливаем вручную для 16-ядерного сервера:
export UVICORN_WORKERS=16
export MAX_WORKERS=256
export PROCESS_POOL_SIZE=32
export MAX_CONCURRENT_OPERATIONS=128
```

#### Запуск с оптимизацией:

```bash
# Автоматическая настройка (рекомендуется)
python main.py

# Или с явным количеством воркеров
python main.py --workers 16

# Для production с reverse proxy (nginx)
python main.py --host 0.0.0.0 --port 8000 --workers 16
```

### Архитектура производительности:

- **Uvicorn workers**: Многопроцессная обработка запросов
- **Thread pool**: Для I/O-bound операций (файлы, сеть)
- **Process pool**: Для CPU-bound операций (PDF, XLSX обработка)
- **Async I/O**: Асинхронное чтение/запись файлов
- **Semaphore**: Ограничение одновременных тяжелых операций
- **Background cleanup**: Автоматическая очистка временных файлов

## 🚀 Установка

```bash
# Клонируйте репозиторий
cd xml_converter

# Установите зависимости
pip install -r requirements.txt
```

## 📖 Использование

### Командная строка

```bash
# Базовая конвертация (активный лист)
python main.py data.xlsx

# Указать выходной файл
python main.py data.xlsx output.xml

# Конвертировать конкретный лист
python main.py data.xlsx --sheet "Лист1"

# Все листы в один файл
python main.py data.xlsx --all-sheets

# Каждый лист в отдельный файл
python main.py data.xlsx --all-sheets --separate

# Настроить XML структуру
python main.py data.xlsx --root "products" --record "product"

# Указать строку заголовков и начала данных
python main.py data.xlsx --header-row 2 --data-row 3
```

### Полный список параметров

| Параметр | Описание | По умолчанию |
|----------|----------|--------------|
| `input` | Путь к XLSX файлу | (обязательный) |
| `output` | Путь к XML файлу | `<input>.xml` |
| `-s, --sheet` | Имя листа | активный лист |
| `-a, --all-sheets` | Все листы | `False` |
| `-sep, --separate` | Отдельные файлы | `False` |
| `--header-row` | Строка заголовков | `1` |
| `--data-row` | Строка начала данных | `2` |
| `--root` | Корневой элемент | `data` |
| `--record` | Элемент записи | `record` |
| `--encoding` | Кодировка | `utf-8` |
| `--no-format` | Без отступов | `False` |
| `-v, --verbose` | Подробный вывод | `False` |

### Программный API

```python
from src import XlsxToXmlConverter

# Создание конвертера
converter = XlsxToXmlConverter(
    root_element="products",
    row_element="product"
)

# Конвертация одного листа
converter.convert("data.xlsx", "output.xml")

# Конвертация конкретного листа
converter.convert("data.xlsx", sheet_name="Товары")

# Все листы в один файл
converter.convert_all_sheets("data.xlsx", "all_data.xml")

# Каждый лист в отдельный файл
converter.convert_all_sheets("data.xlsx", separate_files=True)

# Получить XML как строку
xml_string = converter.to_xml_string("data.xlsx")
print(xml_string)
```

### Использование отдельных модулей

```python
from src import XlsxReader, XmlWriter

# Чтение XLSX
with XlsxReader("data.xlsx") as reader:
    print(f"Листы: {reader.sheet_names}")
    
    sheet_data = reader.read_sheet("Sheet1")
    print(f"Заголовки: {sheet_data.headers}")
    print(f"Записей: {len(sheet_data.rows)}")

# Запись XML
writer = XmlWriter(root_element="items", row_element="item")
writer.write(sheet_data, "output.xml")
```

## 📁 Структура проекта

```
xml_converter/
├── main.py              # Точка входа (CLI)
├── requirements.txt     # Зависимости
├── README.md           # Документация
├── src/
│   ├── __init__.py     # Экспорт модулей
│   ├── converter.py    # Главный класс конвертера
│   ├── xlsx_reader.py  # Чтение XLSX файлов
│   └── xml_writer.py   # Запись XML файлов
└── examples/
    ├── example_basic.py     # Базовый пример
    └── example_advanced.py  # Продвинутый пример
```

## 📝 Пример вывода

Входной файл `products.xlsx`:

| ID | Название | Цена | В наличии |
|----|----------|------|-----------|
| 1  | Товар А  | 100  | Да        |
| 2  | Товар Б  | 200  | Нет       |

Выходной файл `products.xml`:

```xml
<?xml version='1.0' encoding='utf-8'?>
<data source_sheet="Sheet1" record_count="2">
  <record id="1">
    <ID>1</ID>
    <Название>Товар А</Название>
    <Цена>100</Цена>
    <В_наличии>Да</В_наличии>
  </record>
  <record id="2">
    <ID>2</ID>
    <Название>Товар Б</Название>
    <Цена>200</Цена>
    <В_наличии>Нет</В_наличии>
  </record>
</data>
```

## 🔧 Зависимости

- **openpyxl** >= 3.1.0 - чтение XLSX файлов
- **lxml** >= 5.0.0 - создание и запись XML

## 📄 Лицензия

MIT License
