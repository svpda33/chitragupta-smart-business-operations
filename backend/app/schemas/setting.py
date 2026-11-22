from datetime import datetime
from decimal import Decimal
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.utils.money import paise_to_rupees_text, rupees_to_paise


def _blank_to_none(value):
    if isinstance(value, str) and not value.strip():
        return None
    return value


class ExpenseItem(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    amount: str | int | float | Decimal | None = None
    amount_paise: int | None = None
    day_of_month: int = Field(default=1, ge=1, le=31)

    @model_validator(mode="before")
    @classmethod
    def check_amount(cls, data: Any):
        if isinstance(data, dict):
            if "amount_paise" in data and data["amount_paise"] is not None and "amount" not in data:
                data["amount"] = str((Decimal(data["amount_paise"]) / Decimal(100)).quantize(Decimal("0.01")))
        return data

    def get_amount_paise(self) -> int:
        if self.amount_paise is not None:
            return self.amount_paise
        if self.amount is not None:
            return rupees_to_paise(self.amount)
        return 0


class SettingIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    business_name: str = Field(min_length=1, max_length=120)
    owner_name: str = Field(min_length=1, max_length=120)
    category: str | None = Field(default=None, max_length=80)
    description: str | None = Field(default=None, max_length=1000)
    currency: str | None = Field(default="INR", max_length=10)
    allow_negative_stock: bool | None = None
    email: str | None = Field(default=None, max_length=254)
    phone: str | None = Field(default=None, max_length=20)
    address: str | None = Field(default=None, max_length=500)
    gstin: str | None = Field(default=None, max_length=20)
    upi_id: str | None = Field(default=None, max_length=100)
    bank_name: str | None = Field(default=None, max_length=100)
    bank_account: str | None = Field(default=None, max_length=50)
    bank_ifsc: str | None = Field(default=None, max_length=20)

    default_payment_terms_days: int = Field(default=15, ge=0, le=180)
    default_tax_percent: int = Field(default=18, ge=0, le=100)

    initial_cash_balance: str | int | float | Decimal | None = None
    initial_cash_balance_paise: int | None = None
    monthly_recurring_expenses: str | int | float | Decimal | None = None
    monthly_recurring_expenses_paise: int | None = None
    safety_cash_threshold: str | int | float | Decimal | None = None
    safety_cash_threshold_paise: int | None = None

    expenses: list[ExpenseItem] = Field(default_factory=list)

    @field_validator(
        "category",
        "description",
        "email",
        "phone",
        "address",
        "gstin",
        "upi_id",
        "bank_name",
        "bank_account",
        "bank_ifsc",
        mode="before",
    )
    @classmethod
    def clean_optional_text(cls, value):
        return _blank_to_none(value)

    def get_initial_cash_paise(self) -> int:
        if self.initial_cash_balance_paise is not None:
            return self.initial_cash_balance_paise
        if self.initial_cash_balance is not None:
            return rupees_to_paise(self.initial_cash_balance)
        return 25000000

    def get_monthly_expenses_paise(self) -> int:
        if self.monthly_recurring_expenses_paise is not None:
            return self.monthly_recurring_expenses_paise
        if self.monthly_recurring_expenses is not None:
            return rupees_to_paise(self.monthly_recurring_expenses)
        return 6500000

    def get_safety_threshold_paise(self) -> int:
        if self.safety_cash_threshold_paise is not None:
            return self.safety_cash_threshold_paise
        if self.safety_cash_threshold is not None:
            return rupees_to_paise(self.safety_cash_threshold)
        return 5000000


class SettingOut(BaseModel):
    business_name: str
    owner_name: str
    category: str | None = None
    description: str | None = None
    logo_url: str | None = None
    currency: str = "INR"
    allow_negative_stock: bool = False
    email: str | None
    phone: str | None
    address: str | None
    gstin: str | None
    upi_id: str | None
    bank_name: str | None
    bank_account: str | None
    bank_ifsc: str | None

    default_payment_terms_days: int
    default_tax_percent: int

    initial_cash_balance_paise: int
    monthly_recurring_expenses_paise: int
    safety_cash_threshold_paise: int
    expenses: list[dict]
    updated_at: datetime
