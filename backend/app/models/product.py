"""Product and Service catalogue item model scoped per business."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base
from app.utils.dates import now_utc


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    item_type: Mapped[str] = mapped_column(String(16), nullable=False, default="product")  # "product" | "service"
    name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sku: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    category: Mapped[str | None] = mapped_column(String(80), nullable=True, default="General")
    image_url: Mapped[str | None] = mapped_column(String(300), nullable=True)

    selling_price_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_price_paise: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tax_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=18)
    unit: Mapped[str] = mapped_column(String(32), nullable=False, default="pcs")

    # Stock fields (used when item_type == "product")
    stock_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    min_stock_threshold: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=now_utc, onupdate=now_utc
    )
