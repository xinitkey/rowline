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
    Convert DOCX to PDF with full support for SmartArt, diagrams, and complex graphics.
    Strategy:
    1. docx2pdf (Windows/macOS with Word) - best quality, preserves all elements
    2. LibreOffice with optimal settings - preserves graphics and formatting
    3. mammoth (DOCX → HTML → PDF) - fallback for simple documents
    """
    import platform
    import shutil
    
    system = platform.system()
    
    # Try docx2pdf on Windows/macOS with Word - best quality
    if system in ("Windows", "Darwin"):
        try:
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
        except (RuntimeError, NotImplementedError, Exception):
            pass  # Fall through to LibreOffice
    
    # Use LibreOffice as primary method on Linux - preserves all graphics
    out_dir = os.path.dirname(os.path.abspath(output_path)) or "."
    
    # Check if LibreOffice is installed
    libreoffice_cmd = None
    for cmd in ["libreoffice", "soffice"]:
        if shutil.which(cmd):
            libreoffice_cmd = cmd
            break
    
    if libreoffice_cmd:
        # Try with xvfb first for better text positioning in shapes
        if system == "Linux" and shutil.which("xvfb-run"):
            try:
                # Use xvfb with LibreOffice for better rendering of text in shapes
                subprocess.run(
                    [
                        "xvfb-run", "-a", "--server-args=-screen 0 1920x1080x24",
                        libreoffice_cmd,
                        "--headless",
                        "--convert-to", "pdf:writer_pdf_Export",
                        "--outdir", out_dir,
                        input_path
                    ],
                    capture_output=True,
                    timeout=120,
                    check=True,
                    env={
                        **os.environ,
                        "XDG_CONFIG_HOME": tempfile.gettempdir(),
                        "XDG_CACHE_HOME": tempfile.gettempdir(),
                        "DISPLAY": ":99"
                    }
                )
                
                # LibreOffice creates PDF in same dir with same name
                expected_pdf = os.path.join(out_dir, os.path.splitext(os.path.basename(input_path))[0] + ".pdf")
                if os.path.exists(expected_pdf):
                    if expected_pdf != output_path:
                        os.rename(expected_pdf, output_path)
                    return
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
                print(f"LibreOffice with xvfb conversion failed: {e}")
                pass  # Fall through to regular LibreOffice
        
        # Try regular LibreOffice without xvfb
        try:
            # Use LibreOffice with optimal PDF export settings
            # These filter options preserve graphics, SmartArt, diagrams
            subprocess.run(
                [
                    libreoffice_cmd,
                    "--headless",
                    "--convert-to", "pdf:writer_pdf_Export",
                    "--outdir", out_dir,
                    input_path
                ],
                capture_output=True,
                timeout=120,
                check=True,
                env={
                    **os.environ,
                    "XDG_CONFIG_HOME": tempfile.gettempdir(),
                    "XDG_CACHE_HOME": tempfile.gettempdir(),
                    # Force better quality for images and graphics
                    "SAL_USE_VCLPLUGIN": "svp"  # Use server-side rendering plugin
                }
            )
            
            # LibreOffice creates PDF in same dir with same name
            expected_pdf = os.path.join(out_dir, os.path.splitext(os.path.basename(input_path))[0] + ".pdf")
            if os.path.exists(expected_pdf):
                if expected_pdf != output_path:
                    os.rename(expected_pdf, output_path)
                return
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
            print(f"LibreOffice conversion failed: {e}")
            pass  # Fall through to unoconv
    
    # Try unoconv with xvfb for better rendering (preserves graphics better)
    if system == "Linux":
        # Try with xvfb for better rendering of complex elements
        if shutil.which("xvfb-run") and shutil.which("unoconv"):
            try:
                result = subprocess.run(
                    ["xvfb-run", "-a", "unoconv", "-f", "pdf", "-o", output_path, input_path],
                    capture_output=True,
                    timeout=120,
                    env={**os.environ, "XDG_CONFIG_HOME": tempfile.gettempdir(), "XDG_CACHE_HOME": tempfile.gettempdir()}
                )
                if os.path.exists(output_path) and result.returncode == 0:
                    return
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
        
        # Try unoconv without xvfb
        if shutil.which("unoconv"):
            try:
                subprocess.run(
                    ["unoconv", "-f", "pdf", "-o", output_path, input_path],
                    capture_output=True,
                    timeout=120,
                    check=True,
                    env={**os.environ, "XDG_CONFIG_HOME": tempfile.gettempdir(), "XDG_CACHE_HOME": tempfile.gettempdir()}
                )
                if os.path.exists(output_path):
                    return
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
                pass
    
    # Try mammoth only as last resort (doesn't support SmartArt/diagrams well)
    try:
        import mammoth
        
        # Convert DOCX to HTML with image extraction
        with open(input_path, "rb") as docx_file:
            # Extract images and convert to base64
            result = mammoth.convert_to_html(
                docx_file,
                convert_image=mammoth.images.img_element(lambda image: {
                    "src": "data:" + image.content_type + ";base64," + 
                           __import__('base64').b64encode(image.open().read()).decode('utf-8')
                })
            )
            html_content = result.value
        
        # Create full HTML document with styling
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: 'Times New Roman', Times, serif;
                    font-size: 12pt;
                    line-height: 1.5;
                    margin: 2cm;
                    color: #000;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin: 1em 0;
                }}
                table, th, td {{
                    border: 1px solid #000;
                    padding: 8px;
                }}
                img {{
                    max-width: 100%;
                    height: auto;
                }}
                h1, h2, h3, h4, h5, h6 {{
                    margin-top: 1em;
                    margin-bottom: 0.5em;
                }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        # Convert HTML to PDF using wkhtmltopdf
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as tmp_html:
            tmp_html.write(full_html)
            tmp_html_path = tmp_html.name
        
        try:
            pdfkit.from_file(tmp_html_path, output_path)
            if os.path.exists(output_path):
                return
        finally:
            os.remove(tmp_html_path)
            
    except ImportError:
        pass  # mammoth not installed
    except Exception as e:
        print(f"Mammoth conversion failed: {e}")
    
    # If we get here, all methods failed
    raise RuntimeError(f"Failed to convert DOCX to PDF. Please ensure LibreOffice or unoconv is installed.")

    # Try Pandoc as fallback
    if shutil.which("pandoc"):
        try:
            subprocess.run(
                ["pandoc", input_path, "-o", output_path, "--pdf-engine=wkhtmltopdf"],
                capture_output=True,
                timeout=120,
                check=True
            )
            if os.path.exists(output_path):
                return
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            pass  # Fall back to LibreOffice
    
    # Try LibreOffice as last resort
    out_dir = os.path.dirname(os.path.abspath(output_path)) or "."
    
    # Check if libreoffice is installed
    if not shutil.which("libreoffice") and not shutil.which("soffice"):
        raise UnsupportedFormat(
            "DOCX conversion requires unoconv or LibreOffice with xvfb. "
            "Install with: sudo apt install xvfb unoconv libreoffice"
        )
    
    try:
        # Create environment to disable dconf warnings and user profile
        env = os.environ.copy()
        env["XDG_CONFIG_HOME"] = tempfile.gettempdir()
        env["XDG_CACHE_HOME"] = tempfile.gettempdir()
        
        # Convert using libreoffice with better rendering options
        result = subprocess.run(
            ["libreoffice", "--headless", "--norestore", "--invisible",
             "--convert-to", "pdf:writer_pdf_Export", 
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
        
        # Convert using libreoffice with better rendering options
        result = subprocess.run(
            ["libreoffice", "--headless", "--norestore", "--invisible",
             "--convert-to", "pdf:writer_pdf_Export", 
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
