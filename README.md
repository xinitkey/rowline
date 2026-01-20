# XLSX to XML Converter with PDF Operations

A high-performance Python application for converting Excel (XLSX) files to XML format with advanced PDF processing capabilities. Features async processing, progress tracking, and batch operations optimized for server deployment.

## 📋 Features

- ✅ Convert single sheet or all XLSX sheets to XML
- ✅ Convert various formats to PDF (DOCX, TXT, images, etc.)
- ✅ Split and merge PDF files with parallel processing
- ✅ Async PDF conversion with real-time progress tracking
- ✅ Batch conversion for multiple files simultaneously
- ✅ Configurable XML element names and structure
- ✅ Automatic data type handling (dates, numbers, booleans)
- ✅ CLI interface and REST API (FastAPI)
- ✅ Cyrillic character support
- ✅ High performance with multithreading and async processing
- ✅ Production-ready with nginx reverse proxy support

## 🚀 Quick Start

### Local Development

```bash
# Clone the repository
git clone <repository-url>
cd xlsx-to-xml-converter

# Install dependencies
pip install -r requirements.txt

# Start development server
python main.py --reload
```

### Production Deployment

```bash
# Install system dependencies
sudo apt update
sudo apt install -y python3 python3-pip wkhtmltopdf

# Install Python packages
pip install -r requirements.txt

# Start production server
python main.py --host 0.0.0.0 --port 8000 --workers 4
```

## ⚡ Performance & Scalability

### Platform-Optimized Configuration

The application automatically adapts to your platform:

- **Windows**: Single process + large thread pool
- **Linux/Ubuntu**: Multi-process architecture + threads + processes

### Environment Variables for Fine-Tuning

```bash
# Copy example configuration
cp .env.example .env

# Load environment variables
export $(cat .env | xargs)

# Or set manually for 16-core server:
export UVICORN_WORKERS=16
export MAX_WORKERS=256
export PROCESS_POOL_SIZE=32
export MAX_CONCURRENT_OPERATIONS=128
```

### Production Startup Commands

```bash
# Auto-configured (recommended)
python main.py --host 0.0.0.0 --port 8000

# Explicit worker count
python main.py --host 0.0.0.0 --port 8000 --workers 16

# With nginx reverse proxy
python main.py --host 127.0.0.1 --port 8000 --workers 16
```

### Performance Architecture

- **Uvicorn workers**: Multi-process request handling
- **Thread pool**: I/O-bound operations (files, network)
- **Process pool**: CPU-bound operations (PDF, XLSX processing)
- **Async I/O**: Asynchronous file read/write operations
- **Semaphore**: Concurrent heavy operation limiting
- **Background cleanup**: Automatic temporary file cleanup
- **Extended timeouts**: 30 minutes for large file processing, 1 hour for batch operations
- **Excel optimization**: Specialized handling with adaptive threading (up to 32 threads for large files)
- **Resource management**: CPU-aware thread allocation and memory optimization

### Excel Conversion Optimizations

The system includes maximum performance optimizations for Excel to PDF conversion:

- **Adaptive Threading**: CPU-aware thread pool (12 workers on 8-core system)
- **Large File Handling**: Special optimization path for files >100MB with 32 max threads
- **LibreOffice Tuning**: Performance environment variables and headless optimizations
- **Resource Limiting**: Excel conversions limited to 2 concurrent operations to prevent CPU saturation
- **Fallback Method**: Alternative conversion using openpyxl + reportlab for systems without LibreOffice
- **Memory Optimization**: Optimized allocation for headless LibreOffice operation

## 📖 Usage

### Command Line Interface

```bash
# Basic conversion (active sheet)
python main.py data.xlsx

# Specify output file
python main.py data.xlsx output.xml

# Convert specific sheet
python main.py data.xlsx --sheet "Sheet1"

# All sheets to one file
python main.py data.xlsx --all-sheets

# Each sheet to separate file
python main.py data.xlsx --all-sheets --separate

# Configure XML structure
python main.py data.xlsx --root "products" --record "product"

# Specify header and data row numbers
python main.py data.xlsx --header-row 2 --data-row 3
```

### Complete CLI Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `input` | Path to XLSX file | (required) |
| `output` | Path to XML file | `<input>.xml` |
| `-s, --sheet` | Sheet name | active sheet |
| `-a, --all-sheets` | Convert all sheets | `False` |
| `-sep, --separate` | Separate files for each sheet | `False` |
| `--header-row` | Header row number | `1` |
| `--data-row` | Data start row number | `2` |
| `--root` | Root XML element | `data` |
| `--record` | Record XML element | `record` |
| `--encoding` | File encoding | `utf-8` |
| `--no-format` | Disable formatting | `False` |
| `-v, --verbose` | Verbose output | `False` |

### REST API

The application provides a comprehensive REST API for all operations.

#### XLSX to XML Conversion

```bash
# Convert XLSX to XML
curl -X POST "http://localhost:8000/convert" \
  -F "file=@data.xlsx" \
  -F "sheet_name=Sheet1" \
  -o output.xml
```

#### PDF Operations

```bash
# Convert file to PDF
curl -X POST "http://localhost:8000/convert_to_pdf" \
  -F "file=@document.docx" \
  -o output.pdf

# Batch convert multiple files to PDF
curl -X POST "http://localhost:8000/batch_convert_to_pdf" \
  -F "files=@file1.txt" \
  -F "files=@file2.docx" \
  -o batch_result.json

# Check conversion progress
curl "http://localhost:8000/conversion_progress/{request_id}"

# Merge PDF files
curl -X POST "http://localhost:8000/merge_pdf" \
  -F "files=@doc1.pdf" \
  -F "files=@doc2.pdf" \
  -o merged.pdf

# Split PDF file
curl -X POST "http://localhost:8000/split_pdf" \
  -F "file=@document.pdf" \
  -F "pages=1,3,5-7" \
  -o split_result.zip
```

#### API Endpoints

- `POST /convert` - Convert XLSX to XML
- `POST /convert_to_pdf` - Convert file to PDF
- `POST /batch_convert_to_pdf` - Batch PDF conversion
- `GET /conversion_progress/{request_id}` - Check progress
- `POST /merge_pdf` - Merge PDF files
- `POST /split_pdf` - Split PDF file
- `GET /api/health` - Health check
- `GET /docs` - API documentation

### Python API

```python
from src import XlsxToXmlConverter, any_to_pdf_async, ConversionProgress

# XLSX to XML conversion
converter = XlsxToXmlConverter(
    root_element="products",
    row_element="product"
)

# Convert single sheet
converter.convert("data.xlsx", "output.xml")

# Convert specific sheet
converter.convert("data.xlsx", sheet_name="Products")

# Convert all sheets to one file
converter.convert_all_sheets("data.xlsx", "all_data.xml")

# Convert each sheet to separate file
converter.convert_all_sheets("data.xlsx", separate_files=True)

# Get XML as string
xml_string = converter.to_xml_string("data.xlsx")
print(xml_string)

# Async PDF conversion with progress tracking
import asyncio

async def convert_with_progress():
    progress = ConversionProgress()
    result = await any_to_pdf_async("document.docx", "output.pdf", progress)

    # Check progress
    step, status = progress.get_progress()
    print(f"Progress: {step}, Status: {status}")

asyncio.run(convert_with_progress())
```

### Individual Modules

```python
from src import XlsxReader, XmlWriter

# Read XLSX file
with XlsxReader("data.xlsx") as reader:
    print(f"Sheets: {reader.sheet_names}")

    sheet_data = reader.read_sheet("Sheet1")
    print(f"Headers: {sheet_data.headers}")
    print(f"Records: {len(sheet_data.rows)}")

# Write XML
writer = XmlWriter(root_element="items", row_element="item")
writer.write(sheet_data, "output.xml")
```

## 🏗️ Project Structure

```
xlsx-to-xml-converter/
├── main.py                    # CLI entry point
├── requirements.txt           # Python dependencies
├── README.md                  # Documentation
├── src/
│   ├── __init__.py           # Module exports
│   ├── api.py                # FastAPI application
│   ├── converter.py          # Main converter class
│   ├── xlsx_reader.py        # XLSX file reader
│   ├── xml_writer.py         # XML file writer
│   └── pdf/
│       ├── __init__.py       # PDF module exports
│       └── any_to_pdf.py     # PDF conversion engine
├── www/                      # Web frontend
│   ├── index.html
│   ├── js/
│   └── css/
├── templates/                # XML templates
├── examples/                 # Usage examples
└── temp/                     # Temporary files
```

## 📝 Sample Output

Input file `products.xlsx`:

| ID | Name | Price | In Stock |
|----|------|-------|----------|
| 1  | Product A | 100 | Yes |
| 2  | Product B | 200 | No |

Output file `products.xml`:

```xml
<?xml version='1.0' encoding='utf-8'?>
<data source_sheet="Sheet1" record_count="2">
  <record id="1">
    <ID>1</ID>
    <Name>Product A</Name>
    <Price>100</Price>
    <In_Stock>Yes</In_Stock>
  </record>
  <record id="2">
    <ID>2</ID>
    <Name>Product B</Name>
    <Price>200</Price>
    <In_Stock>No</In_Stock>
  </record>
</data>
```

## 🔧 Dependencies

- **openpyxl** >= 3.1.0 - XLSX file reading
- **lxml** >= 5.0.0 - XML creation and writing
- **fastapi** >= 0.100.0 - Web API framework
- **uvicorn** >= 0.20.0 - ASGI server
- **pdfkit** >= 1.0.0 - PDF generation
- **pypdf** >= 3.0.0 - PDF manipulation
- **python-multipart** - File upload handling

## 🌐 Nginx Configuration

For production deployment with nginx reverse proxy:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    # Static files
    location /static/ {
        alias /path/to/your/app/www/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # API endpoints
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeout settings
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;

        # File upload size
        client_max_body_size 100M;
    }

    # Health check
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

## 🚀 Deployment

### System Requirements

- Python 3.8+
- 2GB RAM minimum (4GB recommended)
- wkhtmltopdf for PDF generation
- nginx for reverse proxy (recommended)

### Production Checklist

- [ ] Set up nginx reverse proxy
- [ ] Configure SSL certificates
- [ ] Set up systemd service
- [ ] Configure log rotation
- [ ] Set up monitoring
- [ ] Configure backup strategy
- [ ] Test high-load scenarios

### Docker Deployment (Optional)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wkhtmltopdf \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

EXPOSE 8000

CMD ["python", "main.py", "--host", "0.0.0.0", "--port", "8000"]
```

## 📄 License

MIT License

# Each sheet to separate file
python main.py data.xlsx --all-sheets --separate

# Configure XML structure
python main.py data.xlsx --root "products" --record "product"

# Specify header and data row numbers
python main.py data.xlsx --header-row 2 --data-row 3
```

### Complete CLI Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `input` | Path to XLSX file | (required) |
| `output` | Path to XML file | `<input>.xml` |
| `-s, --sheet` | Sheet name | active sheet |
| `-a, --all-sheets` | Convert all sheets | `False` |
| `-sep, --separate` | Separate files for each sheet | `False` |
| `--header-row` | Header row number | `1` |
| `--data-row` | Data start row number | `2` |
| `--root` | Root XML element | `data` |
| `--record` | Record XML element | `record` |
| `--encoding` | File encoding | `utf-8` |
| `--no-format` | Disable formatting | `False` |
| `-v, --verbose` | Verbose output | `False` |

### Программный API

```python
from src import XlsxToXmlConverter

# Create converter
converter = XlsxToXmlConverter(
    root_element="products",
    row_element="product"
)

# Convert single sheet
converter.convert("data.xlsx", "output.xml")

# Convert specific sheet
converter.convert("data.xlsx", sheet_name="Products")

# Convert all sheets to one file
converter.convert_all_sheets("data.xlsx", "all_data.xml")

# Convert each sheet to separate file
converter.convert_all_sheets("data.xlsx", separate_files=True)

# Get XML as string
xml_string = converter.to_xml_string("data.xlsx")
print(xml_string)
```

### Individual Modules

```python
from src import XlsxReader, XmlWriter

# Read XLSX file
with XlsxReader("data.xlsx") as reader:
    print(f"Sheets: {reader.sheet_names}")
    
    sheet_data = reader.read_sheet("Sheet1")
    print(f"Headers: {sheet_data.headers}")
    print(f"Records: {len(sheet_data.rows)}")

# Write XML
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
    ├── example_basic.py     # Basic usage example
    └── example_advanced.py  # Advanced usage example
```

## 📝 Sample Output

Input file `products.xlsx`:

| ID | Name | Price | In Stock |
|----|------|-------|----------|
| 1  | Product A | 100 | Yes |
| 2  | Product B | 200 | No |

Output file `products.xml`:

```xml
<?xml version='1.0' encoding='utf-8'?>
<data source_sheet="Sheet1" record_count="2">
  <record id="1">
    <ID>1</ID>
    <Name>Product A</Name>
    <Price>100</Price>
    <In_Stock>Yes</In_Stock>
  </record>
  <record id="2">
    <ID>2</ID>
    <Name>Product B</Name>
    <Price>200</Price>
    <In_Stock>No</In_Stock>
  </record>
</data>
```

## 🔧 Dependencies

- **openpyxl** >= 3.1.0 - XLSX file reading
- **lxml** >= 5.0.0 - XML creation and writing
- **fastapi** >= 0.100.0 - Web API framework
- **uvicorn** >= 0.20.0 - ASGI server
- **pdfkit** >= 1.0.0 - PDF generation
- **pypdf** >= 3.0.0 - PDF manipulation
- **python-multipart** - File upload handling

## 🌐 Nginx Configuration

For production deployment with nginx reverse proxy:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    # Static files
    location /static/ {
        alias /path/to/your/app/www/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # API endpoints
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeout settings
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;

        # File upload size
        client_max_body_size 100M;
    }

    # Health check
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

## 🚀 Deployment

### System Requirements

- Python 3.8+
- 2GB RAM minimum (4GB recommended)
- wkhtmltopdf for PDF generation
- nginx for reverse proxy (recommended)

### Production Checklist

- [ ] Set up nginx reverse proxy
- [ ] Configure SSL certificates
- [ ] Set up systemd service
- [ ] Configure log rotation
- [ ] Set up monitoring
- [ ] Configure backup strategy
- [ ] Test high-load scenarios

### Docker Deployment (Optional)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wkhtmltopdf \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

EXPOSE 8000

CMD ["python", "main.py", "--host", "0.0.0.0", "--port", "8000"]
```

## 📄 License

MIT License
