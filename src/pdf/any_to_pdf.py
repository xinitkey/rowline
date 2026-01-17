import os
import tempfile
import mimetypes
import subprocess

import pdfkit          # html -> pdf [web:1]
from docx2pdf import convert as docx2pdf_convert  # docx -> pdf [web:9]
import img2pdf         # images -> pdf [web:10]
from PIL import Image  # img2pdf зависит от Pillow [web:10]


class UnsupportedFormat(Exception):
    pass


def any_to_pdf(input_path: str, output_path: str | None = None) -> str:
    """
    Convert file to PDF by extension.
    Supports: .pdf, .html/.htm, .xml, .docx, .xlsx/.xls, images (.jpg/.jpeg/.png/.bmp/.tiff),
    text (.txt, .py, .log, .md).
    """
    if output_path is None:
        base, _ = os.path.splitext(input_path)
        output_path = base + ".pdf"

    ext = os.path.splitext(input_path)[1].lower()

    if ext == ".pdf":
        # Already PDF - just copy
        if input_path != output_path:
            with open(input_path, "rb") as src, open(output_path, "wb") as dst:
                dst.write(src.read())
        return output_path

    if ext in {".html", ".htm"}:
        html_to_pdf(input_path, output_path)
        return output_path

    if ext == ".xml":
        xml_to_pdf(input_path, output_path)
        return output_path

    if ext == ".docx":
        docx_to_pdf(input_path, output_path)
        return output_path

    if ext in {".xlsx", ".xls"}:
        excel_to_pdf(input_path, output_path)
        return output_path

    if ext in {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}:
        image_to_pdf(input_path, output_path)
        return output_path

    # Simple text files: read and render to PDF via wkhtmltopdf
    if ext in {".txt", ".py", ".log", ".md"}:
        text_to_pdf(input_path, output_path)
        return output_path

    # Fallback by MIME type
    mime, _ = mimetypes.guess_type(input_path)
    if mime and mime.startswith("image/"):
        image_to_pdf(input_path, output_path)
        return output_path

    raise UnsupportedFormat(f"Формат {ext} не поддерживается")


def html_to_pdf(input_path: str, output_path: str) -> None:
    # pdfkit использует wkhtmltopdf под капотом [web:1]
    pdfkit.from_file(input_path, output_path)


def _convert_via_onlyoffice(input_path: str, output_path: str, onlyoffice_url: str = None) -> bool:
    """
    Convert document to PDF using OnlyOffice Document Server API.
    Returns True if successful, False otherwise.
    
    OnlyOffice API Documentation: https://api.onlyoffice.com/editors/conversionapi
    """
    import requests
    import json
    import time
    
    # Get OnlyOffice URL from environment or use default
    if onlyoffice_url is None:
        onlyoffice_url = os.environ.get("ONLYOFFICE_URL", "http://localhost:8080")
    
    print(f"🔍 Attempting OnlyOffice conversion using: {onlyoffice_url}")
    
    # Check if OnlyOffice is available
    try:
        health_check = requests.get(f"{onlyoffice_url}/healthcheck", timeout=2)
        if health_check.status_code != 200:
            print(f"❌ OnlyOffice healthcheck failed: status {health_check.status_code}")
            return False
        print(f"✅ OnlyOffice healthcheck passed")
    except requests.exceptions.RequestException as e:
        print(f"❌ OnlyOffice healthcheck failed: {e}")
        return False
    
    # Read file content
    with open(input_path, "rb") as f:
        file_content = f.read()
    
    print(f"📄 File size: {len(file_content)} bytes")
    
    # Prepare conversion request
    conversion_api_url = f"{onlyoffice_url}/ConvertService.ashx"
    
    # Get file extension
    file_ext = os.path.splitext(input_path)[1].lower().lstrip(".")
    
    # Prepare request payload
    payload = {
        "async": False,
        "filetype": file_ext,
        "key": os.path.basename(input_path) + str(time.time()),  # Unique key
        "outputtype": "pdf",
        "title": os.path.basename(input_path),
        "url": ""  # Will be filled with base64 data URL
    }
    
    # Encode file as base64 data URL
    import base64
    file_base64 = base64.b64encode(file_content).decode('utf-8')
    mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    data_url = f"data:{mime_type};base64,{file_base64}"
    payload["url"] = data_url
    
    print(f"🔄 Sending conversion request to {conversion_api_url}")
    
    try:
        # Send conversion request
        response = requests.post(
            conversion_api_url,
            json=payload,
            timeout=60
        )
        
        print(f"📥 OnlyOffice response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ OnlyOffice returned status {response.status_code}: {response.text}")
            return False
        
        result = response.json()
        print(f"📦 OnlyOffice response: {json.dumps(result, indent=2)}")
        
        if result.get("error"):
            error_code = result.get("error")
            print(f"❌ OnlyOffice error code: {error_code}")
            return False
        
        # Download converted PDF
        pdf_url = result.get("fileUrl") or result.get("url")
        if not pdf_url:
            print(f"❌ OnlyOffice did not return PDF URL. Response keys: {result.keys()}")
            return False
        
        print(f"⬇️ Downloading PDF from: {pdf_url}")
        
        # Download PDF file
        pdf_response = requests.get(pdf_url, timeout=30)
        if pdf_response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(pdf_response.content)
            print(f"✅ PDF saved: {output_path} ({len(pdf_response.content)} bytes)")
            return True
        else:
            print(f"❌ Failed to download PDF from OnlyOffice: {pdf_response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ OnlyOffice request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ OnlyOffice conversion error: {e}")
        import traceback
        traceback.print_exc()
        return False


def docx_to_pdf(input_path: str, output_path: str) -> None:
    """
    Convert DOCX to PDF using OnlyOffice Document Server API only.
    OnlyOffice provides the best compatibility with Microsoft Office documents,
    including correct text positioning in shapes and SmartArt.
    
    Requires OnlyOffice Document Server running on http://localhost:8080
    or set ONLYOFFICE_URL environment variable.
    """
    
    # Use OnlyOffice Document Server API
    onlyoffice_result = _convert_via_onlyoffice(input_path, output_path)
    if onlyoffice_result:
        print("✅ Converted via OnlyOffice Document Server")
        return
    
    # If OnlyOffice failed, raise an error
    raise RuntimeError(
        "DOCX conversion failed. OnlyOffice Document Server is not available. "
        "Please ensure OnlyOffice is running on http://localhost:8080 or set ONLYOFFICE_URL environment variable. "
        "Check logs with: sudo docker ps | grep onlyoffice"
    )


def excel_to_pdf(input_path: str, output_path: str) -> None:
    """
    Convert Excel (XLSX/XLS) to PDF using LibreOffice.
    """
    import shutil
    
    out_dir = os.path.dirname(os.path.abspath(output_path)) or "."
    
    # Find LibreOffice command
    libreoffice_cmd = None
    for cmd in ["libreoffice", "soffice"]:
        if shutil.which(cmd):
            libreoffice_cmd = cmd
            break
    
    if not libreoffice_cmd:
        raise UnsupportedFormat(
            "Excel to PDF conversion requires LibreOffice. "
            "Install with: sudo apt install libreoffice"
        )
    
    try:
        subprocess.run(
            [
                libreoffice_cmd,
                "--headless",
                "--convert-to", "pdf:calc_pdf_Export",
                "--outdir", out_dir,
                input_path
            ],
            capture_output=True,
            timeout=120,
            check=True,
            env={
                **os.environ,
                "XDG_CONFIG_HOME": tempfile.gettempdir(),
                "XDG_CACHE_HOME": tempfile.gettempdir()
            }
        )
        
        expected_pdf = os.path.join(out_dir, os.path.splitext(os.path.basename(input_path))[0] + ".pdf")
        if os.path.exists(expected_pdf):
            if expected_pdf != output_path:
                os.rename(expected_pdf, output_path)
            return
        
        raise RuntimeError("LibreOffice did not create PDF file")
        
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Excel conversion failed: {e}")
    except subprocess.TimeoutExpired:
        raise RuntimeError("Excel conversion timed out")


def image_to_pdf(input_path: str, output_path: str) -> None:
    # img2pdf.convert возвращает bytes PDF [web:10]
    with open(output_path, "wb") as f_out:
        f_out.write(img2pdf.convert(input_path))


def xml_to_pdf(input_path: str, output_path: str) -> None:
    """
    Convert XML to PDF with formatting.
    """
    import html as html_module
    
    with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
        xml_content = f.read()
    
    # Escape HTML entities and wrap in pre tag for formatting
    escaped_xml = html_module.escape(xml_content)
    
    html = f"""
    <html>
      <head>
        <meta charset="utf-8">
        <style>
          body {{
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 10pt;
            line-height: 1.4;
            padding: 20px;
            background: #f8f9fa;
          }}
          pre {{
            white-space: pre-wrap;
            word-wrap: break-word;
            background: white;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 4px;
          }}
        </style>
      </head>
      <body><pre>{escaped_xml}</pre></body>
    </html>
    """
    
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as tmp_html:
        tmp_html.write(html)
        tmp_html_path = tmp_html.name
    
    try:
        pdfkit.from_file(tmp_html_path, output_path)
    finally:
        os.remove(tmp_html_path)


def text_to_pdf(input_path: str, output_path: str) -> None:
    """
    Simple: wrap text in HTML and render to PDF via wkhtmltopdf.
    Can be replaced with fpdf/reportlab if you don't want to depend on wkhtmltopdf.
    """
    with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()

    html = f"""
    <html>
      <head>
        <meta charset="utf-8">
        <style>
          body {{
            font-family: monospace;
            white-space: pre-wrap;
          }}
        </style>
      </head>
      <body>{text}</body>
    </html>
    """

    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as tmp_html:
        tmp_html.write(html)
        tmp_html_path = tmp_html.name

    try:
        pdfkit.from_file(tmp_html_path, output_path)
    finally:
        os.remove(tmp_html_path)
