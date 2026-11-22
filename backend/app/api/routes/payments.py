from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_business
from app.database.session import get_db
from app.models.business import Business
from app.schemas.common import Page
from app.schemas.payment import PaymentCreate, PaymentDetail, PaymentOut, PaymentUpdate, ReverseIn
from app.services import payment_service

router = APIRouter(prefix="/payments", tags=["payments"])

PaymentStatusFilter = Literal["active", "reversed"]


@router.get("", response_model=Page[PaymentOut])
def list_payments(
    invoice_id: int | None = None,
    customer_id: int | None = None,
    status: PaymentStatusFilter | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    biz: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
) -> dict:
    items, total = payment_service.list_payments(
        db,
        invoice_id=invoice_id,
        customer_id=customer_id,
        status=status,
        page=page,
        page_size=page_size,
        business_id=biz.id,
    )
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("", response_model=PaymentDetail, status_code=201)
def record_payment(
    data: PaymentCreate,
    biz: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
) -> dict:
    return payment_service.record_payment(db, data, today=date.today(), business_id=biz.id)


@router.get("/{payment_id}", response_model=PaymentDetail)
def get_payment(
    payment_id: int,
    biz: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
) -> dict:
    return payment_service.get_payment_detail(db, payment_id, business_id=biz.id)


@router.put("/{payment_id}", response_model=PaymentDetail)
def update_payment(
    payment_id: int,
    data: PaymentUpdate,
    biz: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
) -> dict:
    return payment_service.update_payment(db, payment_id, data, today=date.today(), business_id=biz.id)


@router.post("/{payment_id}/reverse", response_model=PaymentDetail)
def reverse_payment(
    payment_id: int,
    data: ReverseIn,
    biz: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
) -> dict:
    return payment_service.reverse_payment(db, payment_id, data.reason, business_id=biz.id)
