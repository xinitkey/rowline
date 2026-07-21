import os
import tempfile
import mimetypes
import subprocess
import asyncio
import shutil

import pdfkit
import img2pdf


class UnsupportedFormat(Exception):
    pass


def _find_libreoffice() -> str:
    paths = [
        "/usr/bin/libreoffice", "/usr/bin/soffice",
        "/usr/local/bin/libreoffice", "/usr/local/bin/soffice",
        "/opt/libreoffice/program/soffice",
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    for cmd in ["libreoffice", "soffice"]:
        if shutil.which(cmd):
            return cmd
    raise UnsupportedFormat("LibreOffice not found. Install: sudo apt install libreoffice")


def _run_libreoffice(input_path: str, output_dir: str, convert_filter: str = "pdf"):
    cmd = _find_libreoffice()
    env = {**os.environ, "XDG_CONFIG_HOME": tempfile.gettempdir(), "XDG_CACHE_HOME": tempfile.gettempdir()}
    subprocess.run(
        [cmd, "--headless", "--convert-to", convert_filter, "--outdir", output_dir, input_path],
        capture_output=True, env=env, timeout=7200, check=True,
    )


async def any_to_pdf_async(input_path: str, output_path: str | None = None) -> str:
    if output_path is None:
        output_path = os.path.splitext(input_path)[0] + ".pdf"

    ext = os.path.splitext(input_path)[1].lower()

    if ext == ".pdf":
        if input_path != output_path:
            with open(input_path, "rb") as src, open(output_path, "wb") as dst:
                while chunk := src.read(8192):
                    dst.write(chunk)
        return output_path

    loop = asyncio.get_event_loop()

    if ext in {".html", ".htm"}:
        await loop.run_in_executor(None, _html_to_pdf, input_path, output_path)
    elif ext == ".xml":
        await loop.run_in_executor(None, _xml_to_pdf, input_path, output_path)
    elif ext == ".docx":
        await loop.run_in_executor(None, _docx_to_pdf, input_path, output_path)
    elif ext in {".xlsx", ".xls"}:
        await loop.run_in_executor(None, _excel_to_pdf, input_path, output_path)
    elif ext in {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".gif", ".webp"}:
        await loop.run_in_executor(None, _image_to_pdf, input_path, output_path)
    elif ext in {".txt", ".py", ".log", ".md", ".json", ".yaml", ".yml", ".csv"}:
        await loop.run_in_executor(None, _text_to_pdf, input_path, output_path)
    else:
        mime, _ = mimetypes.guess_type(input_path)
        if mime and mime.startswith("image/"):
            await loop.run_in_executor(None, _image_to_pdf, input_path, output_path)
        else:
            raise UnsupportedFormat(f"Unsupported format: {ext}")

    return output_path


def _html_to_pdf(input_path: str, output_path: str):
    pdfkit.from_file(input_path, output_path, options={
        'page-size': 'A4', 'encoding': 'UTF-8',
        'enable-local-file-access': None,
        'disable-external-links': None,
        'disable-internal-links': None,
        'load-error-handling': 'ignore',
        'load-media-error-handling': 'ignore',
    })


def _xml_to_pdf(input_path: str, output_path: str):
    import html
    with open(input_path, encoding="utf-8", errors="ignore") as f:
        content = f.read()
    escaped = html.escape(content)
    html_body = f"""<html><head><meta charset="utf-8"><style>
body {{ font-family: monospace; font-size: 10pt; padding: 20px; background: #f8f9fa; }}
pre {{ white-space: pre-wrap; background: white; padding: 15px; border: 1px solid #ddd; }}
</style></head><body><pre>{escaped}</pre></body></html>"""
    tmp = tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8")
    tmp.write(html_body)
    tmp.flush()
    try:
        pdfkit.from_file(tmp.name, output_path)
    finally:
        os.unlink(tmp.name)


def _docx_to_pdf(input_path: str, output_path: str):
    out_dir = os.path.dirname(os.path.abspath(output_path)) or "."
    _run_libreoffice(input_path, out_dir)
    expected = os.path.join(out_dir, os.path.splitext(os.path.basename(input_path))[0] + ".pdf")
    if os.path.exists(expected):
        if expected != output_path:
            os.replace(expected, output_path)
        return
    raise RuntimeError("LibreOffice did not produce PDF")


def _excel_to_pdf(input_path: str, output_path: str):
    out_dir = os.path.dirname(os.path.abspath(output_path)) or "."
    _run_libreoffice(input_path, out_dir, "pdf:calc_pdf_Export")
    expected = os.path.join(out_dir, os.path.splitext(os.path.basename(input_path))[0] + ".pdf")
    if os.path.exists(expected):
        if expected != output_path:
            os.replace(expected, output_path)
        return
    raise RuntimeError("LibreOffice did not produce PDF")


def _image_to_pdf(input_path: str, output_path: str):
    with open(output_path, "wb") as f:
        f.write(img2pdf.convert(input_path))


def _text_to_pdf(input_path: str, output_path: str):
    with open(input_path, encoding="utf-8", errors="ignore") as f:
        text = f.read()
    html_body = f"""<html><head><meta charset="utf-8"><style>
body {{ font-family: monospace; white-space: pre-wrap; }}
</style></head><body>{text}</body></html>"""
    tmp = tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8")
    tmp.write(html_body)
    tmp.flush()
    try:
        pdfkit.from_file(tmp.name, output_path)
    finally:
        os.unlink(tmp.name)
