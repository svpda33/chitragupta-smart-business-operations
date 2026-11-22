"""Shared response shapes and the rupee-amount boundary check."""

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel

from app.utils.money import positive_rupees_to_paise

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


class HistoryEvent(BaseModel):
    id: int
    action: str
    summary: str
    created_at: datetime


def check_rupee_amount(value):
    """Field validator helper: accepts a positive rupee value or raises ValueError."""
    positive_rupees_to_paise(value)
    return value
