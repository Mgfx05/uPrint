from fastapi import APIRouter, HTTPException
from pypdf import PdfReader
import uuid

from services.pricing import calculate_price
from services.storage import pdf_storage

router = APIRouter()


@router.get("/calculate-pdf-price")
def calculate_pdf_price(
    file_id: str,
    copies: int = 1,
    print_type: str = "bw",
    paper_size: str = "a4",
    sides: str = "single",
    orientation: str = "portrait",
):
    try:
        safe_file_id = str(uuid.UUID(file_id))
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(status_code=404, detail="PDF not found")

    if not 1 <= copies <= 50:
        raise HTTPException(status_code=400, detail="Copies must be between 1 and 50")
    if print_type not in {"bw", "color"}:
        raise HTTPException(status_code=400, detail="Invalid print type")
    if paper_size not in {"a4", "a3"}:
        raise HTTPException(status_code=400, detail="Invalid paper size")
    if sides not in {"single", "double"}:
        raise HTTPException(status_code=400, detail="Invalid sides option")
    if orientation not in {"portrait", "landscape"}:
        raise HTTPException(status_code=400, detail="Invalid orientation")

    try:
        file_path = pdf_storage.materialize(safe_file_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="PDF not found")

    try:
        pages = len(PdfReader(file_path).pages)
        result = calculate_price(
            pages=pages,
            copies=copies,
            print_type=print_type,
            paper_size=paper_size,
        )
        return {
            "file_id": safe_file_id,
            "filename": f"{safe_file_id}.pdf",
            **result,
        }
    except Exception as error:
        raise HTTPException(status_code=400, detail="Could not read stored PDF") from error
    finally:
        # Local files are persistent; any alternate temporary materialization
        # must be cleaned up after pricing.
        from config import UPLOAD_DIR
        if file_path.parent != UPLOAD_DIR:
            file_path.unlink(missing_ok=True)
