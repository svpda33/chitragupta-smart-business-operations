"""Interactive business notepad model scoped per business."""

import json
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base
from app.utils.dates import now_utc


class BusinessNote(Base):
    __tablename__ = "business_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(160), nullable=False, default="Untitled note")
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    category: Mapped[str] = mapped_column(String(48), nullable=False, default="General")
    is_pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    checklist_json: Mapped[str | None] = mapped_column(Text, nullable=True, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=now_utc, onupdate=now_utc
    )

    def get_checklist(self) -> list[dict]:
        if not self.checklist_json:
            return []
        try:
            data = json.loads(self.checklist_json)
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def set_checklist(self, items: list[dict]) -> None:
        self.checklist_json = json.dumps(items)
