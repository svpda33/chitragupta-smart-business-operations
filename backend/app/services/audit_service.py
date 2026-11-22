"""Audit history: append-only event log for invoices and payments."""

from datetime import datetime

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent
from app.utils.money import paise_to_rupees_text

SUMMARY_MAX_LENGTH = 300


def format_rupees(paise: int) -> str:
    return "₹" + paise_to_rupees_text(paise)


def clip_summary(text: str) -> str:
    return text[:SUMMARY_MAX_LENGTH]


def record_event(
    db: Session,
    entity_type: str,
    entity_id: int,
    action: str,
    summary: str,
    now: datetime,
) -> AuditEvent:
    event = AuditEvent(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        summary=clip_summary(summary),
        created_at=now,
    )
    db.add(event)
    return event


def list_history(db: Session, pairs: list[tuple[str, int]]) -> list[AuditEvent]:
    """Events for the given (entity_type, entity_id) pairs, newest first."""
    if not pairs:
        return []
    conditions = [
        and_(AuditEvent.entity_type == entity_type, AuditEvent.entity_id == entity_id)
        for entity_type, entity_id in pairs
    ]
    stmt = (
        select(AuditEvent)
        .where(or_(*conditions))
        .order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
    )
    return list(db.scalars(stmt))


def history_to_dicts(events: list[AuditEvent]) -> list[dict]:
    return [
        {"id": e.id, "action": e.action, "summary": e.summary, "created_at": e.created_at}
        for e in events
    ]
