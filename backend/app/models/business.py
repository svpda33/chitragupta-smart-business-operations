"""Business workspace profile owned by a registered user."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.utils.dates import now_utc


class Business(Base):
    __tablename__ = "businesses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(140), nullable=False)
    category: Mapped[str | None] = mapped_column(String(80), nullable=True, default="Services & Consulting")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(300), nullable=True)

    owner_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(25), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    gstin: Mapped[str | None] = mapped_column(String(20), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="INR")

    upi_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    bank_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    bank_account: Mapped[str | None] = mapped_column(String(50), nullable=True)
    bank_ifsc: Mapped[str | None] = mapped_column(String(20), nullable=True)

    default_payment_terms_days: Mapped[int] = mapped_column(Integer, nullable=False, default=15)
    default_tax_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=18)
    initial_cash_balance_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    monthly_recurring_expenses_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    safety_cash_threshold_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=5000000)
    allow_negative_stock: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=now_utc, onupdate=now_utc
    )

    owner: Mapped["User"] = relationship(back_populates="businesses")
