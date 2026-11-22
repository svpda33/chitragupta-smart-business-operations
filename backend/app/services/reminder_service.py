from datetime import date, timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.audit_event import AuditEvent
from app.models.customer import Customer
from app.models.invoice import Invoice
from app.services.audit_service import record_event
from app.services.payment_service import paid_totals
from app.services.setting_service import get_or_create_settings
from app.services.status import LIFECYCLE_SENT, STATUS_OVERDUE, derive_invoice_status
from app.utils.dates import now_utc
from app.utils.money import paise_to_rupees_text


def generate_5_templates(
    customer_name: str,
    invoice_number: str,
    amount_text: str,
    due_date_text: str,
    days_overdue: int,
    days_to_due: int,
    settings,
) -> tuple[str, str, dict]:
    biz_name = settings.business_name
    owner_name = settings.owner_name
    upi_id = settings.upi_id or "aditi@upi"
    bank_info = f"{settings.bank_name or 'Bank'} (A/C: {settings.bank_account or '—'}, IFSC: {settings.bank_ifsc or '—'})"

    if days_to_due == 0:
        urgency = "due_today"
        urgency_label = "Payment Due Today"
        whatsapp = (
            f"Hello {customer_name},\n\n"
            f"This is a gentle reminder from *{biz_name}* that invoice *{invoice_number}* for *₹{amount_text}* "
            f"is due for payment *today ({due_date_text})*.\n\n"
            f"Payment Details:\n"
            f"• UPI ID: *{upi_id}*\n"
            f"• Bank Transfer: {bank_info}\n\n"
            f"Thank you for your partnership!\n— {owner_name}"
        )
        email_subj = f"Due Today: Invoice {invoice_number} - {biz_name}"
        email_body = (
            f"Dear {customer_name},\n\n"
            f"We hope you are having a productive day.\n\n"
            f"This is a quick notification to let you know that invoice {invoice_number} for ₹{amount_text} is due for payment today ({due_date_text}).\n\n"
            f"You can settle the payment via:\n"
            f"• UPI ID: {upi_id}\n"
            f"• Bank Details: {bank_info}\n\n"
            f"If you have already processed this, please disregard this note and accept our thanks.\n\n"
            f"Warm regards,\n{owner_name}\n{biz_name}"
        )
        sms = f"Reminder from {biz_name}: Invoice {invoice_number} for Rs {amount_text} is due today ({due_date_text}). Pay via UPI: {upi_id}."

    elif days_overdue <= 0:
        urgency = "upcoming"
        urgency_label = f"Upcoming Due ({days_to_due}d left)"
        whatsapp = (
            f"Hello {customer_name},\n\n"
            f"Hope you are doing well! This is an advance courtesy reminder from *{biz_name}* regarding invoice *{invoice_number}* for *₹{amount_text}*, "
            f"which is due in *{days_to_due} days on {due_date_text}*.\n\n"
            f"Payment Options:\n"
            f"• UPI ID: *{upi_id}*\n"
            f"• Bank Transfer: {bank_info}\n\n"
            f"Thank you for your business!\n— {owner_name}"
        )
        email_subj = f"Upcoming: Invoice {invoice_number} due on {due_date_text} - {biz_name}"
        email_body = (
            f"Dear {customer_name},\n\n"
            f"We hope this email finds you well.\n\n"
            f"This is an advance notice that invoice {invoice_number} for ₹{amount_text} is scheduled for payment on {due_date_text}.\n\n"
            f"Payment Details:\n"
            f"• UPI ID: {upi_id}\n"
            f"• Bank Transfer: {bank_info}\n\n"
            f"Thank you for your continued collaboration.\n\n"
            f"Warm regards,\n{owner_name}\n{biz_name}"
        )
        sms = f"Advance note from {biz_name}: Invoice {invoice_number} (Rs {amount_text}) is due on {due_date_text}. Pay via UPI: {upi_id}."

    elif days_overdue <= 7:
        urgency = "first_overdue"
        urgency_label = f"First Overdue ({days_overdue}d Overdue)"
        whatsapp = (
            f"Hello {customer_name},\n\n"
            f"Hope you are having a great week! Just following up from *{biz_name}* on invoice *{invoice_number}* for *₹{amount_text}*, "
            f"which was due on *{due_date_text}* ({days_overdue} days ago).\n\n"
            f"Could you please check and confirm when we might expect the payment? Quick UPI: *{upi_id}*.\n\n"
            f"Thanks a lot,\n— {owner_name}"
        )
        email_subj = f"Friendly Follow-up: Invoice {invoice_number} is past due - {biz_name}"
        email_body = (
            f"Dear {customer_name},\n\n"
            f"We noticed that invoice {invoice_number} for ₹{amount_text}, due on {due_date_text}, is now {days_overdue} days past due.\n\n"
            f"We understand how busy things get! Kindly arrange the payment when convenient:\n"
            f"• UPI ID: {upi_id}\n"
            f"• Bank Details: {bank_info}\n\n"
            f"Please let us know if you need any clarification or a duplicate invoice copy.\n\n"
            f"Best regards,\n{owner_name}\n{biz_name}"
        )
        sms = f"Follow-up from {biz_name}: Invoice {invoice_number} for Rs {amount_text} was due on {due_date_text} ({days_overdue}d ago). Settle via UPI: {upi_id}."

    elif days_overdue <= 21:
        urgency = "followup_overdue"
        urgency_label = f"Follow-up Overdue ({days_overdue}d Overdue)"
        whatsapp = (
            f"Dear {customer_name},\n\n"
            f"Our records indicate that invoice *{invoice_number}* for *₹{amount_text}* is now *{days_overdue} days overdue* (due date was {due_date_text}).\n\n"
            f"As a micro-business, prompt settlement is essential for our cash operations. Please arrange payment today via UPI (*{upi_id}*) or Bank Transfer ({bank_info}).\n\n"
            f"Kindly reply with the payment confirmation or reference number.\n— {owner_name}, {biz_name}"
        )
        email_subj = f"SECOND NOTICE: Invoice {invoice_number} ({days_overdue} days past due) - {biz_name}"
        email_body = (
            f"Dear {customer_name},\n\n"
            f"This is an urgent follow-up regarding invoice {invoice_number} for ₹{amount_text}, which was due on {due_date_text} and is now {days_overdue} days overdue.\n\n"
            f"We request you to prioritize this settlement today. Payment details:\n"
            f"• UPI ID: {upi_id}\n"
            f"• Bank Transfer: {bank_info}\n\n"
            f"If there is any question or approval delay, please contact us immediately at {settings.phone or ''}.\n\n"
            f"Sincerely,\n{owner_name}\n{biz_name}"
        )
        sms = f"SECOND NOTICE from {biz_name}: Invoice {invoice_number} (Rs {amount_text}) is {days_overdue} days overdue. Kindly clear today via UPI: {upi_id}."

    else:
        urgency = "final_notice"
        urgency_label = f"Final Polite Follow-up ({days_overdue}d Overdue)"
        whatsapp = (
            f"FINAL NOTICE — {customer_name},\n\n"
            f"Invoice *{invoice_number}* for *₹{amount_text}* is now *{days_overdue} days overdue*. Despite our previous reminders, this balance remains outstanding.\n\n"
            f"Please arrange payment today via UPI (*{upi_id}*) or {bank_info} so we can maintain your account in good standing and continue our working relationship.\n\n"
            f"Thank you for your prompt attention.\n— {owner_name}, {biz_name}"
        )
        email_subj = f"FINAL NOTICE: Invoice {invoice_number} is {days_overdue} days overdue - {biz_name}"
        email_body = (
            f"Dear {customer_name},\n\n"
            f"This is a final polite payment follow-up regarding invoice {invoice_number} for ₹{amount_text}, which was due on {due_date_text} and is now {days_overdue} days overdue.\n\n"
            f"We request that you settle this balance immediately:\n"
            f"• UPI ID: {upi_id}\n"
            f"• Bank Transfer: {bank_info}\n\n"
            f"If payment has already been scheduled, please provide the transfer reference. Otherwise, kindly confirm when we can expect clearance.\n\n"
            f"Best regards,\n{owner_name}\n{biz_name}"
        )
        sms = f"FINAL NOTICE: Invoice {invoice_number} (Rs {amount_text}) is {days_overdue} days overdue from {biz_name}. Please settle today: {upi_id}."

    templates = {
        "whatsapp": whatsapp,
        "email_subject": email_subj,
        "email_body": email_body,
        "sms": sms,
    }
    return urgency, urgency_label, templates


def list_reminders(
    db: Session, today: date | None = None, business_id: int | None = None
) -> dict:
    if today is None:
        today = date.today()

    settings = get_or_create_settings(db, business_id=business_id)

    stmt = (
        select(Invoice, Customer)
        .join(Customer, Invoice.customer_id == Customer.id)
        .where(Invoice.lifecycle == LIFECYCLE_SENT)
        .order_by(Invoice.due_date.asc())
    )
    if business_id is not None:
        stmt = stmt.where(Invoice.business_id == business_id)
    rows = db.execute(stmt).all()
    invoice_ids = [row.Invoice.id for row in rows]
    paid_map = paid_totals(db, invoice_ids)

    reminded_events = db.execute(
        select(AuditEvent.entity_id, AuditEvent.created_at, AuditEvent.summary)
        .where(AuditEvent.entity_type == "invoice", AuditEvent.action == "reminder_sent")
        .order_by(AuditEvent.created_at.desc())
    ).all()
    last_reminded_map = {}
    for r in reminded_events:
        if r.entity_id not in last_reminded_map:
            last_reminded_map[r.entity_id] = r.created_at

    items = []
    total_overdue = 0
    total_upcoming = 0
    total_outstanding = 0

    for row in rows:
        inv = row.Invoice
        cust = row.Customer
        paid = paid_map.get(inv.id, 0)
        status, days_overdue = derive_invoice_status(inv.lifecycle, inv.total_paise, paid, inv.due_date, today)
        outstanding = max(0, inv.total_paise - paid)

        if outstanding <= 0:
            continue

        days_to_due = (inv.due_date - today).days

        # Include all overdue invoices or invoices due within next 5 days
        if days_overdue > 0 or 0 <= days_to_due <= 5:
            total_outstanding += outstanding
            if days_overdue > 0:
                total_overdue += 1
            else:
                total_upcoming += 1

            amt_text = paise_to_rupees_text(outstanding)
            due_text = inv.due_date.strftime("%d %b %Y")
            urgency, urgency_label, templates = generate_5_templates(
                customer_name=cust.name,
                invoice_number=inv.invoice_number,
                amount_text=amt_text,
                due_date_text=due_text,
                days_overdue=days_overdue,
                days_to_due=days_to_due,
                settings=settings,
            )

            items.append({
                "invoice_id": inv.id,
                "invoice_number": inv.invoice_number,
                "customer_id": cust.id,
                "customer_name": cust.name,
                "customer_email": cust.email,
                "customer_phone": cust.phone,
                "total_paise": inv.total_paise,
                "paid_paise": paid,
                "outstanding_paise": outstanding,
                "due_date": inv.due_date,
                "days_overdue": days_overdue,
                "urgency": urgency,
                "urgency_label": urgency_label,
                "templates": templates,
                "last_reminded_at": last_reminded_map.get(inv.id),
            })

    urgency_order = {"final_notice": 0, "followup_overdue": 1, "first_overdue": 2, "due_today": 3, "upcoming": 4}
    items.sort(key=lambda x: (urgency_order.get(x["urgency"], 5), -x["outstanding_paise"]))

    return {
        "items": items,
        "total_overdue_count": total_overdue,
        "total_upcoming_count": total_upcoming,
        "total_outstanding_paise": total_outstanding,
    }


def log_reminder(
    db: Session,
    invoice_id: int,
    channel: str,
    note: str | None = None,
    business_id: int | None = None,
) -> dict:
    inv = db.get(Invoice, invoice_id)
    if not inv or (business_id is not None and inv.business_id != business_id):
        raise AppError(404, "Invoice not found.")

    channel_name = channel.upper()
    summary = f"Assisted reminder sent via {channel_name}."
    if note:
        summary += f" ({note})"

    record_event(db, "invoice", invoice_id, "reminder_sent", summary, now_utc())
    return {"message": "Reminder recorded in audit history.", "invoice_id": invoice_id}
