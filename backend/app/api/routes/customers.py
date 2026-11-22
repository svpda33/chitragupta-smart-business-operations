from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_business
from app.database.session import get_db
from app.models.business import Business
from app.schemas.common import Page
from app.schemas.customer import CustomerIn, CustomerOut
from app.services import customer_service

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", response_model=Page[CustomerOut])
def list_customers(
    search: str | None = Query(default=None, max_length=120),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    biz: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
) -> dict:
    items, total = customer_service.list_customers(
        db, search=search, page=page, page_size=page_size, business_id=biz.id
    )
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("", response_model=CustomerOut, status_code=201)
def create_customer(
    data: CustomerIn,
    biz: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
) -> dict:
    return customer_service.create_customer(db, data, business_id=biz.id)


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(
    customer_id: int,
    biz: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
) -> dict:
    return customer_service.get_customer(db, customer_id, business_id=biz.id)


@router.put("/{customer_id}", response_model=CustomerOut)
def update_customer(
    customer_id: int,
    data: CustomerIn,
    biz: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
) -> dict:
    return customer_service.update_customer(db, customer_id, data, business_id=biz.id)


@router.delete("/{customer_id}", status_code=204, response_class=Response)
def delete_customer(
    customer_id: int,
    biz: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
) -> Response:
    customer_service.delete_customer(db, customer_id, business_id=biz.id)
    return Response(status_code=204)
