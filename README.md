# Rowline Converter Hub

A universal web-based file conversion platform built with Python and FastAPI. Convert between various file formats including documents, spreadsheets, media files, and more — all through a clean web interface or REST API.

## Available Converters

### Media Converters
- **MP4 to MP3** — Extract audio from video files
- **Video to GIF** — Convert video files to animated GIFs with customizable settings

### Document Converters
- **XLSX to XML** — Convert Excel spreadsheets to XML format
- **Any to PDF** — Convert DOCX, TXT, images, and other formats to PDF
- **PDF Operations** — Merge, split, and manipulate PDF files

### More Coming Soon
The platform is designed for easy addition of new converters.

## Features

- Web Interface — User-friendly interface accessible from any browser
- REST API — Full API access for programmatic usage
- High Performance — Async processing with multi-threading and multiprocessing
- Batch Operations — Process multiple files simultaneously
- Progress Tracking — Real-time conversion progress monitoring
- Secure — Automatic cleanup of temporary files, file size limits
- Modern UI — Clean, responsive design
- Multi-language — Cyrillic and international character support

## Quick Start

### Local Development

```bash
# Clone the repository
git clone <repository-url>
cd rowline.me

# Install dependencies
pip install -r requirements.txt

# Start development server
python main.py --reload
```

Access the web interface at: **http://127.0.0.1:8000**

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

## Performance & Scalability

### Platform-Optimized Configuration

The application automatically adapts to your platform:

- **Windows**: Single process + large thread pool
- **Linux/Unix**: Multi-process architecture with threads + processes

### Environment Variables for Fine-Tuning

```bash
export UVICORN_WORKERS=16
export MAX_WORKERS=256
export PROCESS_POOL_SIZE=32
export MAX_CONCURRENT_OPERATIONS=128
```

### Performance Architecture

- **Uvicorn workers**: Multi-process request handling
- **Thread pool**: I/O-bound operations (files, network)
- **Process pool**: CPU-bound operations (media processing, PDF generation)
- **Async I/O**: Asynchronous file read/write operations
- **Semaphore**: Concurrent heavy operation limiting
- **Background cleanup**: Automatic temporary file cleanup

## Usage

### Web Interface

1. Open **http://localhost:8000** in your browser
2. Select the converter you need
3. Upload your file(s)
4. Configure conversion settings (if applicable)
5. Click "Convert" and download the result

### REST API

#### MP4 to MP3 Conversion

```bash
curl -X POST "http://localhost:8000/api/mp4-to-mp3" \
  -F "file=@video.mp4" \
  -o audio.mp3
```

#### Video to GIF Conversion

```bash
curl -X POST "http://localhost:8000/api/video-to-gif" \
  -F "file=@video.mp4" \
  -F "fps=15" \
  -F "width=480" \
  -o output.gif
```

#### XLSX to XML Conversion

```bash
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

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/mp4-to-mp3` | POST | Extract audio from video |
| `/api/video-to-gif` | POST | Convert video to GIF |
| `/convert` | POST | Convert XLSX to XML |
| `/convert_to_pdf` | POST | Convert file to PDF |
| `/batch_convert_to_pdf` | POST | Batch PDF conversion |
| `/merge_pdf` | POST | Merge PDF files |
| `/split_pdf` | POST | Split PDF file |
| `/conversion_progress/{id}` | GET | Check conversion progress |
| `/api/health` | GET | Health check |
| `/docs` | GET | Interactive API documentation |

### Python API

```python
# MP4 to MP3
from src.media_converters.mp4_to_mp3 import mp4_to_mp3
mp4_to_mp3("video.mp4", "audio.mp3")

# Video to GIF
from src.gif.video_to_gif import video_to_gif
video_to_gif("video.mp4", "output.gif", fps=15, width=480)

# XLSX to XML
from src import XlsxToXmlConverter
converter = XlsxToXmlConverter(root_element="data", row_element="record")
converter.convert("data.xlsx", "output.xml")

# Async PDF conversion
from src import any_to_pdf_async, ConversionProgress
import asyncio

async def convert_with_progress():
    progress = ConversionProgress()
    await any_to_pdf_async("document.docx", "output.pdf", progress)

asyncio.run(convert_with_progress())
```

## Project Structure

```
rowline.me/
├── main.py                     # Main entry point
├── requirements.txt            # Python dependencies
├── README.md                   # Documentation
├── src/
│   ├── __init__.py            # Module exports
│   ├── api.py                 # FastAPI application
│   ├── media_converters/
│   │   └── mp4_to_mp3.py      # MP4 to MP3 converter
│   ├── gif/
│   │   └── video_to_gif.py    # Video to GIF converter
│   ├── pdf/
│   │   ├── __init__.py        # PDF module exports
│   │   └── any_to_pdf.py      # PDF conversion engine
│   └── xlsx2xml/
│       ├── converter.py       # XLSX to XML converter
│       ├── xlsx_reader.py     # XLSX file reader
│       └── xml_writer.py      # XML file writer
├── www/                       # Web frontend
│   ├── index.html
│   ├── js/
│   └── css/
├── templates/                 # XML templates
├── examples/                  # Usage examples
└── temp/                      # Temporary files (auto-cleaned)
```

## Dependencies

### Core
- **Python 3.8+**
- **FastAPI** >= 0.100.0 — Web API framework
- **Uvicorn** >= 0.20.0 — ASGI server
- **python-multipart** — File upload handling

### Media Processing
- **moviepy** — Video and audio processing

### Document Processing
- **openpyxl** >= 3.1.0 — XLSX file reading
- **lxml** >= 5.0.0 — XML creation
- **pdfkit** >= 1.0.0 — PDF generation
- **pypdf** >= 3.0.0 — PDF manipulation
- **wkhtmltopdf** — System dependency for PDF generation

## Nginx Configuration

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
        client_max_body_size 500M;
    }

    # Health check
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

## Deployment

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

## License

MIT License
