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


def docx_to_pdf(input_path: str, output_path: str) -> None:
    """
    Convert DOCX to PDF.
    On Windows: uses installed Microsoft Word.
    On macOS: uses Word application.
    On Linux: requires LibreOffice to be installed.
    """
    import platform
    import shutil
    
    system = platform.system()
    
    # On Linux, skip docx2pdf and go straight to LibreOffice
    if system != "Linux":
        try:
            # Try docx2pdf (works on Windows/macOS with Word installed)
            out_dir = os.path.dirname(os.path.abspath(output_path)) or "."
            with tempfile.TemporaryDirectory() as tmp:
                from docx2pdf import convert as docx2pdf_convert
                docx2pdf_convert(input_path, tmp)
                for f in os.listdir(tmp):
                    if f.lower().endswith(".pdf"):
                        src_pdf = os.path.join(tmp, f)
                        with open(src_pdf, "rb") as src, open(output_path, "wb") as dst:
                            dst.write(src.read())
                        return
            raise RuntimeError("Failed to convert DOCX to PDF using docx2pdf")
        except (RuntimeError, NotImplementedError, Exception):
            pass  # Fall through to LibreOffice attempt
    
    # Try LibreOffice
    out_dir = os.path.dirname(os.path.abspath(output_path)) or "."
    
    # Check if libreoffice is installed
    if not shutil.which("libreoffice") and not shutil.which("soffice"):
        raise UnsupportedFormat(
            "DOCX conversion requires either Microsoft Word (Windows/macOS) "
            "or LibreOffice (Linux). Install with: sudo apt install libreoffice"
        )
    
    try:
        # Create environment to disable dconf warnings and user profile
        env = os.environ.copy()
        env["XDG_CONFIG_HOME"] = tempfile.gettempdir()
        env["XDG_CACHE_HOME"] = tempfile.gettempdir()
        
        # Convert using libreoffice with proper flags for server environments
        result = subprocess.run(
            ["libreoffice", "--headless", "--norestore", 
             "--convert-to", "pdf", 
             "--outdir", out_dir, input_path],
            capture_output=True,
            timeout=120,
            text=True,
            env=env
        )
        
        # LibreOffice creates output with same name as input
        lo_output = os.path.splitext(input_path)[0] + ".pdf"
        
        if os.path.exists(lo_output):
            if lo_output != output_path:
                os.rename(lo_output, output_path)
            return
        
        # If conversion failed, check error output
        error_msg = result.stderr if result.stderr else result.stdout
        raise RuntimeError(f"LibreOffice conversion failed: {error_msg}")
        
    except subprocess.TimeoutExpired:
        raise RuntimeError("LibreOffice conversion timed out")
    except FileNotFoundError:
        raise UnsupportedFormat(
            "LibreOffice not found. Install with: sudo apt install libreoffice"
        )
    except Exception as e:
        raise RuntimeError(f"DOCX conversion error: {str(e)}")


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


def excel_to_pdf(input_path: str, output_path: str) -> None:
    """
    Convert Excel (.xlsx, .xls) to PDF.
    Uses LibreOffice for conversion (works on all platforms).
    """
    import platform
    import shutil
    
    out_dir = os.path.dirname(os.path.abspath(output_path)) or "."
    
    # Check if libreoffice is installed
    if not shutil.which("libreoffice") and not shutil.which("soffice"):
        raise UnsupportedFormat(
            "Excel conversion requires LibreOffice. "
            "Install with: sudo apt install libreoffice (Linux) or brew install libreoffice (macOS)"
        )
    
    try:
        # Create environment to disable dconf warnings and user profile
        env = os.environ.copy()
        env["XDG_CONFIG_HOME"] = tempfile.gettempdir()
        env["XDG_CACHE_HOME"] = tempfile.gettempdir()
        
        # Convert using libreoffice
        result = subprocess.run(
            ["libreoffice", "--headless", "--norestore", 
             "--convert-to", "pdf", 
             "--outdir", out_dir, input_path],
            capture_output=True,
            timeout=120,
            text=True,
            env=env
        )
        
        # LibreOffice creates output with same name as input
        lo_output = os.path.splitext(input_path)[0] + ".pdf"
        
        if os.path.exists(lo_output):
            if lo_output != output_path:
                os.rename(lo_output, output_path)
            return
        
        # If conversion failed, check error output
        error_msg = result.stderr if result.stderr else result.stdout
        raise RuntimeError(f"LibreOffice conversion failed: {error_msg}")
        
    except subprocess.TimeoutExpired:
        raise RuntimeError("Excel conversion timed out")
    except FileNotFoundError:
        raise UnsupportedFormat(
            "LibreOffice not found. Install with: sudo apt install libreoffice"
        )
    except Exception as e:
        raise RuntimeError(f"Excel conversion error: {str(e)}")


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
