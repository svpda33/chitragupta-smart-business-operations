"""Product/service catalogue and transactional inventory stock ledger service."""

from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.business import Business
from app.models.inventory_movement import InventoryMovement
from app.models.invoice import Invoice
from app.models.product import Product
from app.schemas.product import ProductIn, StockAdjustIn
from app.utils.dates import now_utc


def derive_stock_status(product: Product) -> str:
    if product.item_type == "service":
        return "service"
    if product.stock_quantity <= 0:
        return "out_of_stock"
    if product.stock_quantity <= product.min_stock_threshold:
        return "low_stock"
    return "in_stock"


def serialize_product(p: Product) -> dict[str, Any]:
    return {
        "id": p.id,
        "business_id": p.business_id,
        "item_type": p.item_type,
        "name": p.name,
        "description": p.description,
        "sku": p.sku,
        "category": p.category,
        "image_url": p.image_url,
        "selling_price_paise": p.selling_price_paise,
        "cost_price_paise": p.cost_price_paise,
        "tax_percent": p.tax_percent,
        "unit": p.unit,
        "stock_quantity": p.stock_quantity,
        "min_stock_threshold": p.min_stock_threshold,
        "stock_status": derive_stock_status(p),
        "is_active": p.is_active,
        "created_at": p.created_at,
        "updated_at": p.updated_at,
    }


def list_products(
    db: Session,
    business_id: int,
    search: str | None = None,
    category: str | None = None,
    item_type: str | None = None,
    stock_filter: str | None = None,
    include_inactive: bool = False,
) -> list[dict[str, Any]]:
    stmt = select(Product).where(Product.business_id == business_id)
    if not include_inactive:
        stmt = stmt.where(Product.is_active == True)  # noqa: E712
    if item_type in ("product", "service"):
        stmt = stmt.where(Product.item_type == item_type)
    if category and category.strip():
        stmt = stmt.where(Product.category == category.strip())
    if search and search.strip():
        term = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                Product.name.ilike(term),
                Product.sku.ilike(term),
                Product.description.ilike(term),
                Product.category.ilike(term),
            )
        )
    stmt = stmt.order_by(Product.is_active.desc(), Product.name.asc())
    products = list(db.scalars(stmt).all())
    serialized = [serialize_product(p) for p in products]

    if stock_filter in ("in_stock", "low_stock", "out_of_stock", "service"):
        serialized = [p for p in serialized if p["stock_status"] == stock_filter]
    return serialized


def get_product_entity(db: Session, business_id: int, product_id: int) -> Product:
    p = db.scalar(
        select(Product).where(Product.id == product_id, Product.business_id == business_id).limit(1)
    )
    if p is None:
        raise AppError(404, "Product or service not found.")
    return p


def create_product(db: Session, business_id: int, data: ProductIn) -> dict[str, Any]:
    try:
        selling_paise = data.selling_price_paise()
        cost_paise = data.cost_price_paise()
    except ValueError as exc:
        raise AppError(422, str(exc), field="selling_price") from exc

    if data.sku:
        dup = db.scalar(
            select(Product.id)
            .where(Product.business_id == business_id, Product.sku == data.sku)
            .limit(1)
        )
        if dup is not None:
            raise AppError(409, "A product or service with this SKU already exists.", field="sku")

    initial_stock = data.stock_quantity if data.item_type == "product" else 0
    product = Product(
        business_id=business_id,
        item_type=data.item_type,
        name=data.name,
        description=data.description,
        sku=data.sku,
        category=data.category or "General",
        selling_price_paise=selling_paise,
        cost_price_paise=cost_paise,
        tax_percent=data.tax_percent,
        unit=data.unit,
        stock_quantity=initial_stock,
        min_stock_threshold=data.min_stock_threshold if data.item_type == "product" else 0,
        is_active=data.is_active,
    )
    db.add(product)
    db.flush()

    if data.item_type == "product" and initial_stock > 0:
        db.add(
            InventoryMovement(
                business_id=business_id,
                product_id=product.id,
                quantity_change=initial_stock,
                balance_after=initial_stock,
                movement_type="initial",
                reason="Initial opening stock",
                created_at=now_utc(),
            )
        )

    db.commit()
    db.refresh(product)
    return serialize_product(product)


def update_product(db: Session, business_id: int, product_id: int, data: ProductIn) -> dict[str, Any]:
    product = get_product_entity(db, business_id, product_id)
    try:
        selling_paise = data.selling_price_paise()
        cost_paise = data.cost_price_paise()
    except ValueError as exc:
        raise AppError(422, str(exc), field="selling_price") from exc

    if data.sku:
        dup = db.scalar(
            select(Product.id)
            .where(
                Product.business_id == business_id,
                Product.sku == data.sku,
                Product.id != product_id,
            )
            .limit(1)
        )
        if dup is not None:
            raise AppError(409, "A product or service with this SKU already exists.", field="sku")

    product.item_type = data.item_type
    product.name = data.name
    product.description = data.description
    product.sku = data.sku
    product.category = data.category or "General"
    product.selling_price_paise = selling_paise
    product.cost_price_paise = cost_paise
    product.tax_percent = data.tax_percent
    product.unit = data.unit
    product.min_stock_threshold = data.min_stock_threshold if data.item_type == "product" else 0
    product.is_active = data.is_active

    # Do not silently overwrite stock_quantity on edit; use Stock Adjustment for auditable changes
    db.commit()
    db.refresh(product)
    return serialize_product(product)


def archive_product(db: Session, business_id: int, product_id: int) -> dict[str, Any]:
    product = get_product_entity(db, business_id, product_id)
    product.is_active = not product.is_active
    db.commit()
    db.refresh(product)
    return serialize_product(product)


def adjust_stock(
    db: Session,
    business: Business,
    product_id: int,
    data: StockAdjustIn,
) -> dict[str, Any]:
    product = get_product_entity(db, business.id, product_id)
    if product.item_type != "product":
        raise AppError(422, "Stock tracking applies only to physical products, not services.")
    if data.quantity_change == 0:
        raise AppError(422, "Quantity change cannot be zero.", field="quantity_change")

    new_balance = product.stock_quantity + data.quantity_change
    if new_balance < 0 and not business.allow_negative_stock:
        raise AppError(
            422,
            f"Insufficient stock for {product.name}. Available: {product.stock_quantity} {product.unit}.",
            field="quantity_change",
        )

    product.stock_quantity = new_balance
    movement = InventoryMovement(
        business_id=business.id,
        product_id=product.id,
        quantity_change=data.quantity_change,
        balance_after=new_balance,
        movement_type=data.movement_type,
        reason=data.reason,
        reference=data.reference,
        created_at=now_utc(),
    )
    db.add(movement)
    db.commit()
    db.refresh(movement)
    return {
        "id": movement.id,
        "product_id": product.id,
        "product_name": product.name,
        "sku": product.sku,
        "quantity_change": movement.quantity_change,
        "balance_after": movement.balance_after,
        "movement_type": movement.movement_type,
        "reason": movement.reason,
        "reference": movement.reference,
        "invoice_id": movement.invoice_id,
        "created_at": movement.created_at,
    }


def deduct_stock_for_sent_invoice(db: Session, business_id: int | None, invoice: Invoice) -> None:
    """Deduct stock once when an invoice is sent. Idempotent & service-safe."""
    if not business_id:
        return
    biz = db.get(Business, business_id)
    allow_neg = bool(biz and biz.allow_negative_stock)

    # Guard against duplicate deductions for the same invoice
    already_deducted = db.scalar(
        select(InventoryMovement.id)
        .where(
            InventoryMovement.invoice_id == invoice.id,
            InventoryMovement.movement_type == "sale",
        )
        .limit(1)
    )
    if already_deducted is not None:
        return

    for item in invoice.items:
        if not item.product_id:
            continue
        product = db.scalar(
            select(Product)
            .where(Product.id == item.product_id, Product.business_id == business_id)
            .limit(1)
        )
        if product is None or product.item_type != "product":
            continue

        new_balance = product.stock_quantity - item.quantity
        if new_balance < 0 and not allow_neg:
            raise AppError(
                422,
                f"Insufficient stock to send invoice: '{product.name}' has {product.stock_quantity} {product.unit} available, but {item.quantity} requested.",
            )
        product.stock_quantity = new_balance
        db.add(
            InventoryMovement(
                business_id=business_id,
                product_id=product.id,
                quantity_change=-item.quantity,
                balance_after=new_balance,
                movement_type="sale",
                reason=f"Sold via invoice {invoice.invoice_number}",
                reference=invoice.invoice_number,
                invoice_id=invoice.id,
                created_at=now_utc(),
            )
        )


def list_movements(
    db: Session,
    business_id: int,
    product_id: int | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    stmt = (
        select(InventoryMovement, Product.name.label("product_name"), Product.sku.label("sku"))
        .join(Product, InventoryMovement.product_id == Product.id)
        .where(InventoryMovement.business_id == business_id)
    )
    if product_id is not None:
        stmt = stmt.where(InventoryMovement.product_id == product_id)
    stmt = stmt.order_by(InventoryMovement.created_at.desc(), InventoryMovement.id.desc()).limit(limit)

    rows = db.execute(stmt).all()
    return [
        {
            "id": r.InventoryMovement.id,
            "product_id": r.InventoryMovement.product_id,
            "product_name": r.product_name,
            "sku": r.sku,
            "quantity_change": r.InventoryMovement.quantity_change,
            "balance_after": r.InventoryMovement.balance_after,
            "movement_type": r.InventoryMovement.movement_type,
            "reason": r.InventoryMovement.reason,
            "reference": r.InventoryMovement.reference,
            "invoice_id": r.InventoryMovement.invoice_id,
            "created_at": r.InventoryMovement.created_at,
        }
        for r in rows
    ]


def get_inventory_summary(db: Session, business_id: int) -> dict[str, Any]:
    all_active = list(
        db.scalars(
            select(Product).where(Product.business_id == business_id, Product.is_active == True)  # noqa: E712
        ).all()
    )
    products = [p for p in all_active if p.item_type == "product"]
    services = [p for p in all_active if p.item_type == "service"]

    total_units = sum(max(0, p.stock_quantity) for p in products)
    low_stock = [p for p in products if 0 < p.stock_quantity <= p.min_stock_threshold]
    out_of_stock = [p for p in products if p.stock_quantity <= 0]

    valuation_paise = 0
    valued_count = 0
    for p in products:
        if p.cost_price_paise is not None and p.stock_quantity > 0:
            valuation_paise += p.cost_price_paise * p.stock_quantity
            valued_count += 1

    alert_items = sorted(out_of_stock + low_stock, key=lambda x: x.stock_quantity)

    return {
        "total_active_products": len(products),
        "total_active_services": len(services),
        "total_stock_units": total_units,
        "low_stock_count": len(low_stock),
        "out_of_stock_count": len(out_of_stock),
        "inventory_valuation_paise": valuation_paise,
        "valued_products_count": valued_count,
        "low_stock_items": [serialize_product(p) for p in alert_items[:12]],
        "recent_movements": list_movements(db, business_id, limit=25),
    }
