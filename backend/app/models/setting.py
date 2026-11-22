import json
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base
from app.utils.dates import now_utc


class Setting(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    business_id: Mapped[int | None] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"), nullable=True, index=True
    )
    business_name: Mapped[str] = mapped_column(String(120), nullable=False, default="My Business")
    owner_name: Mapped[str] = mapped_column(String(120), nullable=False, default="Aditi Sharma")
    email: Mapped[str | None] = mapped_column(String(254), nullable=True, default="aditi@chitragupta.local")
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True, default="+91 98765 43210")
    address: Mapped[str | None] = mapped_column(String(500), nullable=True, default="123 Indiranagar, Bengaluru, Karnataka 560038")
    gstin: Mapped[str | None] = mapped_column(String(20), nullable=True, default="29AAAAA0000A1Z5")
    upi_id: Mapped[str | None] = mapped_column(String(100), nullable=True, default="aditi@upi")
    bank_name: Mapped[str | None] = mapped_column(String(100), nullable=True, default="HDFC Bank")
    bank_account: Mapped[str | None] = mapped_column(String(50), nullable=True, default="50100456789012")
    bank_ifsc: Mapped[str | None] = mapped_column(String(20), nullable=True, default="HDFC0001234")

    default_payment_terms_days: Mapped[int] = mapped_column(Integer, nullable=False, default=15)
    default_tax_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=18)

    initial_cash_balance_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=25000000)
    monthly_recurring_expenses_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=6500000)
    safety_cash_threshold_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=5000000)
    expenses_json: Mapped[str | None] = mapped_column(Text, nullable=True, default="[]")

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=now_utc, onupdate=now_utc
    )

    def get_expenses(self) -> list[dict]:
        if not self.expenses_json:
            return []
        try:
            return json.loads(self.expenses_json)
        except Exception:
            return []

    def set_expenses(self, items: list[dict]) -> None:
        self.expenses_json = json.dumps(items)
