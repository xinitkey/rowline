#!/usr/bin/env python3
"""
FastAPI module for XLSX to XML Converter.
Provides REST API for file conversion.
"""

import io
import zipfile
import tempfile
import shutil
import asyncio
import os
from pathlib import Path
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import aiofiles

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from src import XlsxToXmlConverter, XmlFiller, any_to_pdf, any_to_pdf_async, ConversionProgress, UnsupportedFormat, split_pdf, merge_pdf

# Path to static files (frontend)
STATIC_DIR = Path(__file__).parent.parent / "www"
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
# Use project folder instead of system /tmp
TEMP_DIR = Path(__file__).parent.parent / "temp"

# Thread pool for heavy operations
import os
import platform

# Adaptive configuration based on platform and environment
import os
import platform

system = platform.system()
cpu_count = os.cpu_count() or 4  # fallback to 4 if None

# Allow environment variable overrides for fine-tuning
MAX_WORKERS = int(os.getenv('MAX_WORKERS', max(cpu_count * (8 if system != 'Windows' else 4), 16)))
PROCESS_POOL_SIZE = int(os.getenv('PROCESS_POOL_SIZE', min(cpu_count, 16 if system != 'Windows' else 4)))
MAX_CONCURRENT_OPERATIONS = int(os.getenv('MAX_CONCURRENT_OPERATIONS', min(cpu_count * (4 if system != 'Windows' else 2), 32 if system != 'Windows' else 8)))

# Special limits for Excel conversions (more restrictive due to high CPU usage)
EXCEL_MAX_CONCURRENT = int(os.getenv('EXCEL_MAX_CONCURRENT', min(cpu_count, 4 if system != 'Windows' else 2)))

if system == 'Windows':
    # Windows specific optimizations
    print(f"[CONFIG] Windows detected - using thread-based parallelism")
    print(f"[CONFIG] Thread pool: {MAX_WORKERS}, Concurrent ops: {MAX_CONCURRENT_OPERATIONS}, Excel ops: {EXCEL_MAX_CONCURRENT}")
else:
    # Linux/Unix full power mode
    print(f"[CONFIG] {system} detected - using full multiprocessing power")
    print(f"[CONFIG] Workers: auto-scaled, Thread pool: {MAX_WORKERS}, Process pool: {PROCESS_POOL_SIZE}, Concurrent ops: {MAX_CONCURRENT_OPERATIONS}, Excel ops: {EXCEL_MAX_CONCURRENT}")

executor = ThreadPoolExecutor(max_workers=MAX_WORKERS, thread_name_prefix="pdf-worker")

# Process pool for CPU-intensive tasks
try:
    process_executor = ProcessPoolExecutor(max_workers=PROCESS_POOL_SIZE)
    USE_MULTIPROCESSING = True
except Exception as e:
    print(f"[CONFIG] Process pool disabled: {e}")
    process_executor = None
    USE_MULTIPROCESSING = False

# Semaphore to limit concurrent heavy operations
operation_semaphore = asyncio.Semaphore(MAX_CONCURRENT_OPERATIONS)
excel_semaphore = asyncio.Semaphore(EXCEL_MAX_CONCURRENT)

# Global dictionary to track conversion progress
_conversion_progress: dict[str, ConversionProgress] = {}

# Create temp directory if it doesn't exist
TEMP_DIR.mkdir(parents=True, exist_ok=True)


async def save_uploaded_file_async(file: UploadFile, path: Path) -> None:
    """Asynchronously save uploaded file to disk."""
    async with aiofiles.open(path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    return len(content)


async def save_file_content_async(content: bytes, path: Path) -> None:
    """Asynchronously save file content to disk."""
    async with aiofiles.open(path, 'wb') as f:
        await f.write(content)


async def run_cpu_bound_task(func, *args, **kwargs):
    """Run CPU-bound task in process pool if available, otherwise in thread pool."""
    if USE_MULTIPROCESSING and process_executor:
        return await asyncio.get_event_loop().run_in_executor(
            process_executor, func, *args, **kwargs
        )
    else:
        return await asyncio.to_thread(func, *args, **kwargs)


async def cleanup_conversion_progress(request_id: str) -> None:
    """Clean up conversion progress tracking after a delay."""
    await asyncio.sleep(300)  # Keep progress for 5 minutes
    _conversion_progress.pop(request_id, None)


# Start background cleanup task
async def start_background_cleanup():
    """Start background task for cleaning up old temp files."""
    while True:
        cleanup_temp_files()
        await asyncio.sleep(1800)  # Run every 30 minutes


# Create FastAPI application
app = FastAPI(
    title="XLSX to XML Converter API",
    description="API for converting XLSX files to XML format",
    version="1.0.0"
)

# CORS settings for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize background tasks on startup."""
    # Start background cleanup task
    asyncio.create_task(start_background_cleanup())
    print("[STARTUP] Background cleanup task started")


@app.get("/api/health")
async def health_check():
    """Check API health."""
    return {"status": "ok", "message": "XLSX to XML Converter API is running"}


@app.get("/temp-files/{file_id}")
async def serve_temp_file(file_id: str):
    """Serve temporary files for OnlyOffice to download."""
    print(f"[TempFiles] Request: {file_id}")
    
    file_info = get_file_mapping(file_id)
    if not file_info:
        print(f"[TempFiles] ERROR: File not found in storage: {file_id}")
        raise HTTPException(status_code=404, detail="File not found")
    
    file_path = Path(file_info["path"])
    
    print(f"[TempFiles] Serving file: {file_path}")
    
    if not file_path.exists():
        print(f"[TempFiles] ERROR: File doesn't exist on disk: {file_path}")
        # Clean up missing file from storage
        remove_file_mapping(file_id)
        raise HTTPException(status_code=404, detail="File not found")
    
    print(f"[TempFiles] SUCCESS: Returning {file_path.name} ({file_path.stat().st_size} bytes)")
    
    return FileResponse(
        path=file_path,
        media_type="application/octet-stream",
        filename=file_path.name
    )


@app.get("/api/templates")
async def list_templates():
    """Get list of available XML templates."""
    templates = []
    
    if TEMPLATES_DIR.exists():
        for f in TEMPLATES_DIR.glob("*.xml"):
            templates.append({
                "name": f.stem,
                "filename": f.name,
                "size": f.stat().st_size
            })
    
    return {"templates": templates}


def _do_conversion(
    input_path: Path,
    output_dir: Path,
    mode: str,
    template: Optional[str],
    sheet_name: Optional[str],
    code_col: int,
    data_start_col: int,
    data_end_col: int,
    start_row: int
) -> list[Path]:
    """
    Synchronous conversion function (executed in a separate thread).
    """
    result_files = []
    
    if mode == "fill":
        if not template:
            raise ValueError("Template is required for 'fill' mode")
        
        template_path = TEMPLATES_DIR / template
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template}")
        
        filler = XmlFiller(template_path)
        
        if sheet_name:
            output_path = output_dir / f"{input_path.stem}_{sheet_name}.xml"
            filler.fill_from_xlsx(
                xlsx_path=input_path,
                output_path=output_path,
                sheet_name=sheet_name,
                code_column=code_col,
                data_start_column=data_start_col,
                data_end_column=data_end_col,
                start_row=start_row
            )
            result_files.append(output_path)
        else:
            result_files = filler.fill_all_sheets(
                xlsx_path=input_path,
                output_dir=output_dir,
                code_column=code_col,
                data_start_column=data_start_col,
                data_end_column=data_end_col,
                start_row=start_row
            )
    
    elif mode == "convert":
        converter = XlsxToXmlConverter()
        
        if sheet_name:
            output_path = output_dir / f"{input_path.stem}_{sheet_name}.xml"
            converter.convert(
                input_path=input_path,
                output_path=output_path,
                sheet_name=sheet_name,
                start_row=start_row
            )
            result_files.append(output_path)
        else:
            result_files = converter.convert_all_sheets(
                input_path=input_path,
                output_path=output_dir,
                start_row=start_row,
                separate_files=True
            )
    else:
        raise ValueError(f"Unknown mode: {mode}. Use 'fill' or 'convert'")
    
    return [Path(f) for f in result_files if Path(f).exists()]


@app.post("/api/convert")
async def convert_xlsx_to_xml(
    file: UploadFile = File(..., description="XLSX file for conversion"),
    mode: str = Form(default="fill", description="Mode: 'fill' or 'convert'"),
    template: Optional[str] = Form(default=None, description="Template filename"),
    sheet_name: Optional[str] = Form(default=None, description="Sheet name (optional)"),
    code_col: int = Form(default=6, description="Code column (1-based)"),
    data_start_col: int = Form(default=7, description="Data start column"),
    data_end_col: int = Form(default=12, description="Data end column"),
    start_row: int = Form(default=9, description="Data start row")
):
    """
    Convert XLSX file to XML (asynchronously).
    
    - **file**: Uploaded XLSX file
    - **mode**: Operation mode ('fill' - fill template, 'convert' - create new XML)
    - **template**: Template name from templates folder (for fill mode)
    - **sheet_name**: Specific sheet to process (optional, default - all sheets)
    """
    # Check file format
    if not file.filename.lower().endswith('.xlsx'):
        raise HTTPException(
            status_code=400, 
            detail="Invalid file format. Expected .xlsx"
        )
    
    # Limit concurrent operations
    async with operation_semaphore:
        # Create unique temp folder for this request
        import uuid
        request_id = str(uuid.uuid4())
        work_dir = TEMP_DIR / request_id
        work_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Save uploaded file
            input_path = work_dir / file.filename
            content = await file.read()
            
            await save_file_content_async(content, input_path)
            
            output_dir = work_dir / "output"
            output_dir.mkdir(exist_ok=True)
            
            # Perform conversion in separate thread/process (CPU-bound)
            try:
                result_files = await run_cpu_bound_task(
                    _do_conversion,
                    input_path,
                    output_dir,
                    mode,
                    template,
                    sheet_name,
                    code_col,
                    data_start_col,
                    data_end_col,
                    start_row
                )
            except ValueError as e:
                # Sanitize error message for HTTP response
                safe_detail = str(e).encode('utf-8', errors='replace').decode('utf-8')
                raise HTTPException(status_code=400, detail=safe_detail)
            except FileNotFoundError as e:
                # Sanitize error message for HTTP response
                safe_detail = str(e).encode('utf-8', errors='replace').decode('utf-8')
                raise HTTPException(status_code=404, detail=safe_detail)
            
            if not result_files:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to create output files"
                )
            
            # If one file - return it directly
            if len(result_files) == 1:
                # Sanitize filename for HTTP headers (ASCII only)
                safe_filename = "".join(c for c in result_files[0].name if ord(c) < 128)
                if not safe_filename:
                    safe_filename = "result.xml"
                
                return FileResponse(
                    path=result_files[0],
                    filename=safe_filename,
                    media_type="application/xml",
                    headers={
                        "Content-Disposition": f'attachment; filename="{safe_filename}"'
                    }
                )
            
            # If multiple files - return JSON with download links
            if len(result_files) > 1:
                import uuid
                import json
                
                # Create unique session ID for this convert operation
                session_id = str(uuid.uuid4())
                session_dir = TEMP_DIR / session_id
                session_dir.mkdir(parents=True, exist_ok=True)
                
                # Move files to session directory and create download links
                file_links = []
                for result_file in result_files:
                    print(f"[CONVERT] Processing result_file: {result_file}, exists: {result_file.exists()}")
                    if not result_file.exists():
                        print(f"[CONVERT] Warning: result_file does not exist: {result_file}")
                        continue
                        
                    filename = result_file.name
                    session_file = session_dir / filename
                    
                    # Copy file to session directory
                    import shutil
                    print(f"[CONVERT] Copying {result_file} to {session_file}")
                    shutil.copy2(result_file, session_file)
                    
                    file_size = session_file.stat().st_size
                    print(f"[CONVERT] Copied file {filename}, size: {file_size} bytes")
                    
                    file_links.append({
                        "filename": filename,
                        "url": f"/temp-files/{session_id}/{filename}",
                        "size": file_size
                    })
                
                # Store session info (in a real app, use database/redis)
                session_info = {
                    "files": file_links,
                    "created": asyncio.get_event_loop().time(),
                    "session_id": session_id
                }
                
                # For demo, store in memory (in production use persistent storage)
                if not hasattr(convert_xlsx_to_xml, 'sessions'):
                    convert_xlsx_to_xml.sessions = {}
                convert_xlsx_to_xml.sessions[session_id] = session_info
                
                return {
                    "message": f"Converted to {len(file_links)} XML files",
                    "files": file_links,
                    "session_id": session_id
                }
        
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload-template")
async def upload_template(file: UploadFile = File(...)):
    """
    Upload new XML template.
    """
    if not file.filename.lower().endswith('.xml'):
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Expected .xml"
        )
    
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    template_path = TEMPLATES_DIR / file.filename
    
    with open(template_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    return {
        "message": "Template uploaded successfully",
        "filename": file.filename
    }


@app.delete("/api/templates/{filename}")
async def delete_template(filename: str):
    """Delete XML template."""
    template_path = TEMPLATES_DIR / filename
    
    if not template_path.exists():
        raise HTTPException(status_code=404, detail="Template not found")
    
    template_path.unlink()
    return {"message": f"Template {filename} deleted"}


@app.post("/api/convert-to-pdf")
async def convert_to_pdf(
    file: UploadFile = File(..., description="File to convert to PDF"),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Convert any supported file to PDF with async processing and progress tracking.

    Supported formats: PDF, HTML, XML, XLSX, XLS, DOCX, JPG, JPEG, PNG, BMP, TIFF, TXT, PY, LOG, MD
    """
    # Determine file type and choose appropriate semaphore
    filename_lower = file.filename.lower()
    is_excel = filename_lower.endswith(('.xlsx', '.xls'))
    
    # Use more restrictive semaphore for Excel files due to high CPU usage
    semaphore = excel_semaphore if is_excel else operation_semaphore
    
    async with semaphore:
        # Create unique temp folder for this request
        import uuid
        request_id = str(uuid.uuid4())
        work_dir = TEMP_DIR / request_id
        work_dir.mkdir(parents=True, exist_ok=True)

        # Initialize progress tracking
        progress = ConversionProgress(total_steps=1)
        _conversion_progress[request_id] = progress

        try:
            # Save uploaded file asynchronously
            input_path = work_dir / file.filename
            content = await file.read()

            # Check file size (limit to 500MB)
            file_size = len(content)
            if file_size > 500 * 1024 * 1024:  # 500MB limit
                raise HTTPException(
                    status_code=413,
                    detail="File too large. Maximum size is 500MB."
                )

            await save_file_content_async(content, input_path)

            # Define output path
            output_path = work_dir / (input_path.stem + ".pdf")

            # Convert to PDF asynchronously with progress tracking
            try:
                await asyncio.wait_for(
                    any_to_pdf_async(str(input_path), str(output_path), progress),
                    timeout=2000  # 2000 seconds (33 minutes) timeout for API level
                )
            except UnsupportedFormat as e:
                # Clean up progress tracking
                _conversion_progress.pop(request_id, None)
                # Sanitize error message for HTTP response
                safe_detail = str(e).encode('utf-8', errors='replace').decode('utf-8')
                raise HTTPException(status_code=400, detail=safe_detail)
            except Exception as e:
                # Clean up progress tracking
                _conversion_progress.pop(request_id, None)
                # Sanitize error message for HTTP response
                safe_detail = str(e).encode('utf-8', errors='replace').decode('utf-8')
                raise HTTPException(status_code=500, detail=f"Conversion failed: {safe_detail}")

            if not output_path.exists():
                _conversion_progress.pop(request_id, None)
                raise HTTPException(status_code=500, detail="Failed to create PDF file")

            # Schedule cleanup of progress tracking
            background_tasks.add_task(cleanup_conversion_progress, request_id)

            # Sanitize filename for HTTP headers (ASCII only)
            safe_filename = "".join(c for c in output_path.name if ord(c) < 128)
            if not safe_filename:
                safe_filename = "converted.pdf"

            return FileResponse(
                path=output_path,
                filename=safe_filename,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f'attachment; filename="{safe_filename}"'
                }
            )

        except Exception as e:
            # Clean up on any error
            _conversion_progress.pop(request_id, None)
            raise

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/batch-convert-to-pdf")
async def batch_convert_to_pdf(
    files: list[UploadFile] = File(..., description="Files to convert to PDF (up to 10 files)"),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Convert multiple files to PDF concurrently with progress tracking.

    Supported formats: PDF, HTML, XML, XLSX, XLS, DOCX, JPG, JPEG, PNG, BMP, TIFF, TXT, PY, LOG, MD
    Maximum 10 files per request for optimal performance.
    """
    if len(files) == 0:
        raise HTTPException(status_code=400, detail="At least 1 file required")
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 files allowed for batch conversion")

    # Limit concurrent operations (use more restrictive semaphore for batch)
    batch_semaphore = asyncio.Semaphore(min(MAX_CONCURRENT_OPERATIONS // 2, 2))
    async with batch_semaphore:
        # Create unique temp folder for this request
        import uuid
        request_id = str(uuid.uuid4())
        work_dir = TEMP_DIR / request_id
        work_dir.mkdir(parents=True, exist_ok=True)

        # Initialize progress tracking for batch
        progress = ConversionProgress(total_steps=len(files))
        _conversion_progress[request_id] = progress

        try:
            # Save all files and prepare conversion tasks
            conversion_tasks = []
            file_info = []

            for i, file in enumerate(files):
                # Read file content
                content = await file.read()
                file_size = len(content)

                if file_size > 200 * 1024 * 1024:  # 200MB limit per file for batch
                    raise HTTPException(
                        status_code=413,
                        detail=f"File {file.filename} too large. Maximum size is 200MB per file in batch mode."
                    )

                # Save file
                input_path = work_dir / f"input_{i}_{file.filename}"
                await save_file_content_async(content, input_path)

                # Prepare output path
                output_path = work_dir / f"output_{i}_{input_path.stem}.pdf"
                file_info.append((file.filename, str(output_path)))

                # Create conversion task
                task = any_to_pdf_async(str(input_path), str(output_path), None)
                conversion_tasks.append(task)

            # Convert all files concurrently
            progress.update(0, f"Converting {len(files)} files concurrently...")
            try:
                await asyncio.wait_for(
                    asyncio.gather(*conversion_tasks, return_exceptions=True),
                    timeout=3600  # 3600 seconds (1 hour) timeout for batch operations
                )
            except Exception as e:
                _conversion_progress.pop(request_id, None)
                safe_detail = str(e).encode('utf-8', errors='replace').decode('utf-8')
                raise HTTPException(status_code=500, detail=f"Batch conversion failed: {safe_detail}")

            # Check results and create ZIP archive
            successful_conversions = []
            for original_name, output_path in file_info:
                if os.path.exists(output_path):
                    successful_conversions.append((original_name, output_path))
                else:
                    print(f"[BATCH] Failed to convert: {original_name}")

            if not successful_conversions:
                _conversion_progress.pop(request_id, None)
                raise HTTPException(status_code=500, detail="All conversions failed")

            # Create ZIP archive with all converted PDFs
            import zipfile
            zip_path = work_dir / "batch_converted.zip"

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for original_name, pdf_path in successful_conversions:
                    # Use original filename but ensure .pdf extension
                    pdf_name = os.path.splitext(original_name)[0] + ".pdf"
                    zipf.write(pdf_path, pdf_name)

            progress.update(1, f"Successfully converted {len(successful_conversions)} files")

            # Schedule cleanup
            background_tasks.add_task(cleanup_conversion_progress, request_id)

            return FileResponse(
                path=zip_path,
                filename="batch_converted.zip",
                media_type="application/zip",
                headers={
                    "Content-Disposition": 'attachment; filename="batch_converted.zip"'
                }
            )

        except Exception as e:
            # Clean up on any error
            _conversion_progress.pop(request_id, None)
            raise


def parse_page_ranges(pages_str: str) -> list[int]:
    """
    Parse page ranges from string like "1,3-5,8"
    Returns list of page numbers (1-based)
    """
    pages = set()
    
    for part in pages_str.split(','):
        part = part.strip()
        if not part:
            continue
            
        if '-' in part:
            # Range like "3-5"
            start_end = part.split('-')
            if len(start_end) != 2:
                raise ValueError(f"Invalid range format: {part}")
            
            try:
                start = int(start_end[0].strip())
                end = int(start_end[1].strip())
                
                if start < 1 or end < 1 or start > end:
                    raise ValueError(f"Invalid range: {start}-{end}")
                
                pages.update(range(start, end + 1))
            except ValueError:
                raise ValueError(f"Invalid numbers in range: {part}")
        else:
            # Single page like "1"
            try:
                page = int(part)
                if page < 1:
                    raise ValueError(f"Page number must be positive: {page}")
                pages.add(page)
            except ValueError:
                raise ValueError(f"Invalid page number: {part}")
    
    return sorted(list(pages))


@app.get("/temp-files/{session_id}/{filename}")
async def serve_split_file(session_id: str, filename: str):
    """Serve individual split PDF files."""
    # Check if session exists
    if not hasattr(serve_split_file, 'sessions'):
        serve_split_file.sessions = getattr(split_pdf_endpoint, 'sessions', {})
    
    session_info = serve_split_file.sessions.get(session_id)
    if not session_info:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    # Find the file in session
    file_info = None
    for f in session_info['files']:
        if f['filename'] == filename:
            file_info = f
            break
    
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_path = TEMP_DIR / session_id / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@app.get("/temp-files/{session_id}/{filename}")
async def serve_convert_file(session_id: str, filename: str):
    """Serve individual converted XML files."""
    # Check if session exists
    if not hasattr(serve_convert_file, 'sessions'):
        serve_convert_file.sessions = getattr(convert_xlsx_to_xml, 'sessions', {})
    
    session_info = serve_convert_file.sessions.get(session_id)
    if not session_info:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    # Find the file in session
    file_info = None
    for f in session_info['files']:
        if f['filename'] == filename:
            file_info = f
            break
    
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_path = TEMP_DIR / session_id / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/xml",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@app.get("/download-zip/{session_id}")
async def download_session_zip(session_id: str):
    """Download all files from a session as ZIP archive."""
    print(f"[ZIP] Starting ZIP creation for session: {session_id}")
    print(f"[ZIP] TEMP_DIR: {TEMP_DIR}")
    
    # Check all possible session stores
    session_info = None
    
    # Check split PDF sessions
    if hasattr(split_pdf_endpoint, 'sessions'):
        session_info = split_pdf_endpoint.sessions.get(session_id)
        if session_info:
            print(f"[ZIP] Found session in split_pdf_endpoint")
    
    # Check convert XLSX sessions
    if not session_info and hasattr(convert_xlsx_to_xml, 'sessions'):
        session_info = convert_xlsx_to_xml.sessions.get(session_id)
        if session_info:
            print(f"[ZIP] Found session in convert_xlsx_to_xml")
    
    if not session_info:
        print(f"[ZIP] Session not found: {session_id}")
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    print(f"[ZIP] Session info: {len(session_info['files'])} files")
    
    # Create ZIP in memory
    zip_buffer = io.BytesIO()
    
    try:
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_info in session_info['files']:
                file_path = TEMP_DIR / session_id / file_info['filename']
                print(f"[ZIP] Checking file: {file_path}, exists: {file_path.exists()}")
                if file_path.exists():
                    file_size = file_path.stat().st_size
                    print(f"[ZIP] File size: {file_size} bytes")
                    if file_size > 0:
                        # Ensure filename is safe for ZIP
                        safe_filename = file_info['filename'].encode('utf-8', errors='replace').decode('utf-8')
                        print(f"[ZIP] Adding to ZIP as: {safe_filename}")
                        zf.write(str(file_path), safe_filename)
                        print(f"[ZIP] Successfully added {safe_filename}")
                    else:
                        print(f"[ZIP] Skipping empty file: {file_info['filename']}")
                else:
                    print(f"[ZIP] File not found: {file_path}")
        
        zip_size = zip_buffer.tell()
        print(f"[ZIP] Created ZIP with {len(session_info['files'])} files, total size: {zip_size} bytes")
        
        if zip_size == 0:
            raise HTTPException(status_code=500, detail="Failed to create ZIP archive - no files added")
            
    except Exception as e:
        print(f"[ZIP] Error creating ZIP: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create ZIP: {str(e)}")
    
    zip_buffer.seek(0)
    zip_data = zip_buffer.read()
    
    # Generate safe filename
    safe_zip_filename = f"files_{session_id[:8]}.zip"
    
    return Response(
        content=zip_data,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_zip_filename}"'
        }
    )


@app.post("/api/split-pdf")
async def split_pdf_endpoint(
    file: UploadFile = File(..., description="PDF file to split"),
    pages: str = Form(default="", description="Comma-separated page numbers to extract (1-based), empty for split all pages")
):
    """
    Split PDF file into multiple files.

    - **file**: PDF file to split
    - **pages**: Comma-separated page numbers (e.g., "1,3,5"), empty to split each page individually
    """
    # Limit concurrent operations
    async with operation_semaphore:
        # Create unique temp folder for this request
        import uuid
        request_id = str(uuid.uuid4())
        work_dir = TEMP_DIR / request_id
        work_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Save uploaded file
            input_path = work_dir / file.filename
            content = await file.read()
            
            # Check file size (limit to 500MB)
            file_size = len(content)
            if file_size > 500 * 1024 * 1024:  # 500MB limit
                raise HTTPException(
                    status_code=413, 
                    detail="File too large. Maximum size is 500MB."
                )
            
            await save_file_content_async(content, input_path)

            # Parse pages
            page_list = None
            if pages.strip():
                try:
                    page_list = parse_page_ranges(pages.strip())
                except ValueError as e:
                    raise HTTPException(status_code=400, detail=f"Invalid page format: {str(e)}")

            # Split PDF (potentially CPU-bound for large files)
            try:
                output_files = await run_cpu_bound_task(split_pdf, str(input_path), str(work_dir), page_list)
                # Ensure all files are written to disk
                await asyncio.sleep(0.5)
            except Exception as e:
                safe_detail = str(e).encode('utf-8', errors='replace').decode('utf-8')
                raise HTTPException(status_code=500, detail=f"Split failed: {safe_detail}")

            if not output_files:
                raise HTTPException(status_code=500, detail="No output files generated")

            # If multiple files, return JSON with download links
            if len(output_files) > 1:
                import uuid
                import json
                
                # Create unique session ID for this split operation
                session_id = str(uuid.uuid4())
                session_dir = TEMP_DIR / session_id
                session_dir.mkdir(parents=True, exist_ok=True)
                
                # Move files to session directory and create download links
                file_links = []
                for i, pdf_path in enumerate(output_files, 1):
                    print(f"[SPLIT] Processing pdf_path: {pdf_path}, exists: {Path(pdf_path).exists()}")
                    pdf_path_obj = Path(pdf_path)
                    if not pdf_path_obj.exists():
                        print(f"[SPLIT] Warning: pdf_path does not exist: {pdf_path}")
                        continue
                    
                    # Use the actual filename from the path
                    filename = pdf_path_obj.name
                    session_file = session_dir / filename
                    
                    # Copy file to session directory
                    import shutil
                    print(f"[SPLIT] Copying {pdf_path} to {session_file}")
                    shutil.copy2(pdf_path, session_file)
                    
                    file_size = session_file.stat().st_size
                    print(f"[SPLIT] Copied file {filename}, size: {file_size} bytes")
                    
                    file_links.append({
                        "filename": filename,
                        "url": f"/temp-files/{session_id}/{filename}",
                        "size": file_size
                    })
                
                # Store session info (in a real app, use database/redis)
                session_info = {
                    "files": file_links,
                    "created": asyncio.get_event_loop().time(),
                    "session_id": session_id
                }
                
                # For demo, store in memory (in production use persistent storage)
                if not hasattr(split_pdf_endpoint, 'sessions'):
                    split_pdf_endpoint.sessions = {}
                split_pdf_endpoint.sessions[session_id] = session_info
                
                return {
                    "message": f"PDF split into {len(file_links)} pages",
                    "files": file_links,
                    "session_id": session_id
                }
            else:
                # Single file
                output_path = Path(output_files[0])
                safe_filename = "".join(c for c in output_path.name if ord(c) < 128)
                if not safe_filename:
                    safe_filename = "split.pdf"

                return FileResponse(
                    path=output_path,
                    filename=safe_filename,
                    media_type="application/pdf",
                    headers={
                        "Content-Disposition": f'attachment; filename="{safe_filename}"'
                    }
                )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/merge-pdf")
async def merge_pdf_endpoint(
    files: list[UploadFile] = File(..., description="PDF files to merge")
):
    """
    Merge multiple PDF files into one.

    - **files**: List of PDF files to merge (2-25 files)
    """
    if len(files) < 2:
        raise HTTPException(status_code=400, detail="At least 2 PDF files required for merging")
    
    if len(files) > 25:
        raise HTTPException(status_code=400, detail="Maximum 25 PDF files allowed for merging")

    # Limit concurrent operations
    async with operation_semaphore:
        # Create unique temp folder for this request
        import uuid
        request_id = str(uuid.uuid4())
        work_dir = TEMP_DIR / request_id
        work_dir.mkdir(parents=True, exist_ok=True)

        try:
            input_paths = []
            
            # Save all files concurrently
            save_tasks = []
            file_contents = []
            
            for file in files:
                content = await file.read()
                file_contents.append((file.filename, content))
                if len(content) > 500 * 1024 * 1024:  # 500MB limit per file
                    raise HTTPException(
                        status_code=413, 
                        detail=f"File {file.filename} too large. Maximum size is 500MB per file."
                    )
            
            # Save files concurrently with unique names
            for i, (filename, content) in enumerate(file_contents):
                # Generate unique filename to avoid conflicts
                name, ext = os.path.splitext(filename)
                unique_filename = f"{name}_{i}{ext}"
                input_path = work_dir / unique_filename
                save_tasks.append(save_file_content_async(content, input_path))
                input_paths.append(str(input_path))
            
            # Wait for all files to be saved
            await asyncio.gather(*save_tasks)

            # Merge PDF (potentially CPU-bound for large files)
            output_path = work_dir / "merged.pdf"
            try:
                await run_cpu_bound_task(merge_pdf, input_paths, str(output_path))
            except Exception as e:
                safe_detail = str(e).encode('utf-8', errors='replace').decode('utf-8')
                raise HTTPException(status_code=500, detail=f"Merge failed: {safe_detail}")

            if not output_path.exists():
                raise HTTPException(status_code=500, detail="Failed to create merged PDF file")

            return FileResponse(
                path=output_path,
                filename="merged.pdf",
                media_type="application/pdf",
                headers={
                    "Content-Disposition": 'attachment; filename="merged.pdf"'
                }
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/conversion-progress/{request_id}")
async def get_conversion_progress(request_id: str):
    """
    Get conversion progress for a specific request.
    Returns current step and status message.
    """
    progress = _conversion_progress.get(request_id)
    if not progress:
        raise HTTPException(status_code=404, detail="Conversion not found or completed")

    step, status = progress.get_progress()
    return {
        "request_id": request_id,
        "progress": step,
        "status": status,
        "completed": step >= 1
    }


# Mount static files (frontend)
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")


def cleanup_temp_files(max_age_hours: int = 24):
    """Clean up old temporary files."""
    import time
    
    if not TEMP_DIR.exists():
        return
    
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    
    for item in TEMP_DIR.iterdir():
        if item.is_dir():
            try:
                age = current_time - item.stat().st_mtime
                if age > max_age_seconds:
                    shutil.rmtree(item)
            except Exception:
                pass
