from datetime import date, datetime
from pydantic import BaseModel


class ReminderTemplates(BaseModel):
    whatsapp: str
    email_subject: str
    email_body: str
    sms: str


class ReminderItem(BaseModel):
    invoice_id: int
    invoice_number: str
    customer_id: int
    customer_name: str
    customer_email: str | None
    customer_phone: str | None

    total_paise: int
    paid_paise: int
    outstanding_paise: int
    due_date: date
    days_overdue: int

    urgency: str  # upcoming, gentle, firm, urgent
    urgency_label: str

    templates: ReminderTemplates
    last_reminded_at: datetime | None = None


class ReminderListResponse(BaseModel):
    items: list[ReminderItem]
    total_overdue_count: int
    total_upcoming_count: int
    total_outstanding_paise: int


class LogReminderIn(BaseModel):
    channel: str  # whatsapp, email, sms
    note: str | None = None
