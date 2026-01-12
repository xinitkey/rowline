#!/usr/bin/env python3
"""
FastAPI модуль для XLSX to XML Converter.
Предоставляет REST API для конвертации файлов.
"""

import io
import zipfile
import tempfile
import shutil
import asyncio
from pathlib import Path
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from src import XlsxToXmlConverter, XmlFiller


# Создаём FastAPI приложение
app = FastAPI(
    title="XLSX to XML Converter API",
    description="API для конвертации XLSX файлов в XML формат",
    version="1.0.0"
)

# CORS настройки для разработки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Путь к статическим файлам (фронтенд)
STATIC_DIR = Path(__file__).parent.parent / "www"
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
# Используем папку внутри проекта вместо системного /tmp
TEMP_DIR = Path(__file__).parent.parent / "temp"

# Пул потоков для тяжёлых операций
# На Windows используем большой пул потоков вместо многопроцессности
import os
MAX_WORKERS = max(os.cpu_count() * 4, 16)  # Минимум 16 потоков
executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

# Создаём временную директорию если не существует
TEMP_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/api/health")
async def health_check():
    """Проверка работоспособности API."""
    return {"status": "ok", "message": "XLSX to XML Converter API is running"}


@app.get("/api/templates")
async def list_templates():
    """Получить список доступных XML шаблонов."""
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
    Синхронная функция конвертации (выполняется в отдельном потоке).
    """
    result_files = []
    
    if mode == "fill":
        if not template:
            raise ValueError("Для режима 'fill' необходимо указать шаблон")
        
        template_path = TEMPLATES_DIR / template
        if not template_path.exists():
            raise FileNotFoundError(f"Шаблон не найден: {template}")
        
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
        raise ValueError(f"Неизвестный режим: {mode}. Используйте 'fill' или 'convert'")
    
    return [Path(f) for f in result_files if Path(f).exists()]


@app.post("/api/convert")
async def convert_xlsx_to_xml(
    file: UploadFile = File(..., description="XLSX файл для конвертации"),
    mode: str = Form(default="fill", description="Режим: 'fill' или 'convert'"),
    template: Optional[str] = Form(default=None, description="Имя файла шаблона"),
    sheet_name: Optional[str] = Form(default=None, description="Имя листа (опционально)"),
    code_col: int = Form(default=6, description="Столбец с кодом (1-based)"),
    data_start_col: int = Form(default=7, description="Начальный столбец данных"),
    data_end_col: int = Form(default=12, description="Конечный столбец данных"),
    start_row: int = Form(default=9, description="Начальная строка данных")
):
    """
    Конвертировать XLSX файл в XML (асинхронно).
    
    - **file**: Загружаемый XLSX файл
    - **mode**: Режим работы ('fill' - заполнение шаблона, 'convert' - создание нового XML)
    - **template**: Имя шаблона из папки templates (для режима fill)
    - **sheet_name**: Конкретный лист для обработки (опционально, по умолчанию - все листы)
    """
    # Проверка формата файла
    if not file.filename.lower().endswith('.xlsx'):
        raise HTTPException(
            status_code=400, 
            detail="Неверный формат файла. Ожидается .xlsx"
        )
    
    # Создаём уникальную временную папку для этого запроса
    import uuid
    request_id = str(uuid.uuid4())
    work_dir = TEMP_DIR / request_id
    work_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Сохраняем загруженный файл
        input_path = work_dir / file.filename
        content = await file.read()
        
        # Асинхронная запись файла
        await asyncio.to_thread(input_path.write_bytes, content)
        
        output_dir = work_dir / "output"
        output_dir.mkdir(exist_ok=True)
        
        # Выполняем конвертацию в отдельном потоке (не блокируем event loop)
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
                detail="Не удалось создать выходные файлы"
            )
        
        # Если один файл - возвращаем его напрямую
        if len(result_files) == 1:
            return FileResponse(
                path=result_files[0],
                filename=result_files[0].name,
                media_type="application/xml",
                headers={
                    "Content-Disposition": f'attachment; filename="{result_files[0].name}"'
                }
            )
        
        # Если несколько файлов - создаём ZIP архив (тоже в отдельном потоке)
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
        # Очистка временных файлов откладывается для FileResponse
        # В реальном приложении нужно добавить background task для очистки
        pass


@app.post("/api/upload-template")
async def upload_template(file: UploadFile = File(...)):
    """
    Загрузить новый XML шаблон.
    """
    if not file.filename.lower().endswith('.xml'):
        raise HTTPException(
            status_code=400,
            detail="Неверный формат файла. Ожидается .xml"
        )
    
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    template_path = TEMPLATES_DIR / file.filename
    
    with open(template_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    return {
        "message": "Шаблон успешно загружен",
        "filename": file.filename
    }


@app.delete("/api/templates/{filename}")
async def delete_template(filename: str):
    """Удалить XML шаблон."""
    template_path = TEMPLATES_DIR / filename
    
    if not template_path.exists():
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    
    template_path.unlink()
    return {"message": f"Шаблон {filename} удалён"}


# Подключаем статические файлы (фронтенд)
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")


def cleanup_temp_files(max_age_hours: int = 24):
    """Очистка старых временных файлов."""
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
