from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
import uuid

from config import UPLOAD_DIR
from models.database import SessionLocal
from models.order import Order
from pypdf import PdfReader
from fastapi import Depends
from security import require_print_device


router = APIRouter()

# ============================================================
# CREATE ORDER
# ============================================================

@router.post("/create-order")
def create_order(
    file_id: str,
    copies: int = 1,
    print_type: str = "bw",
    paper_size: str = "a4",
    sides: str = "single",
    orientation: str = "portrait"
):
    file_path = UPLOAD_DIR / f"{file_id}.pdf"

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="PDF not found"
        )

    pdf = PdfReader(file_path)
    pages = len(pdf.pages)

    price_per_page = 10 if print_type == "color" else 2
    if paper_size == "a3":
        price_per_page *= 2
    total_price = pages * copies * price_per_page

    order_id = "ERB-" + str(uuid.uuid4())[:8].upper()

    db: Session = SessionLocal()

    try:
        order = Order(
            order_id=order_id,
            file_id=file_id,
            pages=pages,
            copies=copies,
            print_type=print_type,
            paper_size=paper_size,
            sides=sides,
            orientation=orientation,
            amount=total_price,
            payment_status="pending",
            print_status="queued"
        )

        db.add(order)
        db.commit()
        db.refresh(order)

        return {
            "message": "Order created successfully",
            "order_id": order.order_id,
            "file_id": order.file_id,
            "pages": order.pages,
            "copies": order.copies,
            "print_type": order.print_type,
            "paper_size": order.paper_size,
            "sides": order.sides,
            "orientation": order.orientation,
            "amount": order.amount,
            "payment_status": order.payment_status,
            "print_status": order.print_status
        }

    finally:
        db.close()


# ============================================================
# GET ORDER DETAILS
# ============================================================

@router.get("/order/{order_id}")
def get_order(order_id: str):

    db: Session = SessionLocal()

    try:
        order = db.query(Order).filter(
            Order.order_id == order_id
        ).first()

        if not order:
            raise HTTPException(
                status_code=404,
                detail="Order not found"
            )

        return {
            "message": "Order found",
            "order_id": order.order_id,
            "file_id": order.file_id,
            "pages": order.pages,
            "copies": order.copies,
            "print_type": order.print_type,
            "paper_size": order.paper_size,
            "sides": order.sides,
            "orientation": order.orientation,
            "amount": order.amount,
            "payment_status": order.payment_status,
            "print_status": order.print_status
        }

    finally:
        db.close()


# ============================================================
# ADD ORDER TO PRINT QUEUE
# ============================================================

@router.post("/order/{order_id}/queue")
def queue_order(order_id: str):

    db: Session = SessionLocal()

    try:
        order = db.query(Order).filter(
            Order.order_id == order_id
        ).first()

        if not order:
            raise HTTPException(
                status_code=404,
                detail="Order not found"
            )

        if order.print_status != "pending":
            raise HTTPException(
                status_code=400,
                detail=f"Order cannot be queued. Current status: {order.print_status}"
            )

        order.print_status = "queued"

        db.commit()
        db.refresh(order)

        return {
            "message": "Order added to print queue",
            "order_id": order.order_id,
            "print_status": order.print_status
        }

    finally:
        db.close()


# ============================================================
# GET PRINT QUEUE
# ============================================================

@router.get("/print-queue")
def get_print_queue(_: None = Depends(require_print_device)):

    db: Session = SessionLocal()

    try:
        orders = db.query(Order).filter(
            Order.print_status == "queued"
        ).all()

        jobs = []

        for order in orders:
            jobs.append({
                "order_id": order.order_id,
                "file_id": order.file_id,
                "pages": order.pages,
                "copies": order.copies,
                "print_type": order.print_type,
                "paper_size": order.paper_size,
                "sides": order.sides,
                "orientation": order.orientation,
                "amount": order.amount
            })

        return {
            "queue_count": len(jobs),
            "jobs": jobs
        }

    finally:
        db.close()


# ============================================================
# GET NEXT PRINT JOB
# ============================================================

@router.get("/print-queue/next")
def get_next_print_job(_: None = Depends(require_print_device)):

    db: Session = SessionLocal()

    try:
        # Find the oldest queued job, then atomically transition it to
        # claimed. The conditional UPDATE ensures only one worker wins.
        order = db.query(Order).filter(
            Order.print_status == "queued"
        ).order_by(
            Order.id.asc()
        ).first()

        if not order:
            return {
                "message": "No print jobs available",
                "job": None
            }

        claimed = db.query(Order).filter(
            Order.id == order.id,
            Order.print_status == "queued"
        ).update(
            {Order.print_status: "claimed"},
            synchronize_session=False
        )
        db.commit()

        if claimed != 1:
            return {
                "message": "No print jobs available",
                "job": None
            }

        db.refresh(order)
        return {
            "message": "Print job claimed",
            "job": {
                "order_id": order.order_id,
                "file_id": order.file_id,
                "pages": order.pages,
                "copies": order.copies,
                "print_type": order.print_type,
                "paper_size": order.paper_size,
                "sides": order.sides,
                "orientation": order.orientation,
                "amount": order.amount
            }
        }

    finally:
        db.close()


# ============================================================
# START PRINTING
# ============================================================

@router.post("/order/{order_id}/start-printing")
def start_printing(order_id: str, _: None = Depends(require_print_device)):

    db: Session = SessionLocal()

    try:
        order = db.query(Order).filter(
            Order.order_id == order_id
        ).first()

        if not order:
            raise HTTPException(
                status_code=404,
                detail="Order not found"
            )

        if order.print_status not in {"queued", "claimed"}:
            raise HTTPException(
                status_code=400,
                detail=f"Order cannot start printing. Current status: {order.print_status}"
            )

        order.print_status = "printing"

        db.commit()
        db.refresh(order)

        return {
            "message": "Printing started",
            "order_id": order.order_id,
            "print_status": order.print_status
        }

    finally:
        db.close()


# ============================================================
# COMPLETE PRINTING
# ============================================================

@router.post("/order/{order_id}/complete-printing")
def complete_printing(order_id: str, _: None = Depends(require_print_device)):

    db: Session = SessionLocal()

    try:
        order = db.query(Order).filter(
            Order.order_id == order_id
        ).first()

        if not order:
            raise HTTPException(
                status_code=404,
                detail="Order not found"
            )

        if order.print_status != "printing":
            raise HTTPException(
                status_code=400,
                detail=f"Order cannot be completed. Current status: {order.print_status}"
            )

        order.print_status = "completed"

        db.commit()
        db.refresh(order)

        return {
            "message": "Printing completed",
            "order_id": order.order_id,
            "print_status": order.print_status
        }

    finally:
        db.close()
        
        
# ============================================================
# PRINTING FAILED
# ============================================================

@router.post("/order/{order_id}/fail-printing")
def fail_printing(
    order_id: str,
    reason: str = "Unknown printing error",
    _: None = Depends(require_print_device),
):

    db: Session = SessionLocal()

    try:
        # Find order
        order = db.query(Order).filter(
            Order.order_id == order_id
        ).first()

        if not order:
            raise HTTPException(
                status_code=404,
                detail="Order not found"
            )

        # Only printing orders can be marked as failed
        if order.print_status not in {"claimed", "printing"}:
            raise HTTPException(
                status_code=400,
                detail=f"Order cannot be marked as failed. Current status: {order.print_status}"
            )

        # Change status
        order.print_status = "failed"

        db.commit()
        db.refresh(order)

        return {
            "message": "Printing failed",
            "order_id": order.order_id,
            "print_status": order.print_status,
            "reason": reason
        }

    finally:
        db.close()