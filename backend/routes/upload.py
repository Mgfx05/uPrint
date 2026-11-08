from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from pathlib import Path
from tempfile import NamedTemporaryFile
from starlette.background import BackgroundTask
from pypdf import PdfReader
from pypdf.errors import PdfReadError
import uuid

from config import MAX_UPLOAD_BYTES, UPLOAD_DIR
from services.storage import pdf_storage
from security import require_print_device

router = APIRouter()
UPLOAD_STAGING_DIR = UPLOAD_DIR / ".staging"
UPLOAD_STAGING_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    file_id = str(uuid.uuid4())
    file_path = UPLOAD_STAGING_DIR / f"{file_id}.pdf"
    total_bytes = 0
    header = b""

    try:
        with file_path.open("wb") as destination:
            while chunk := await file.read(1024 * 1024):
                total_bytes += len(chunk)
                if total_bytes > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail=f"PDF exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB upload limit",
                    )
                if len(header) < 5:
                    header += chunk[: 5 - len(header)]
                destination.write(chunk)

        if not header.startswith(b"%PDF-"):
            raise HTTPException(status_code=400, detail="Uploaded file is not a valid PDF")

        pdf = PdfReader(str(file_path), strict=True)
        page_count = len(pdf.pages)
        if page_count < 1:
            raise HTTPException(status_code=400, detail="PDF contains no pages")

        pdf_storage.save_file(file_id, file_path)

        return {
            "message": "PDF uploaded successfully",
            "file_id": file_id,
            "filename": Path(file.filename or "document.pdf").name,
            "pages": page_count,
            "file_size_bytes": total_bytes,
        }

    except HTTPException:
        if file_path.exists():
            file_path.unlink()
        raise
    except (PdfReadError, ValueError, OSError) as error:
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=400, detail="Could not read the uploaded PDF") from error
    except Exception as error:
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail="Could not process PDF") from error
    finally:
        file_path.unlink(missing_ok=True)
        await file.close()


@router.get("/download-pdf/{file_id}")
def download_pdf(file_id: str, _: None = Depends(require_print_device)):
    try:
        safe_file_id = str(uuid.UUID(file_id))
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(status_code=404, detail="PDF not found")

    try:
        file_path = pdf_storage.materialize(safe_file_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="PDF not found")

    background = BackgroundTask(file_path.unlink, missing_ok=True) if file_path.parent != UPLOAD_DIR else None
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=f"{safe_file_id}.pdf",
        background=background,
    )
