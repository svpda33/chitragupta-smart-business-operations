from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _blank_to_none(value):
    if isinstance(value, str) and not value.strip():
        return None
    return value


class CustomerIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=120)
    email: str | None = None
    phone: str | None = None
    address: str | None = Field(default=None, max_length=500)
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("email", "phone", "address", "notes", mode="before")
    @classmethod
    def clean_optional_text(cls, value):
        return _blank_to_none(value)


class CustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
    invoice_count: int = 0
    total_invoiced_paise: int = 0
    total_paid_paise: int = 0
    outstanding_paise: int = 0
    overdue_paise: int = 0
