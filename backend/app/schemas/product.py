from datetime import datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.utils.money import rupees_to_paise


def _blank_to_none(v):
    if isinstance(v, str) and not v.strip():
        return None
    return v


class ProductIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    item_type: Literal["product", "service"] = "product"
    name: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=1000)
    sku: str | None = Field(default=None, max_length=64)
    category: str | None = Field(default="General", max_length=80)
    selling_price: str | int | float | Decimal
    cost_price: str | int | float | Decimal | None = None
    tax_percent: int = Field(default=18, ge=0, le=100)
    unit: str = Field(default="pcs", min_length=1, max_length=32)
    stock_quantity: int = Field(default=0, ge=0, le=10_000_000)
    min_stock_threshold: int = Field(default=5, ge=0, le=1_000_000)
    is_active: bool = True

    @field_validator("description", "sku", "category", mode="before")
    @classmethod
    def clean_opt(cls, v):
        return _blank_to_none(v)

    def selling_price_paise(self) -> int:
        paise = rupees_to_paise(self.selling_price)
        if paise <= 0:
            raise ValueError("Selling price must be greater than zero.")
        return paise

    def cost_price_paise(self) -> int | None:
        if self.cost_price is None or str(self.cost_price).strip() == "":
            return None
        paise = rupees_to_paise(self.cost_price)
        if paise < 0:
            raise ValueError("Cost price cannot be negative.")
        return paise


class ProductOut(BaseModel):
    id: int
    business_id: int
    item_type: str
    name: str
    description: str | None
    sku: str | None
    category: str | None
    image_url: str | None
    selling_price_paise: int
    cost_price_paise: int | None
    tax_percent: int
    unit: str
    stock_quantity: int
    min_stock_threshold: int
    stock_status: str  # "service" | "in_stock" | "low_stock" | "out_of_stock"
    is_active: bool
    created_at: datetime
    updated_at: datetime


class StockAdjustIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    movement_type: Literal["restock", "adjustment", "return_reversal"] = "restock"
    quantity_change: int = Field(..., ge=-1_000_000, le=1_000_000)
    reason: str = Field(min_length=2, max_length=300)
    reference: str | None = Field(default=None, max_length=120)

    @field_validator("reference", mode="before")
    @classmethod
    def clean_ref(cls, v):
        return _blank_to_none(v)


class InventoryMovementOut(BaseModel):
    id: int
    product_id: int
    product_name: str
    sku: str | None
    quantity_change: int
    balance_after: int
    movement_type: str
    reason: str | None
    reference: str | None
    invoice_id: int | None
    created_at: datetime


class InventorySummaryOut(BaseModel):
    total_active_products: int
    total_active_services: int
    total_stock_units: int
    low_stock_count: int
    out_of_stock_count: int
    inventory_valuation_paise: int
    valued_products_count: int
    low_stock_items: list[ProductOut]
    recent_movements: list[InventoryMovementOut]
