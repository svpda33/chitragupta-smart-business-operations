"""Payment rules: recording, editing, reversing and listing payments.

Money is integer paise. Only ACTIVE payments count towards an invoice's paid total.
"""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.schemas.payment import PaymentCreate, PaymentUpdate
from app.services.audit_service import format_rupees, history_to_dicts, list_history, record_event
from app.services.status import LIFECYCLE_SENT
from app.utils.dates import now_utc
from app.utils.dates import today as default_today
from app.utils.money import positive_rupees_to_paise

PAYMENT_ACTIVE = "active"
PAYMENT_REVERSED = "reversed"
PAYMENT_METHODS = ("cash", "bank_transfer", "upi", "other")
REASON_MIN_LENGTH = 3
REASON_MAX_LENGTH = 300


def paid_total(db: Session, invoice_id: int, exclude_payment_id: int | None = None) -> int:
    """Sum of ACTIVE payments for an invoice, optionally leaving one payment out."""
    stmt = select(func.coalesce(func.sum(Payment.amount_paise), 0)).where(
        Payment.invoice_id == invoice_id,
        Payment.status == PAYMENT_ACTIVE,
    )
    if exclude_payment_id is not None:
        stmt = stmt.where(Payment.id != exclude_payment_id)
    return int(db.scalar(stmt) or 0)


def paid_totals(db: Session, invoice_ids: list[int]) -> dict[int, int]:
    """Active paid totals for many invoices in one query."""
    if not invoice_ids:
        return {}
    rows = db.execute(
        select(Payment.invoice_id, func.sum(Payment.amount_paise))
        .where(Payment.invoice_id.in_(invoice_ids), Payment.status == PAYMENT_ACTIVE)
        .group_by(Payment.invoice_id)
    ).all()
    return {invoice_id: int(total or 0) for invoice_id, total in rows}


def ensure_can_record(invoice: Invoice) -> None:
    if invoice.lifecycle != LIFECYCLE_SENT:
        raise AppError(409, "Payments can only be recorded against sent invoices.")


def check_not_over(invoice: Invoice, other_paid: int, amount: int) -> None:
    if other_paid + amount > invoice.total_paise:
        remaining = invoice.total_paise - other_paid
        raise AppError(
            422,
            f"The payment is more than the outstanding balance of {format_rupees(remaining)}.",
            field="amount",
        )


def _amount_paise(value) -> int:
    try:
        return positive_rupees_to_paise(value)
    except ValueError as exc:
        raise AppError(422, str(exc), field="amount") from exc


def _check_date_and_method(payment_date: date, method: str, today: date) -> None:
    if payment_date > today:
        raise AppError(422, "Payment date cannot be in the future.", field="payment_date")
    if method not in PAYMENT_METHODS:
        raise AppError(
            422,
            "Choose a payment method: cash, bank_transfer, upi or other.",
            field="method",
        )


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def to_payment_out(payment: Payment, invoice_number: str, customer_name: str) -> dict:
    return {
        "id": payment.id,
        "invoice_id": payment.invoice_id,
        "invoice_number": invoice_number,
        "customer_id": payment.customer_id,
        "customer_name": customer_name,
        "amount_paise": payment.amount_paise,
        "payment_date": payment.payment_date,
        "method": payment.method,
        "reference": payment.reference,
        "notes": payment.notes,
        "status": payment.status,
        "reversed_at": payment.reversed_at,
        "reversal_reason": payment.reversal_reason,
        "created_at": payment.created_at,
    }


def _joined_statement():
    return (
        select(Payment, Invoice.invoice_number, Customer.name)
        .join(Invoice, Invoice.id == Payment.invoice_id)
        .join(Customer, Customer.id == Payment.customer_id)
    )


def _get_payment(db: Session, payment_id: int, business_id: int | None = None) -> Payment:
    stmt = select(Payment).where(Payment.id == payment_id)
    if business_id is not None:
        stmt = stmt.where(Payment.business_id == business_id)
    payment = db.scalar(stmt.limit(1))
    if payment is None:
        raise AppError(404, "Payment not found.")
    return payment


def _get_invoice(db: Session, invoice_id: int, business_id: int | None = None) -> Invoice:
    stmt = select(Invoice).where(Invoice.id == invoice_id)
    if business_id is not None:
        stmt = stmt.where(Invoice.business_id == business_id)
    invoice = db.scalar(stmt.limit(1))
    if invoice is None:
        raise AppError(404, "Invoice not found.")
    return invoice


def record_payment(
    db: Session,
    data: PaymentCreate,
    today: date | None = None,
    business_id: int | None = None,
) -> dict:
    today = today or default_today()
    invoice = _get_invoice(db, data.invoice_id, business_id=business_id)
    ensure_can_record(invoice)

    amount = _amount_paise(data.amount)
    payment_date = data.payment_date or today
    method = data.method.strip()
    _check_date_and_method(payment_date, method, today)
    check_not_over(invoice, paid_total(db, invoice.id), amount)

    now = now_utc()
    payment = Payment(
        business_id=business_id or invoice.business_id,
        invoice_id=invoice.id,
        customer_id=invoice.customer_id,
        amount_paise=amount,
        payment_date=payment_date,
        method=method,
        reference=_clean_text(data.reference),
        notes=_clean_text(data.notes),
        status=PAYMENT_ACTIVE,
        created_at=now,
        updated_at=now,
    )
    db.add(payment)
    db.flush()

    summary = f"Payment of {format_rupees(amount)} recorded"
    record_event(db, "payment", payment.id, "payment_recorded", summary, now)
    record_event(
        db,
        "invoice",
        invoice.id,
        "payment_recorded",
        f"{summary} against {invoice.invoice_number}",
        now,
    )
    db.commit()
    return get_payment_detail(db, payment.id, business_id=business_id)


def list_payments(
    db: Session,
    invoice_id: int | None = None,
    customer_id: int | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
    business_id: int | None = None,
) -> tuple[list[dict], int]:
    conditions = []
    if business_id is not None:
        conditions.append(Payment.business_id == business_id)
    if invoice_id is not None:
        conditions.append(Payment.invoice_id == invoice_id)
    if customer_id is not None:
        conditions.append(Payment.customer_id == customer_id)
    if status is not None:
        conditions.append(Payment.status == status)

    stmt = _joined_statement()
    if conditions:
        stmt = stmt.where(*conditions)

    total = int(db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
    rows = db.execute(
        stmt.order_by(Payment.payment_date.desc(), Payment.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    items = [to_payment_out(payment, number, name) for payment, number, name in rows]
    return items, total


def get_payment_detail(
    db: Session,
    payment_id: int,
    business_id: int | None = None,
) -> dict:
    stmt = _joined_statement().where(Payment.id == payment_id)
    if business_id is not None:
        stmt = stmt.where(Payment.business_id == business_id)
    row = db.execute(stmt).first()
    if row is None:
        raise AppError(404, "Payment not found.")
    payment, invoice_number, customer_name = row
    history = history_to_dicts(list_history(db, [("payment", payment.id)]))
    return {**to_payment_out(payment, invoice_number, customer_name), "history": history}


def update_payment(
    db: Session,
    payment_id: int,
    data: PaymentUpdate,
    today: date | None = None,
    business_id: int | None = None,
) -> dict:
    today = today or default_today()
    payment = _get_payment(db, payment_id, business_id=business_id)
    if payment.status != PAYMENT_ACTIVE:
        raise AppError(409, "Reversed payments cannot be edited.")
    invoice = _get_invoice(db, payment.invoice_id, business_id=business_id)

    amount = _amount_paise(data.amount)
    method = data.method.strip()
    _check_date_and_method(data.payment_date, method, today)
    check_not_over(invoice, paid_total(db, invoice.id, exclude_payment_id=payment.id), amount)

    reference = _clean_text(data.reference)
    notes = _clean_text(data.notes)

    changes = []
    if amount != payment.amount_paise:
        changes.append(
            f"amount {format_rupees(payment.amount_paise)} -> {format_rupees(amount)}"
        )
    if data.payment_date != payment.payment_date:
        changes.append(f"payment date {payment.payment_date.isoformat()} -> {data.payment_date.isoformat()}")
    if method != payment.method:
        changes.append(f"method {payment.method} -> {method}")
    if reference != payment.reference:
        changes.append(f"reference {payment.reference or '-'} -> {reference or '-'}")
    if notes != payment.notes:
        changes.append(f"notes {payment.notes or '-'} -> {notes or '-'}")

    payment.amount_paise = amount
    payment.payment_date = data.payment_date
    payment.method = method
    payment.reference = reference
    payment.notes = notes

    now = now_utc()
    payment.updated_at = now
    summary = "Payment updated: " + (", ".join(changes) if changes else "no field changes")
    record_event(db, "payment", payment.id, "payment_updated", summary, now)
    record_event(
        db,
        "invoice",
        invoice.id,
        "payment_updated",
        f"Payment {payment.id} updated on {invoice.invoice_number}: "
        + (", ".join(changes) if changes else "no field changes"),
        now,
    )
    db.commit()
    return get_payment_detail(db, payment.id, business_id=business_id)


def reverse_payment(
    db: Session,
    payment_id: int,
    reason: str,
    business_id: int | None = None,
) -> dict:
    payment = _get_payment(db, payment_id, business_id=business_id)
    if payment.status == PAYMENT_REVERSED:
        raise AppError(409, "This payment has already been reversed.")

    reason_text = (reason or "").strip()
    if not (REASON_MIN_LENGTH <= len(reason_text) <= REASON_MAX_LENGTH):
        raise AppError(
            422,
            f"Enter a reason between {REASON_MIN_LENGTH} and {REASON_MAX_LENGTH} characters.",
            field="reason",
        )
    invoice = _get_invoice(db, payment.invoice_id, business_id=business_id)

    now = now_utc()
    payment.status = PAYMENT_REVERSED
    payment.reversed_at = now
    payment.reversal_reason = reason_text
    payment.updated_at = now

    summary = f"Payment of {format_rupees(payment.amount_paise)} reversed: {reason_text}"
    record_event(db, "payment", payment.id, "payment_reversed", summary, now)
    record_event(db, "invoice", invoice.id, "payment_reversed", summary, now)
    db.commit()
    return get_payment_detail(db, payment.id, business_id=business_id)
