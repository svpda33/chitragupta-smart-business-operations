from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field

from app.utils.money import positive_rupees_to_paise


class ExpenseIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=120)
    category: str = Field(default="Other", max_length=50)
    amount: str | int | float | Decimal
    expense_date: date
    is_recurring: bool = False
    day_of_month: int | None = Field(default=None, ge=1, le=31)
    notes: str | None = Field(default=None, max_length=500)

    def amount_paise(self) -> int:
        return positive_rupees_to_paise(self.amount)


class ExpenseOut(BaseModel):
    id: int
    name: str
    category: str
    amount_paise: int
    expense_date: date
    is_recurring: bool
    day_of_month: int | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
