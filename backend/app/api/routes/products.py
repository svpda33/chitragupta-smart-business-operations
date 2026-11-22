from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_business
from app.database.session import get_db
from app.models.business import Business
from app.schemas.product import (
    InventoryMovementOut,
    InventorySummaryOut,
    ProductIn,
    ProductOut,
    StockAdjustIn,
)
from app.services import inventory_service

router = APIRouter(tags=["products & inventory"])


@router.get("/products", response_model=list[ProductOut])
def list_products(
    search: str | None = Query(default=None, max_length=120),
    category: str | None = Query(default=None, max_length=80),
    item_type: str | None = Query(default=None),
    stock_filter: str | None = Query(default=None),
    include_inactive: bool = Query(default=False),
    biz: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
) -> list[dict]:
    return inventory_service.list_products(
        db,
        business_id=biz.id,
        search=search,
        category=category,
        item_type=item_type,
        stock_filter=stock_filter,
        include_inactive=include_inactive,
    )


@router.post("/products", response_model=ProductOut, status_code=201)
def create_product(
    data: ProductIn,
    biz: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
) -> dict:
    return inventory_service.create_product(db, biz.id, data)


@router.get("/products/{product_id}", response_model=ProductOut)
def get_product(
    product_id: int,
    biz: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
) -> dict:
    p = inventory_service.get_product_entity(db, biz.id, product_id)
    return inventory_service.serialize_product(p)


@router.put("/products/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    data: ProductIn,
    biz: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
) -> dict:
    return inventory_service.update_product(db, biz.id, product_id, data)


@router.post("/products/{product_id}/archive", response_model=ProductOut)
def toggle_archive_product(
    product_id: int,
    biz: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
) -> dict:
    return inventory_service.archive_product(db, biz.id, product_id)


@router.post("/products/{product_id}/stock", response_model=InventoryMovementOut, status_code=201)
def adjust_stock(
    product_id: int,
    data: StockAdjustIn,
    biz: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
) -> dict:
    return inventory_service.adjust_stock(db, biz, product_id, data)


@router.get("/products/{product_id}/movements", response_model=list[InventoryMovementOut])
def get_product_movements(
    product_id: int,
    biz: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
) -> list[dict]:
    inventory_service.get_product_entity(db, biz.id, product_id)
    return inventory_service.list_movements(db, biz.id, product_id=product_id, limit=100)


@router.get("/inventory/summary", response_model=InventorySummaryOut)
def get_inventory_summary(
    biz: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
) -> dict:
    return inventory_service.get_inventory_summary(db, biz.id)
