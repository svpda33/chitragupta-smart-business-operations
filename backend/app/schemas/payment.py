from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import HistoryEvent, check_rupee_amount


def _blank_to_none(value):
    if isinstance(value, str) and not value.strip():
        return None
    return value


class PaymentCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    invoice_id: int
    amount: str | int | float | Decimal
    payment_date: date | None = None
    method: str
    reference: str | None = Field(default=None, max_length=100)
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("amount")
    @classmethod
    def check_amount(cls, value):
        return check_rupee_amount(value)

    @field_validator("reference", "notes", mode="before")
    @classmethod
    def clean_optional_text(cls, value):
        return _blank_to_none(value)


class PaymentUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    amount: str | int | float | Decimal
    payment_date: date
    method: str
    reference: str | None = Field(default=None, max_length=100)
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("amount")
    @classmethod
    def check_amount(cls, value):
        return check_rupee_amount(value)

    @field_validator("reference", "notes", mode="before")
    @classmethod
    def clean_optional_text(cls, value):
        return _blank_to_none(value)


class ReverseIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    reason: str = Field(min_length=3, max_length=300)


class PaymentOut(BaseModel):
    id: int
    invoice_id: int
    invoice_number: str
    customer_id: int
    customer_name: str
    amount_paise: int
    payment_date: date
    method: str
    reference: str | None = None
    notes: str | None = None
    status: str
    reversed_at: datetime | None = None
    reversal_reason: str | None = None
    created_at: datetime


class PaymentDetail(PaymentOut):
    history: list[HistoryEvent] = []
