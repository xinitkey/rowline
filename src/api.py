import io
import zipfile
import uuid
import asyncio
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import aiofiles

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from src import XlsxToXmlConverter, XmlFiller, any_to_pdf_async, UnsupportedFormat, split_pdf, merge_pdf
from src.gif.video_to_gif import video_to_gif
from src.media_converters.mp4_to_mp3 import mp4_to_mp3

STATIC_DIR = Path(__file__).parent.parent / "www"
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
TEMP_DIR = Path(__file__).parent.parent / "temp"

cpu_count = os.cpu_count() or 4
MAX_WORKERS = int(os.getenv('MAX_WORKERS', str(cpu_count * 8)))
MAX_CONCURRENT = int(os.getenv('MAX_CONCURRENT', str(min(cpu_count * 4, 32))))

_process_executor = None
_process_enabled = False
try:
    _process_executor = ProcessPoolExecutor(max_workers=min(cpu_count, 8))
    _process_enabled = True
except Exception:
    pass

sem = asyncio.Semaphore(MAX_CONCURRENT)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Rowline API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


async def _run_cpu(func, *args):
    if _process_enabled and _process_executor:
        return await asyncio.get_event_loop().run_in_executor(_process_executor, func, *args)
    return await asyncio.to_thread(func, *args)


async def _save(content: bytes, path: Path):
    async with aiofiles.open(path, 'wb') as f:
        await f.write(content)


def _safe_name(name: str, fallback: str) -> str:
    safe = "".join(c for c in name if ord(c) < 128)
    return safe or fallback


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/convert")
async def convert_xlsx(
    file: UploadFile = File(...),
    mode: str = Form("fill"),
    template: str = Form(None),
    sheet_name: str = Form(None),
    code_col: int = Form(6),
    data_start: int = Form(7),
    data_end: int = Form(12),
    start_row: int = Form(9),
):
    if not file.filename.lower().endswith('.xlsx'):
        raise HTTPException(400, "Expected .xlsx file")

    async with sem:
        rid = str(uuid.uuid4())
        work = TEMP_DIR / rid
        work.mkdir()
        try:
            src = work / file.filename
            await _save(await file.read(), src)

            out_dir = work / "out"
            out_dir.mkdir()

            if mode == "fill":
                tpl_path = TEMPLATES_DIR / template
                if not template or not tpl_path.exists():
                    raise HTTPException(400, "Valid template required for fill mode")
                filler = XmlFiller(tpl_path)
                if sheet_name:
                    out = out_dir / f"{src.stem}_{sheet_name}.xml"
                    filler.fill_from_xlsx(src, out, sheet_name, code_col, data_start, data_end, start_row)
                    files = [out]
                else:
                    files = filler.fill_all_sheets(src, out_dir, code_col, data_start, data_end, start_row)
            elif mode == "convert":
                conv = XlsxToXmlConverter()
                if sheet_name:
                    out = out_dir / f"{src.stem}_{sheet_name}.xml"
                    conv.convert(src, out, sheet_name, start_row=start_row)
                    files = [out]
                else:
                    files = conv.convert_all_sheets(src, out_dir, start_row=start_row, separate_files=True)
            else:
                raise HTTPException(400, f"Unknown mode: {mode}")

            if not files:
                raise HTTPException(500, "No output files generated")

            if len(files) == 1:
                return FileResponse(files[0], filename=_safe_name(files[0].name, "result.xml"), media_type="application/xml")

            buf = io.BytesIO()
            with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
                for f in files:
                    zf.write(f, f.name)
            buf.seek(0)
            return Response(content=buf.read(), media_type="application/zip",
                            headers={"Content-Disposition": f'attachment; filename="{src.stem}_files.zip"'})
        finally:
            import shutil
            shutil.rmtree(work, ignore_errors=True)


@app.post("/api/convert-to-pdf")
async def convert_to_pdf(file: UploadFile = File(...)):
    async with sem:
        rid = str(uuid.uuid4())
        work = TEMP_DIR / rid
        work.mkdir()
        try:
            src = work / file.filename
            content = await file.read()
            if len(content) > 500 * 1024 * 1024:
                raise HTTPException(413, "File too large (max 500MB)")
            await _save(content, src)

            out = work / f"{src.stem}.pdf"
            await asyncio.wait_for(any_to_pdf_async(str(src), str(out)), timeout=1800)

            if not out.exists():
                raise HTTPException(500, "PDF generation failed")
            return FileResponse(out, filename=_safe_name(out.name, "converted.pdf"), media_type="application/pdf")
        finally:
            import shutil
            shutil.rmtree(work, ignore_errors=True)


@app.post("/api/split-pdf")
async def split_pdf_endpoint(file: UploadFile = File(...), pages: str = Form("")):
    async with sem:
        rid = str(uuid.uuid4())
        work = TEMP_DIR / rid
        work.mkdir()
        try:
            src = work / file.filename
            content = await file.read()
            if len(content) > 500 * 1024 * 1024:
                raise HTTPException(413, "File too large (max 500MB)")
            await _save(content, src)

            page_list = None
            if pages.strip():
                nums = set()
                for part in pages.split(","):
                    part = part.strip()
                    if "-" in part:
                        a, b = part.split("-", 1)
                        nums.update(range(int(a.strip()), int(b.strip()) + 1))
                    else:
                        nums.add(int(part))
                page_list = sorted(nums)

            output_files = await _run_cpu(split_pdf, str(src), str(work), page_list)
            if not output_files:
                raise HTTPException(500, "No output files generated")

            if len(output_files) == 1:
                return FileResponse(output_files[0], filename=_safe_name(Path(output_files[0]).name, "split.pdf"), media_type="application/pdf")

            buf = io.BytesIO()
            with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
                for f in output_files:
                    zf.write(f, Path(f).name)
            buf.seek(0)
            return Response(content=buf.read(), media_type="application/zip",
                            headers={"Content-Disposition": f'attachment; filename="{Path(src).stem}_split.zip"'})
        finally:
            import shutil
            shutil.rmtree(work, ignore_errors=True)


@app.post("/api/merge-pdf")
async def merge_pdf_endpoint(files: list[UploadFile] = File(...)):
    if len(files) < 2:
        raise HTTPException(400, "At least 2 PDF files required")
    if len(files) > 25:
        raise HTTPException(400, "Maximum 25 files allowed")

    async with sem:
        rid = str(uuid.uuid4())
        work = TEMP_DIR / rid
        work.mkdir()
        try:
            paths = []
            for i, f in enumerate(files):
                content = await f.read()
                if len(content) > 500 * 1024 * 1024:
                    raise HTTPException(413, f"{f.filename} too large (max 500MB)")
                p = work / f"{i}_{f.filename}"
                await _save(content, p)
                paths.append(str(p))

            out = work / "merged.pdf"
            await _run_cpu(merge_pdf, paths, str(out))
            if not out.exists():
                raise HTTPException(500, "Merge failed")
            return FileResponse(out, filename="merged.pdf", media_type="application/pdf")
        finally:
            import shutil
            shutil.rmtree(work, ignore_errors=True)


@app.post("/api/video-to-gif")
async def convert_video_to_gif(
    file: UploadFile = File(...),
    start: float = Form(None),
    end: float = Form(None),
    fps: int = Form(None),
    width: int = Form(None),
):
    async with sem:
        rid = str(uuid.uuid4())
        work = TEMP_DIR / rid
        work.mkdir()
        try:
            src = work / file.filename
            content = await file.read()
            if len(content) > 500 * 1024 * 1024:
                raise HTTPException(413, "File too large (max 500MB)")
            await _save(content, src)
            out = work / f"{src.stem}.gif"
            await _run_cpu(video_to_gif, str(src), str(out), start, end, fps, width)
            if not out.exists():
                raise HTTPException(500, "GIF generation failed")
            return FileResponse(out, filename=_safe_name(out.name, "converted.gif"), media_type="image/gif")
        finally:
            import shutil
            shutil.rmtree(work, ignore_errors=True)


@app.post("/api/mp4-to-mp3")
async def convert_mp4_to_mp3(file: UploadFile = File(...)):
    async with sem:
        rid = str(uuid.uuid4())
        work = TEMP_DIR / rid
        work.mkdir()
        try:
            src = work / file.filename
            content = await file.read()
            if len(content) > 500 * 1024 * 1024:
                raise HTTPException(413, "File too large (max 500MB)")
            await _save(content, src)
            out = work / f"{src.stem}.mp3"
            await _run_cpu(mp4_to_mp3, str(src), str(out))
            if not out.exists():
                raise HTTPException(500, "MP3 extraction failed")
            return FileResponse(out, filename=_safe_name(out.name, "audio.mp3"), media_type="audio/mpeg")
        finally:
            import shutil
            shutil.rmtree(work, ignore_errors=True)


if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
