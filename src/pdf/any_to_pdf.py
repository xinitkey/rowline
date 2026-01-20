import os
import tempfile
import mimetypes
import subprocess

import pdfkit          # html -> pdf [web:1]
from docx2pdf import convert as docx2pdf_convert  # docx -> pdf [web:9]
import img2pdf         # images -> pdf [web:10]
from PIL import Image  # img2pdf зависит от Pillow [web:10]
from pypdf import PdfReader, PdfWriter


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
    """
    Convert HTML to PDF using pdfkit (wkhtmltopdf).
    Configured for local file conversion with proper options.
    """
    import os
    import tempfile
    import subprocess
    
    # Get the directory of the input file for resolving relative paths
    input_dir = os.path.dirname(os.path.abspath(input_path))
    
    # Set up environment for wkhtmltopdf
    env = os.environ.copy()
    env['XDG_RUNTIME_DIR'] = tempfile.gettempdir()
    env['QT_QPA_PLATFORM'] = 'offscreen'  # For headless operation
    
    # Try using wkhtmltopdf directly with proper environment
    wkhtmltopdf_path = None
    for path in ['wkhtmltopdf', '/usr/bin/wkhtmltopdf', '/usr/local/bin/wkhtmltopdf']:
        try:
            result = subprocess.run([path, '--version'], capture_output=True, env=env, timeout=10)
            if result.returncode == 0:
                wkhtmltopdf_path = path
                break
        except (subprocess.SubprocessError, FileNotFoundError):
            continue
    
    if wkhtmltopdf_path:
        # Use wkhtmltopdf directly
        cmd = [
            wkhtmltopdf_path,
            '--page-size', 'A4',
            '--margin-top', '0.75in',
            '--margin-right', '0.75in', 
            '--margin-bottom', '0.75in',
            '--margin-left', '0.75in',
            '--encoding', 'UTF-8',
            '--enable-local-file-access',
            '--disable-external-links',
            '--disable-internal-links',
            '--load-error-handling', 'ignore',
            '--load-media-error-handling', 'ignore',
            input_path,
            output_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', 
                                  env=env, timeout=60, check=True)
            print(f"[HTML] wkhtmltopdf conversion completed successfully")
            return
        except subprocess.CalledProcessError as e:
            print(f"[HTML] wkhtmltopdf failed: {e}")
        except subprocess.TimeoutExpired:
            print(f"[HTML] wkhtmltopdf timed out")
    
    # Fallback to pdfkit with minimal options
    print(f"[HTML] Using pdfkit fallback...")
    options = {
        'page-size': 'A4',
        'encoding': 'UTF-8',
        'disable-external-links': None,
        'disable-internal-links': None,
        'load-error-handling': 'ignore',
        'load-media-error-handling': 'ignore',
    }
    
    try:
        pdfkit.from_file(input_path, output_path, options=options)
    except Exception as e:
        print(f"[HTML] pdfkit fallback also failed: {e}")
        raise RuntimeError(f"HTML to PDF conversion failed: {e}")


def docx_to_pdf(input_path: str, output_path: str) -> None:
    """
    Convert DOCX to PDF using LibreOffice.
    LibreOffice provides good compatibility with Microsoft Office documents.
    """
    import shutil
    import os
    
    out_dir = os.path.dirname(os.path.abspath(output_path)) or "."
    
    # Find LibreOffice command
    libreoffice_cmd = None
    for cmd in ["libreoffice", "soffice"]:
        if shutil.which(cmd):
            libreoffice_cmd = cmd
            break
    
    if not libreoffice_cmd:
        raise UnsupportedFormat(
            "DOCX to PDF conversion requires LibreOffice. "
            "Install with: sudo apt install libreoffice"
        )
    
    # Log file size for debugging
    file_size = os.path.getsize(input_path)
    print(f"[DOCX] Converting file: {os.path.basename(input_path)} ({file_size} bytes)")
    
    # Check if file is extremely large (>100MB)
    if file_size > 100 * 1024 * 1024:
        print(f"[DOCX] Warning: Large file detected ({file_size} bytes). Conversion may take a long time.")
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            mem_before = process.memory_info().rss / 1024 / 1024  # MB
            print(f"[DOCX] Memory usage before conversion: {mem_before:.1f} MB")
        except ImportError:
            print("[DOCX] psutil not available for memory monitoring")
    
    try:
        result = subprocess.run(
            [
                libreoffice_cmd,
                "--headless",
                "--invisible",  # Run without GUI for better performance
                "--nocrashreport",  # Disable crash reporting
                "--nodefault",  # Don't load default modules
                "--convert-to", "pdf",
                "--outdir", out_dir,
                input_path
            ],
            capture_output=True,
            timeout=600,  # Increased timeout for very large files (10 minutes)
            check=True,
            env={
                **os.environ,
                "XDG_CONFIG_HOME": tempfile.gettempdir(),
                "XDG_CACHE_HOME": tempfile.gettempdir()
            }
        )
        
        print(f"[DOCX] LibreOffice conversion completed successfully")
        
        # Log memory usage for large files
        if file_size > 100 * 1024 * 1024:
            try:
                mem_after = process.memory_info().rss / 1024 / 1024  # MB
                print(f"[DOCX] Memory usage after conversion: {mem_after:.1f} MB")
                print(f"[DOCX] Memory delta: {mem_after - mem_before:.1f} MB")
            except NameError:
                pass  # psutil not available
        
        # Log output safely (handle encoding issues)
        if result.stdout:
            safe_stdout = result.stdout.decode('utf-8', errors='replace')
            print(f"[DOCX] LibreOffice stdout: {safe_stdout}")
        if result.stderr:
            safe_stderr = result.stderr.decode('utf-8', errors='replace')
            print(f"[DOCX] LibreOffice stderr: {safe_stderr}")
        
        expected_pdf = os.path.join(out_dir, os.path.splitext(os.path.basename(input_path))[0] + ".pdf")
        if os.path.exists(expected_pdf):
            if expected_pdf != output_path:
                os.rename(expected_pdf, output_path)
            return
        
        raise RuntimeError("LibreOffice did not create PDF file")
        
    except subprocess.CalledProcessError as e:
        # Handle encoding issues in error output
        error_msg = str(e)
        if hasattr(e, 'stdout') and e.stdout:
            safe_stdout = e.stdout.decode('utf-8', errors='replace')
            error_msg += f" stdout: {safe_stdout}"
        if hasattr(e, 'stderr') and e.stderr:
            safe_stderr = e.stderr.decode('utf-8', errors='replace')
            error_msg += f" stderr: {safe_stderr}"
        raise RuntimeError(f"DOCX conversion failed: {error_msg}")
    except subprocess.TimeoutExpired:
        raise RuntimeError("DOCX conversion timed out")


def excel_to_pdf(input_path: str, output_path: str) -> None:
    """
    Convert Excel (XLSX/XLS) to PDF using LibreOffice.
    """
    import shutil
    import os
    
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
    
    # Log file size for debugging
    file_size = os.path.getsize(input_path)
    print(f"[Excel] Converting file: {os.path.basename(input_path)} ({file_size} bytes)")
    
    # Check if file is extremely large (>100MB)
    if file_size > 100 * 1024 * 1024:
        print(f"[Excel] Warning: Large file detected ({file_size} bytes). Conversion may take a long time.")
    
    try:
        result = subprocess.run(
            [
                libreoffice_cmd,
                "--headless",
                "--invisible",  # Run without GUI for better performance
                "--nocrashreport",  # Disable crash reporting
                "--nodefault",  # Don't load default modules
                "--convert-to", "pdf:calc_pdf_Export",
                "--outdir", out_dir,
                input_path
            ],
            capture_output=True,
            timeout=600,  # Increased timeout for very large files (10 minutes)
            check=True,
            env={
                **os.environ,
                "XDG_CONFIG_HOME": tempfile.gettempdir(),
                "XDG_CACHE_HOME": tempfile.gettempdir()
            }
        )
        
        print(f"[Excel] LibreOffice conversion completed successfully")
        
        # Log output safely (handle encoding issues)
        if result.stdout:
            safe_stdout = result.stdout.decode('utf-8', errors='replace')
            print(f"[Excel] LibreOffice stdout: {safe_stdout}")
        if result.stderr:
            safe_stderr = result.stderr.decode('utf-8', errors='replace')
            print(f"[Excel] LibreOffice stderr: {safe_stderr}")
        
        expected_pdf = os.path.join(out_dir, os.path.splitext(os.path.basename(input_path))[0] + ".pdf")
        if os.path.exists(expected_pdf):
            if expected_pdf != output_path:
                os.rename(expected_pdf, output_path)
            return
        
        raise RuntimeError("LibreOffice did not create PDF file")
        
    except subprocess.CalledProcessError as e:
        # Handle encoding issues in error output
        error_msg = str(e)
        if hasattr(e, 'stdout') and e.stdout:
            safe_stdout = e.stdout.decode('utf-8', errors='replace')
            error_msg += f" stdout: {safe_stdout}"
        if hasattr(e, 'stderr') and e.stderr:
            safe_stderr = e.stderr.decode('utf-8', errors='replace')
            error_msg += f" stderr: {safe_stderr}"
        raise RuntimeError(f"Excel conversion failed: {error_msg}")
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


def split_pdf(input_path: str, output_dir: str, pages: list[int] | None = None) -> list[str]:
    """
    Split PDF into multiple files.
    
    Args:
        input_path: Path to input PDF
        output_dir: Directory to save split files
        pages: List of page numbers to extract (1-based), if None - split all pages individually
    
    Returns:
        List of output file paths
    """
    reader = PdfReader(input_path)
    total_pages = len(reader.pages)
    
    if pages is None:
        # Split each page into separate file
        output_files = []
        for i in range(total_pages):
            writer = PdfWriter()
            writer.add_page(reader.pages[i])
            
            output_path = os.path.join(output_dir, f"page_{i+1:03d}.pdf")
            with open(output_path, "wb") as f:
                writer.write(f)
            output_files.append(output_path)
        return output_files
    else:
        # Extract specific pages into one file
        writer = PdfWriter()
        for page_num in pages:
            if 1 <= page_num <= total_pages:
                writer.add_page(reader.pages[page_num - 1])
        
        output_path = os.path.join(output_dir, "extracted_pages.pdf")
        with open(output_path, "wb") as f:
            writer.write(f)
        return [output_path]


def merge_pdf(input_paths: list[str], output_path: str) -> str:
    """
    Merge multiple PDF files into one.
    
    Args:
        input_paths: List of PDF file paths to merge
        output_path: Path for merged output file
    
    Returns:
        Output file path
    """
    writer = PdfWriter()
    
    for pdf_path in input_paths:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            writer.add_page(page)
    
    with open(output_path, "wb") as f:
        writer.write(f)
    
    return output_path
