from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_business
from app.database.session import get_db
from app.models.business import Business
from app.schemas.reminder import LogReminderIn, ReminderListResponse
from app.services import reminder_service

router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.get("", response_model=ReminderListResponse)
def get_reminders(
    db: Session = Depends(get_db),
    business: Business = Depends(get_current_business),
) -> dict:
    return reminder_service.list_reminders(db, today=date.today(), business_id=business.id)


@router.post("/{invoice_id}/log")
def log_reminder(
    invoice_id: int,
    data: LogReminderIn,
    db: Session = Depends(get_db),
    business: Business = Depends(get_current_business),
) -> dict:
    return reminder_service.log_reminder(
        db, invoice_id, channel=data.channel, note=data.note, business_id=business.id
    )
