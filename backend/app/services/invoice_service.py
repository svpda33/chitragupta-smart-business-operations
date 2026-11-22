"""Invoice rules: totals, validation, numbering, lifecycle and history.

Totals are computed in integer paise. Tax = round-half-up of subtotal * tax_percent / 100.
"""

from datetime import date

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.payment import Payment
from app.schemas.invoice import InvoiceIn, ItemIn
from app.services.audit_service import history_to_dicts, list_history, record_event
from app.services import inventory_service
from app.services.invoice_numbering import next_invoice_number
from app.services.payment_service import PAYMENT_ACTIVE, paid_totals, to_payment_out
from app.services.status import LIFECYCLE_DRAFT, LIFECYCLE_SENT, derive_invoice_status
from app.utils.dates import now_utc
from app.utils.dates import today as default_today

MIN_ITEMS = 1
MAX_ITEMS = 50
MAX_QUANTITY = 100_000
MAX_DESCRIPTION_LENGTH = 200
MAX_INVOICE_NUMBER_LENGTH = 32
MAX_TOTAL_PAISE = 1_000_000_000
TAX_PERCENT_MIN = 0
TAX_PERCENT_MAX = 100

AMOUNT_LOCKED_MESSAGE = (
    "This invoice has payments recorded. Reverse the payments before changing its amounts."
)
DUPLICATE_NUMBER_MESSAGE = "An invoice with this number already exists."


def compute_totals(lines: list[tuple[int, int]], tax_percent: int) -> tuple[int, int, int]:
    """lines: (quantity, unit_price_paise) pairs. Returns (subtotal, tax, total) in paise."""
    subtotal = sum(quantity * unit_price_paise for quantity, unit_price_paise in lines)
    tax = (subtotal * tax_percent + 50) // 100
    total = subtotal + tax
    if total > MAX_TOTAL_PAISE:
        raise AppError(422, "The invoice total is too large.", field="items")
    return subtotal, tax, total


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _validate_dates(invoice_date: date, due_date: date) -> None:
    if due_date < invoice_date:
        raise AppError(422, "Due date cannot be before the invoice date.", field="due_date")


def _validate_tax(tax_percent: int) -> None:
    if not (TAX_PERCENT_MIN <= tax_percent <= TAX_PERCENT_MAX):
        raise AppError(422, "Tax percent must be between 0 and 100.", field="tax_percent")


def _validate_lines(items: list[ItemIn]) -> list[dict]:
    if not (MIN_ITEMS <= len(items) <= MAX_ITEMS):
        raise AppError(422, "An invoice needs between 1 and 50 items.", field="items")
    prepared = []
    for item in items:
        description = item.description.strip()
        if not (1 <= len(description) <= MAX_DESCRIPTION_LENGTH):
            raise AppError(422, "Item description must be 1 to 200 characters.", field="description")
        if not (1 <= item.quantity <= MAX_QUANTITY):
            raise AppError(422, "Quantity must be between 1 and 100000.", field="quantity")
        try:
            unit_price = item.unit_price_paise()
        except ValueError as exc:
            raise AppError(422, str(exc), field="unit_price") from exc
        prepared.append(
            {
                "product_id": item.product_id,
                "description": description,
                "quantity": item.quantity,
                "unit_price_paise": unit_price,
                "line_total_paise": item.quantity * unit_price,
            }
        )
    return prepared


def _get_customer(db: Session, customer_id: int, business_id: int | None = None) -> Customer:
    stmt = select(Customer).where(Customer.id == customer_id)
    if business_id is not None:
        stmt = stmt.where(Customer.business_id == business_id)
    customer = db.scalar(stmt.limit(1))
    if customer is None:
        raise AppError(404, "Customer not found.")
    return customer


def _get_invoice(db: Session, invoice_id: int, business_id: int | None = None) -> Invoice:
    stmt = select(Invoice).where(Invoice.id == invoice_id)
    if business_id is not None:
        stmt = stmt.where(Invoice.business_id == business_id)
    invoice = db.scalar(stmt.limit(1))
    if invoice is None:
        raise AppError(404, "Invoice not found.")
    return invoice


def _resolve_number(
    db: Session,
    supplied: str | None,
    exclude_id: int | None,
    business_id: int | None = None,
) -> str:
    """Use the supplied number (checked for length and uniqueness) or generate the next one."""
    if supplied is None:
        return next_invoice_number(db)
    number = supplied.strip()
    if not (1 <= len(number) <= MAX_INVOICE_NUMBER_LENGTH):
        raise AppError(422, "Invoice number must be 1 to 32 characters.", field="invoice_number")
    stmt = select(Invoice.id).where(Invoice.invoice_number == number)
    if business_id is not None:
        stmt = stmt.where(Invoice.business_id == business_id)
    if exclude_id is not None:
        stmt = stmt.where(Invoice.id != exclude_id)
    if db.scalar(stmt.limit(1)) is not None:
        raise AppError(409, DUPLICATE_NUMBER_MESSAGE, field="invoice_number")
    return number


def _build_items(lines: list[dict]) -> list[InvoiceItem]:
    return [InvoiceItem(position=index, **line) for index, line in enumerate(lines, start=1)]


def _invoice_row_statement():
    return select(Invoice, Customer.name).join(Customer, Customer.id == Invoice.customer_id)


def _list_item(invoice: Invoice, customer_name: str, paid: int, today: date) -> dict:
    status, days_overdue = derive_invoice_status(
        invoice.lifecycle, invoice.total_paise, paid, invoice.due_date, today
    )
    return {
        "id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "customer_id": invoice.customer_id,
        "customer_name": customer_name,
        "description": invoice.description,
        "invoice_date": invoice.invoice_date,
        "due_date": invoice.due_date,
        "lifecycle": invoice.lifecycle,
        "status": status,
        "total_paise": invoice.total_paise,
        "paid_paise": paid,
        "outstanding_paise": invoice.total_paise - paid,
        "days_overdue": days_overdue,
    }


def get_invoice_detail(
    db: Session,
    invoice_id: int,
    today: date | None = None,
    business_id: int | None = None,
) -> dict:
    today = today or default_today()
    stmt = _invoice_row_statement().where(Invoice.id == invoice_id)
    if business_id is not None:
        stmt = stmt.where(Invoice.business_id == business_id)
    row = db.execute(stmt).first()
    if row is None:
        raise AppError(404, "Invoice not found.")
    invoice, customer_name = row

    paid = paid_totals(db, [invoice.id]).get(invoice.id, 0)
    payments = [to_payment_out(p, invoice.invoice_number, customer_name) for p in invoice.payments]
    pairs = [("invoice", invoice.id)] + [("payment", p.id) for p in invoice.payments]
    history = history_to_dicts(list_history(db, pairs))
    items = [
        {
            "id": item.id,
            "product_id": item.product_id,
            "position": item.position,
            "description": item.description,
            "quantity": item.quantity,
            "unit_price_paise": item.unit_price_paise,
            "line_total_paise": item.line_total_paise,
        }
        for item in invoice.items
    ]
    return {
        **_list_item(invoice, customer_name, paid, today),
        "notes": invoice.notes,
        "tax_percent": invoice.tax_percent,
        "subtotal_paise": invoice.subtotal_paise,
        "tax_paise": invoice.tax_paise,
        "sent_at": invoice.sent_at,
        "items": items,
        "payments": payments,
        "history": history,
    }


def list_invoices(
    db: Session,
    search: str | None = None,
    status: str | None = None,
    customer_id: int | None = None,
    page: int = 1,
    page_size: int = 20,
    today: date | None = None,
    business_id: int | None = None,
) -> tuple[list[dict], int]:
    today = today or default_today()
    stmt = _invoice_row_statement()
    if business_id is not None:
        stmt = stmt.where(Invoice.business_id == business_id)
    if customer_id is not None:
        stmt = stmt.where(Invoice.customer_id == customer_id)
    term = (search or "").strip()
    if term:
        pattern = f"%{term}%"
        stmt = stmt.where(
            or_(
                Invoice.invoice_number.ilike(pattern),
                Invoice.description.ilike(pattern),
                Customer.name.ilike(pattern),
            )
        )
    rows = db.execute(stmt.order_by(Invoice.invoice_date.desc(), Invoice.id.desc())).all()
    paid_map = paid_totals(db, [invoice.id for invoice, _ in rows])

    filtered = []
    for invoice, customer_name in rows:
        item = _list_item(invoice, customer_name, paid_map.get(invoice.id, 0), today)
        if status is None or item["status"] == status:
            filtered.append(item)

    start = (page - 1) * page_size
    return filtered[start : start + page_size], len(filtered)


def create_invoice(
    db: Session,
    data: InvoiceIn,
    today: date | None = None,
    business_id: int | None = None,
) -> dict:
    _get_customer(db, data.customer_id, business_id=business_id)
    _validate_dates(data.invoice_date, data.due_date)
    _validate_tax(data.tax_percent)
    lines = _validate_lines(data.items)
    subtotal, tax, total = compute_totals(
        [(line["quantity"], line["unit_price_paise"]) for line in lines],
        data.tax_percent,
    )
    number = _resolve_number(db, data.invoice_number, exclude_id=None, business_id=business_id)

    now = now_utc()
    invoice = Invoice(
        business_id=business_id,
        invoice_number=number,
        customer_id=data.customer_id,
        description=data.description.strip(),
        invoice_date=data.invoice_date,
        due_date=data.due_date,
        tax_percent=data.tax_percent,
        subtotal_paise=subtotal,
        tax_paise=tax,
        total_paise=total,
        lifecycle=LIFECYCLE_DRAFT,
        notes=_clean_text(data.notes),
        created_at=now,
        updated_at=now,
    )
    invoice.items = _build_items(lines)
    db.add(invoice)
    db.flush()
    record_event(db, "invoice", invoice.id, "created", f"Invoice {number} created", now)
    db.commit()
    return get_invoice_detail(db, invoice.id, today, business_id=business_id)


def update_invoice(
    db: Session,
    invoice_id: int,
    data: InvoiceIn,
    today: date | None = None,
    business_id: int | None = None,
) -> dict:
    invoice = _get_invoice(db, invoice_id, business_id=business_id)
    customer = _get_customer(db, data.customer_id, business_id=business_id)
    _validate_dates(data.invoice_date, data.due_date)
    _validate_tax(data.tax_percent)
    lines = _validate_lines(data.items)
    subtotal, tax, total = compute_totals(
        [(line["quantity"], line["unit_price_paise"]) for line in lines],
        data.tax_percent,
    )

    active_payments = db.scalar(
        select(func.count(Payment.id)).where(
            Payment.invoice_id == invoice.id,
            Payment.status == PAYMENT_ACTIVE,
        )
    )
    existing_lines = [(i.description, i.quantity, i.unit_price_paise) for i in invoice.items]
    new_lines = [(l["description"], l["quantity"], l["unit_price_paise"]) for l in lines]
    amounts_changed = (
        customer.id != invoice.customer_id
        or data.invoice_date != invoice.invoice_date
        or data.due_date != invoice.due_date
        or data.tax_percent != invoice.tax_percent
        or total != invoice.total_paise
        or existing_lines != new_lines
    )
    if active_payments and amounts_changed:
        raise AppError(409, AMOUNT_LOCKED_MESSAGE)

    if data.invoice_number is None:
        number = invoice.invoice_number
    else:
        number = _resolve_number(db, data.invoice_number, exclude_id=invoice.id, business_id=business_id)

    now = now_utc()
    invoice.invoice_number = number
    invoice.customer_id = customer.id
    invoice.description = data.description.strip()
    invoice.notes = _clean_text(data.notes)
    invoice.invoice_date = data.invoice_date
    invoice.due_date = data.due_date
    invoice.tax_percent = data.tax_percent
    invoice.subtotal_paise = subtotal
    invoice.tax_paise = tax
    invoice.total_paise = total
    invoice.items = _build_items(lines)
    invoice.updated_at = now
    record_event(db, "invoice", invoice.id, "updated", f"Invoice {number} updated", now)
    db.commit()
    return get_invoice_detail(db, invoice.id, today, business_id=business_id)


def send_invoice(
    db: Session,
    invoice_id: int,
    today: date | None = None,
    business_id: int | None = None,
) -> dict:
    invoice = _get_invoice(db, invoice_id, business_id=business_id)
    if invoice.lifecycle != LIFECYCLE_DRAFT:
        raise AppError(409, "Only draft invoices can be sent.")
    now = now_utc()
    # Deduct linked physical product stock atomically when invoice is confirmed/sent
    inventory_service.deduct_stock_for_sent_invoice(db, business_id or invoice.business_id, invoice)
    invoice.lifecycle = LIFECYCLE_SENT
    invoice.sent_at = now
    invoice.updated_at = now
    record_event(db, "invoice", invoice.id, "sent", f"Invoice {invoice.invoice_number} sent", now)
    db.commit()
    return get_invoice_detail(db, invoice.id, today, business_id=business_id)


def delete_invoice(db: Session, invoice_id: int, business_id: int | None = None) -> None:
    invoice = _get_invoice(db, invoice_id, business_id=business_id)
    if invoice.lifecycle != LIFECYCLE_DRAFT:
        raise AppError(
            409,
            "Only draft invoices can be deleted. Sent invoices are part of the payment record.",
        )
    db.delete(invoice)
    db.commit()
