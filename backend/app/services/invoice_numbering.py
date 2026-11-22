"""Invoice number generation: INV-0001, INV-0002, ..."""

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.invoice import Invoice

_NUMBER_PATTERN = re.compile(r"^INV-(\d+)$")


def next_invoice_number(db: Session, business_id: int | None = None) -> str:
    highest = 0
    stmt = select(Invoice.invoice_number)
    if business_id is not None:
        stmt = stmt.where(Invoice.business_id == business_id)
    for number in db.scalars(stmt):
        match = _NUMBER_PATTERN.match(number or "")
        if match:
            highest = max(highest, int(match.group(1)))
    return "INV-%04d" % (highest + 1)
