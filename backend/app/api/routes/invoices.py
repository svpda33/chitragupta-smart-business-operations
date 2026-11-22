from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_business
from app.database.session import get_db
from app.models.business import Business
from app.schemas.common import Page
from app.schemas.invoice import InvoiceIn, InvoiceListItem, InvoiceOut
from app.services import invoice_service

router = APIRouter(prefix="/invoices", tags=["invoices"])

InvoiceStatusFilter = Literal["draft", "pending", "partially_paid", "overdue", "paid"]


@router.get("", response_model=Page[InvoiceListItem])
def list_invoices(
    search: str | None = Query(default=None, max_length=120),
    status: InvoiceStatusFilter | None = None,
    customer_id: int | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    biz: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
) -> dict:
    items, total = invoice_service.list_invoices(
        db,
        search=search,
        status=status,
        customer_id=customer_id,
        page=page,
        page_size=page_size,
        today=date.today(),
        business_id=biz.id,
    )
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("", response_model=InvoiceOut, status_code=201)
def create_invoice(
    data: InvoiceIn,
    biz: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
) -> dict:
    return invoice_service.create_invoice(db, data, today=date.today(), business_id=biz.id)


@router.get("/{invoice_id}", response_model=InvoiceOut)
def get_invoice(
    invoice_id: int,
    biz: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
) -> dict:
    return invoice_service.get_invoice_detail(db, invoice_id, today=date.today(), business_id=biz.id)


@router.put("/{invoice_id}", response_model=InvoiceOut)
def update_invoice(
    invoice_id: int,
    data: InvoiceIn,
    biz: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
) -> dict:
    return invoice_service.update_invoice(db, invoice_id, data, today=date.today(), business_id=biz.id)


@router.post("/{invoice_id}/send", response_model=InvoiceOut)
def send_invoice(
    invoice_id: int,
    biz: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
) -> dict:
    return invoice_service.send_invoice(db, invoice_id, today=date.today(), business_id=biz.id)


@router.delete("/{invoice_id}", status_code=204, response_class=Response)
def delete_invoice(
    invoice_id: int,
    biz: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
) -> Response:
    invoice_service.delete_invoice(db, invoice_id, business_id=biz.id)
    return Response(status_code=204)
