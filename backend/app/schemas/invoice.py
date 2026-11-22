from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import HistoryEvent, check_rupee_amount
from app.schemas.payment import PaymentOut
from app.utils.money import positive_rupees_to_paise


def _blank_to_none(value):
    if isinstance(value, str) and not value.strip():
        return None
    return value


class ItemIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    product_id: int | None = None
    description: str = Field(min_length=1, max_length=200)
    quantity: int = Field(ge=1, le=100000)
    unit_price: str | int | float | Decimal

    @field_validator("unit_price")
    @classmethod
    def check_price(cls, value):
        return check_rupee_amount(value)

    def unit_price_paise(self) -> int:
        return positive_rupees_to_paise(self.unit_price)


class InvoiceIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    customer_id: int
    invoice_number: str | None = Field(default=None, max_length=32)
    invoice_date: date
    due_date: date
    description: str = Field(min_length=1, max_length=200)
    notes: str | None = Field(default=None, max_length=1000)
    tax_percent: int = Field(default=0, ge=0, le=100)
    items: list[ItemIn] = Field(min_length=1, max_length=50)

    @field_validator("invoice_number", "notes", mode="before")
    @classmethod
    def clean_optional_text(cls, value):
        return _blank_to_none(value)


class InvoiceListItem(BaseModel):
    id: int
    invoice_number: str
    customer_id: int
    customer_name: str
    description: str
    invoice_date: date
    due_date: date
    lifecycle: str
    status: str
    total_paise: int
    paid_paise: int
    outstanding_paise: int
    days_overdue: int


class ItemOut(BaseModel):
    id: int
    product_id: int | None = None
    position: int
    description: str
    quantity: int
    unit_price_paise: int
    line_total_paise: int


class InvoiceOut(InvoiceListItem):
    notes: str | None = None
    tax_percent: int
    subtotal_paise: int
    tax_paise: int
    sent_at: datetime | None = None
    items: list[ItemOut] = []
    payments: list[PaymentOut] = []
    history: list[HistoryEvent] = []
