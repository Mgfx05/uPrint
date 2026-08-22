from fastapi import APIRouter, HTTPException
from pathlib import Path
from pypdf import PdfReader

from services.pricing import calculate_price

router = APIRouter()

UPLOAD_DIR = Path("uploads")


@router.get("/calculate-pdf-price")
def calculate_pdf_price(
    file_id: str,
    copies: int = 1,
    print_type: str = "bw",
    paper_size: str = "a4",
    sides: str = "single",
    orientation: str = "portrait"
):
    # Find uploaded PDF
    file_path = UPLOAD_DIR / f"{file_id}.pdf"

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="PDF not found"
        )

    # Read PDF
    pdf = PdfReader(file_path)

    # Automatically get page count
    pages = len(pdf.pages)

    # Calculate price
    result = calculate_price(
        pages=pages,
        copies=copies,
        print_type=print_type,
        paper_size=paper_size
    )

    return {
        "file_id": file_id,
        "filename": file_path.name,
        **result
    }