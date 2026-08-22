from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import shutil
import uuid
from pypdf import PdfReader


router = APIRouter()


# ============================================================
# UPLOAD DIRECTORY
# ============================================================

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


# ============================================================
# UPLOAD PDF
# ============================================================

@router.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):

    # Check file type
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )

    # Generate unique file ID
    file_id = str(uuid.uuid4())

    # Create file path
    file_path = UPLOAD_DIR / f"{file_id}.pdf"

    try:

        # Save uploaded PDF
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Read PDF
        pdf = PdfReader(file_path)

        # Count pages
        page_count = len(pdf.pages)

        # Get file size
        file_size = file_path.stat().st_size

        return {
            "message": "PDF uploaded successfully",
            "file_id": file_id,
            "filename": file.filename,
            "pages": page_count,
            "file_size_bytes": file_size
        }

    except Exception as e:

        # Delete incomplete file if something goes wrong
        if file_path.exists():
            file_path.unlink()

        raise HTTPException(
            status_code=500,
            detail=f"Could not process PDF: {str(e)}"
        )

    finally:
        file.file.close()


# ============================================================
# DOWNLOAD PDF
# ============================================================

@router.get("/download-pdf/{file_id}")
def download_pdf(file_id: str):

    # Find PDF
    file_path = UPLOAD_DIR / f"{file_id}.pdf"

    # PDF doesn't exist
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="PDF not found"
        )

    # Send PDF to requester
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=f"{file_id}.pdf"
    )