"""Invoice status rules. Pure functions: no database access."""

from datetime import date

LIFECYCLE_DRAFT = "draft"
LIFECYCLE_SENT = "sent"

STATUS_DRAFT = "draft"
STATUS_PENDING = "pending"
STATUS_PARTIALLY_PAID = "partially_paid"
STATUS_OVERDUE = "overdue"
STATUS_PAID = "paid"

VALID_STATUSES = (STATUS_DRAFT, STATUS_PENDING, STATUS_PARTIALLY_PAID, STATUS_OVERDUE, STATUS_PAID)


def derive_invoice_status(
    lifecycle: str,
    total_paise: int,
    paid_paise: int,
    due_date: date,
    today: date,
) -> tuple[str, int]:
    """Return (status, days_overdue) for an invoice."""
    if lifecycle == LIFECYCLE_DRAFT:
        return STATUS_DRAFT, 0

    outstanding = total_paise - paid_paise
    if outstanding <= 0:
        return STATUS_PAID, 0
    if due_date < today:
        return STATUS_OVERDUE, (today - due_date).days
    if paid_paise == 0:
        return STATUS_PENDING, 0
    return STATUS_PARTIALLY_PAID, 0
