from datetime import datetime
from decimal import Decimal
import re
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.utils.money import rupees_to_paise

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _blank_to_none(v):
    if isinstance(v, str) and not v.strip():
        return None
    return v


class RegisterIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def check_email(cls, value: str) -> str:
        low = value.lower()
        if not _EMAIL_RE.fullmatch(low):
            raise ValueError("Enter a valid email address.")
        return low

    @field_validator("password")
    @classmethod
    def check_password_strength(cls, value: str) -> str:
        if not any(c.isalpha() for c in value) or not any(c.isdigit() for c in value):
            raise ValueError("Password must be at least 8 characters and include both letters and numbers.")
        return value


class LoginIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)
    remember_me: bool = True

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.lower()


class ForgotPasswordIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: str = Field(min_length=5, max_length=254)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        low = value.lower()
        if not _EMAIL_RE.fullmatch(low):
            raise ValueError("Enter a valid email address.")
        return low


class BusinessOnboardingIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=140)
    category: str | None = Field(default="Services & Consulting", max_length=80)
    description: str | None = Field(default=None, max_length=1000)
    owner_name: str | None = Field(default=None, max_length=120)
    email: str | None = Field(default=None, max_length=254)
    phone: str | None = Field(default=None, max_length=25)
    address: str | None = Field(default=None, max_length=500)
    gstin: str | None = Field(default=None, max_length=20)
    currency: str = Field(default="INR", max_length=10)
    upi_id: str | None = Field(default=None, max_length=100)
    bank_name: str | None = Field(default=None, max_length=100)
    bank_account: str | None = Field(default=None, max_length=50)
    bank_ifsc: str | None = Field(default=None, max_length=20)
    default_payment_terms_days: int = Field(default=15, ge=0, le=180)
    default_tax_percent: int = Field(default=18, ge=0, le=100)
    initial_cash_balance: str | int | float | Decimal | None = None
    safety_cash_threshold: str | int | float | Decimal | None = None
    allow_negative_stock: bool = False

    @field_validator(
        "category",
        "description",
        "owner_name",
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
    def clean_opt(cls, v):
        return _blank_to_none(v)

    def get_initial_cash_paise(self) -> int:
        if self.initial_cash_balance is None or str(self.initial_cash_balance).strip() == "":
            return 0
        return rupees_to_paise(self.initial_cash_balance)

    def get_safety_threshold_paise(self) -> int:
        if self.safety_cash_threshold is None or str(self.safety_cash_threshold).strip() == "":
            return 5000000
        return rupees_to_paise(self.safety_cash_threshold)


class UserOut(BaseModel):
    id: int
    full_name: str
    email: str
    created_at: datetime


class BusinessProfileOut(BaseModel):
    id: int
    name: str
    category: str | None
    description: str | None
    logo_url: str | None
    owner_name: str
    email: str | None
    phone: str | None
    address: str | None
    gstin: str | None
    currency: str
    upi_id: str | None
    bank_name: str | None
    bank_account: str | None
    bank_ifsc: str | None
    default_payment_terms_days: int
    default_tax_percent: int
    initial_cash_balance_paise: int
    monthly_recurring_expenses_paise: int
    safety_cash_threshold_paise: int
    allow_negative_stock: bool
    onboarding_completed: bool
    created_at: datetime
    updated_at: datetime


class AuthMeOut(BaseModel):
    user: UserOut
    business: BusinessProfileOut | None = None
    onboarding_completed: bool
