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
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from src import XlsxToXmlConverter, XmlFiller, any_to_pdf, UnsupportedFormat

# Create temp directory if it doesn't exist
TEMP_DIR.mkdir(parents=True, exist_ok=True)


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

# Path to static files (frontend)
STATIC_DIR = Path(__file__).parent.parent / "www"
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
# Use project folder instead of system /tmp
TEMP_DIR = Path(__file__).parent.parent / "temp"

# Thread pool for heavy operations
# On Windows use large thread pool instead of multiprocessing
import os
MAX_WORKERS = max(os.cpu_count() * 4, 16)  # Minimum 16 threads
executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

# Create temp directory if it doesn't exist
TEMP_DIR.mkdir(parents=True, exist_ok=True)


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
    
    # Create unique temp folder for this request
    import uuid
    request_id = str(uuid.uuid4())
    work_dir = TEMP_DIR / request_id
    work_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Save uploaded file
        input_path = work_dir / file.filename
        content = await file.read()
        
        # Async file write
        await asyncio.to_thread(input_path.write_bytes, content)
        
        output_dir = work_dir / "output"
        output_dir.mkdir(exist_ok=True)
        
        # Perform conversion in separate thread (don't block event loop)
        try:
            result_files = await asyncio.to_thread(
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
            raise HTTPException(status_code=400, detail=str(e))
        except FileNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        
        if not result_files:
            raise HTTPException(
                status_code=500,
                detail="Failed to create output files"
            )
        
        # If one file - return it directly
        if len(result_files) == 1:
            return FileResponse(
                path=result_files[0],
                filename=result_files[0].name,
                media_type="application/xml",
                headers={
                    "Content-Disposition": f'attachment; filename="{result_files[0].name}"'
                }
            )
        
        # If multiple files - create ZIP archive (also in separate thread)
        zip_path = work_dir / f"{input_path.stem}_converted.zip"
        
        def create_zip():
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for result_file in result_files:
                    zf.write(result_file, result_file.name)
        
        await asyncio.to_thread(create_zip)
        
        return FileResponse(
            path=zip_path,
            filename=zip_path.name,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{zip_path.name}"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup of temp files is deferred for FileResponse
        # In real app, add background task for cleanup
        pass


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
    file: UploadFile = File(..., description="File to convert to PDF")
):
    """
    Convert any supported file to PDF.

    Supported formats: PDF, HTML, XML, XLSX, XLS, DOCX, JPG, JPEG, PNG, BMP, TIFF, TXT, PY, LOG, MD
    """

    # Create unique temp folder for this request
    import uuid
    request_id = str(uuid.uuid4())
    work_dir = TEMP_DIR / request_id
    work_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Save uploaded file
        input_path = work_dir / file.filename
        content = await file.read()
        await asyncio.to_thread(input_path.write_bytes, content)

        # Define output path
        output_path = work_dir / (input_path.stem + ".pdf")

        # Convert to PDF
        try:
            await asyncio.to_thread(any_to_pdf, str(input_path), str(output_path))
        except UnsupportedFormat as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")

        if not output_path.exists():
            raise HTTPException(status_code=500, detail="Failed to create PDF file")

        return FileResponse(
            path=output_path,
            filename=output_path.name,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{output_path.name}"'
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
