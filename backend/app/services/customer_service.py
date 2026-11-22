"""Customer rules: validation, unique names, financial summaries and CRUD."""

import re
from datetime import date

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.schemas.customer import CustomerIn
from app.services.payment_service import PAYMENT_ACTIVE, paid_totals
from app.services.status import LIFECYCLE_DRAFT, STATUS_OVERDUE, derive_invoice_status
from app.utils.dates import now_utc
from app.utils.dates import today as default_today

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_SEPARATORS = re.compile(r"[\s\-()]")
PHONE_PATTERN = re.compile(r"^\+?[0-9]{7,15}$")
EMAIL_MAX_LENGTH = 254
PHONE_MAX_LENGTH = 20
DELETE_BLOCKED_MESSAGE = (
    "This customer has invoices and cannot be deleted. Keep the record to preserve payment history."
)


def normalise_text(value: str | None) -> str | None:
    """Strip whitespace; an empty result becomes None."""
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def validate_email(value: str | None) -> str | None:
    cleaned = normalise_text(value)
    if cleaned is None:
        return None
    if len(cleaned) > EMAIL_MAX_LENGTH or not EMAIL_PATTERN.match(cleaned):
        raise AppError(422, "Enter a valid email address.", field="email")
    return cleaned


def validate_phone(value: str | None) -> str | None:
    """Validate the phone number. The trimmed user input is stored as entered."""
    cleaned = normalise_text(value)
    if cleaned is None:
        return None
    digits = PHONE_SEPARATORS.sub("", cleaned)
    if len(cleaned) > PHONE_MAX_LENGTH or not PHONE_PATTERN.match(digits):
        raise AppError(422, "Enter a valid phone number with 7 to 15 digits.", field="phone")
    return cleaned


def ensure_unique_name(
    db: Session,
    name: str,
    exclude_id: int | None = None,
    business_id: int | None = None,
) -> None:
    stmt = select(Customer.id).where(func.lower(Customer.name) == name.lower())
    if business_id is not None:
        stmt = stmt.where(Customer.business_id == business_id)
    if exclude_id is not None:
        stmt = stmt.where(Customer.id != exclude_id)
    if db.scalar(stmt.limit(1)) is not None:
        raise AppError(409, "A customer with this name already exists.", field="name")


def _empty_summary() -> dict[str, int]:
    return {
        "invoice_count": 0,
        "total_invoiced_paise": 0,
        "total_paid_paise": 0,
        "outstanding_paise": 0,
        "overdue_paise": 0,
    }


def summarise(db: Session, customer_ids: list[int], today: date | None = None) -> dict[int, dict[str, int]]:
    """Per-customer totals. Drafts count as invoices but add nothing to money totals."""
    today = today or default_today()
    summary = {customer_id: _empty_summary() for customer_id in customer_ids}
    if not customer_ids:
        return summary

    invoice_rows = db.execute(
        select(Invoice.id, Invoice.customer_id, Invoice.lifecycle, Invoice.total_paise, Invoice.due_date)
        .where(Invoice.customer_id.in_(customer_ids))
    ).all()
    paid_by_invoice = paid_totals(db, [row.id for row in invoice_rows])

    for row in invoice_rows:
        bucket = summary[row.customer_id]
        bucket["invoice_count"] += 1
        if row.lifecycle == LIFECYCLE_DRAFT:
            continue
        paid = paid_by_invoice.get(row.id, 0)
        outstanding = row.total_paise - paid
        status, _days = derive_invoice_status(row.lifecycle, row.total_paise, paid, row.due_date, today)
        bucket["total_invoiced_paise"] += row.total_paise
        bucket["outstanding_paise"] += outstanding
        if status == STATUS_OVERDUE:
            bucket["overdue_paise"] += outstanding

    paid_rows = db.execute(
        select(Payment.customer_id, func.sum(Payment.amount_paise))
        .where(Payment.customer_id.in_(customer_ids), Payment.status == PAYMENT_ACTIVE)
        .group_by(Payment.customer_id)
    ).all()
    for customer_id, total in paid_rows:
        summary[customer_id]["total_paid_paise"] = int(total or 0)
    return summary


def _customer_dict(customer: Customer, stats: dict[str, int]) -> dict:
    return {
        "id": customer.id,
        "name": customer.name,
        "email": customer.email,
        "phone": customer.phone,
        "address": customer.address,
        "notes": customer.notes,
        "created_at": customer.created_at,
        "updated_at": customer.updated_at,
        **stats,
    }


def _get_customer(db: Session, customer_id: int, business_id: int | None = None) -> Customer:
    stmt = select(Customer).where(Customer.id == customer_id)
    if business_id is not None:
        stmt = stmt.where(Customer.business_id == business_id)
    customer = db.scalar(stmt.limit(1))
    if customer is None:
        raise AppError(404, "Customer not found.")
    return customer


def _validated_fields(
    db: Session,
    data: CustomerIn,
    exclude_id: int | None,
    business_id: int | None = None,
) -> dict:
    name = data.name.strip()
    if not name:
        raise AppError(422, "Enter a customer name.", field="name")
    ensure_unique_name(db, name, exclude_id, business_id=business_id)
    return {
        "name": name,
        "email": validate_email(data.email),
        "phone": validate_phone(data.phone),
        "address": normalise_text(data.address),
        "notes": normalise_text(data.notes),
    }


def list_customers(
    db: Session,
    search: str | None = None,
    page: int = 1,
    page_size: int = 20,
    today: date | None = None,
    business_id: int | None = None,
) -> tuple[list[dict], int]:
    conditions = []
    if business_id is not None:
        conditions.append(Customer.business_id == business_id)
    term = normalise_text(search)
    if term:
        pattern = f"%{term}%"
        conditions.append(
            or_(
                Customer.name.ilike(pattern),
                Customer.email.ilike(pattern),
                Customer.phone.ilike(pattern),
            )
        )

    count_stmt = select(func.count(Customer.id))
    list_stmt = select(Customer)
    for condition in conditions:
        count_stmt = count_stmt.where(condition)
        list_stmt = list_stmt.where(condition)

    total = int(db.scalar(count_stmt) or 0)
    customers = list(
        db.scalars(
            list_stmt.order_by(func.lower(Customer.name), Customer.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    summaries = summarise(db, [c.id for c in customers], today)
    items = [_customer_dict(c, summaries[c.id]) for c in customers]
    return items, total


def get_customer(
    db: Session,
    customer_id: int,
    today: date | None = None,
    business_id: int | None = None,
) -> dict:
    customer = _get_customer(db, customer_id, business_id=business_id)
    summaries = summarise(db, [customer.id], today)
    return _customer_dict(customer, summaries[customer.id])


def create_customer(
    db: Session,
    data: CustomerIn,
    today: date | None = None,
    business_id: int | None = None,
) -> dict:
    fields = _validated_fields(db, data, exclude_id=None, business_id=business_id)
    now = now_utc()
    customer = Customer(business_id=business_id, **fields, created_at=now, updated_at=now)
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return _customer_dict(customer, summarise(db, [customer.id], today)[customer.id])


def update_customer(
    db: Session,
    customer_id: int,
    data: CustomerIn,
    today: date | None = None,
    business_id: int | None = None,
) -> dict:
    customer = _get_customer(db, customer_id, business_id=business_id)
    fields = _validated_fields(db, data, exclude_id=customer.id, business_id=business_id)
    for field_name, value in fields.items():
        setattr(customer, field_name, value)
    customer.updated_at = now_utc()
    db.commit()
    db.refresh(customer)
    return _customer_dict(customer, summarise(db, [customer.id], today)[customer.id])


def delete_customer(db: Session, customer_id: int, business_id: int | None = None) -> None:
    customer = _get_customer(db, customer_id, business_id=business_id)
    has_invoices = db.scalar(select(func.count(Invoice.id)).where(Invoice.customer_id == customer.id))
    if has_invoices:
        raise AppError(409, DELETE_BLOCKED_MESSAGE)
    db.delete(customer)
    db.commit()
