# Rowline

A web-based file conversion toolkit built with FastAPI. Convert XLSX ↔ XML, documents to PDF, split/merge PDFs, extract audio, and create GIFs.

## Converters

| Converter | Route | Description |
|-----------|-------|-------------|
| **XLSX → XML** | `POST /api/convert` | Convert Excel to XML or fill XML templates |
| **Any → PDF** | `POST /api/convert-to-pdf` | Convert DOCX, TXT, images, etc. via LibreOffice |
| **Split PDF** | `POST /api/split-pdf` | Split PDF by page ranges |
| **Merge PDF** | `POST /api/merge-pdf` | Merge multiple PDFs |
| **Video → GIF** | `POST /api/video-to-gif` | Convert video to animated GIF |
| **MP4 → MP3** | `POST /api/mp4-to-mp3` | Extract audio track |
| **Health** | `GET /api/health` | Health check |

## Quick Start

```bash
pip install -r requirements.txt
python main.py
```

Visit **http://127.0.0.1:8000**

## CLI

```bash
python main.py cli <file.xlsx>
```

## Project Structure

```
rowline/
├── main.py
├── src/
│   ├── api.py                  # FastAPI server
│   ├── cli.py                  # CLI entry point
│   ├── xlsx2xml/
│   │   ├── converter.py
│   │   ├── xlsx_reader.py
│   │   ├── xml_filler.py
│   │   └── xml_writer.py
│   ├── pdf/
│   │   ├── any_to_pdf.py       # LibreOffice-based conversion
│   │   ├── splitter.py
│   │   ├── merger.py
│   │   └── pdf_to_excel.py
│   ├── gif/
│   │   └── video_to_gif.py
│   └── media_converters/
│       └── mp4_to_mp3.py
├── www/                        # Frontend
├── templates/                  # XML templates
└── examples/
```

## Dependencies

- **Python 3.9+**
- fastapi, uvicorn, python-multipart, aiofiles
- openpyxl, lxml
- pypdf, reportlab, pillow, img2pdf, docx2pdf
- moviepy
- **LibreOffice** (system dep for PDF conversion)
