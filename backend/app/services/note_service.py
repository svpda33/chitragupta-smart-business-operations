"""Interactive business notepad persistence service scoped per business."""

from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.note import BusinessNote
from app.schemas.note import NoteIn
from app.utils.dates import now_utc


def serialize_note(note: BusinessNote) -> dict[str, Any]:
    return {
        "id": note.id,
        "business_id": note.business_id,
        "title": note.title,
        "content": note.content,
        "category": note.category,
        "is_pinned": note.is_pinned,
        "checklist": note.get_checklist(),
        "created_at": note.created_at,
        "updated_at": note.updated_at,
    }


def list_notes(
    db: Session,
    business_id: int,
    search: str | None = None,
    category: str | None = None,
) -> list[dict[str, Any]]:
    stmt = select(BusinessNote).where(BusinessNote.business_id == business_id)
    if category and category.strip() and category.strip() != "All":
        stmt = stmt.where(BusinessNote.category == category.strip())
    if search and search.strip():
        term = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                BusinessNote.title.ilike(term),
                BusinessNote.content.ilike(term),
                BusinessNote.category.ilike(term),
            )
        )
    stmt = stmt.order_by(BusinessNote.is_pinned.desc(), BusinessNote.updated_at.desc(), BusinessNote.id.desc())
    return [serialize_note(n) for n in db.scalars(stmt).all()]


def _get_note(db: Session, business_id: int, note_id: int) -> BusinessNote:
    note = db.scalar(
        select(BusinessNote)
        .where(BusinessNote.id == note_id, BusinessNote.business_id == business_id)
        .limit(1)
    )
    if note is None:
        raise AppError(404, "Note not found.")
    return note


def create_note(db: Session, business_id: int, data: NoteIn) -> dict[str, Any]:
    now = now_utc()
    note = BusinessNote(
        business_id=business_id,
        title=data.title or "Untitled note",
        content=data.content,
        category=data.category or "General",
        is_pinned=data.is_pinned,
        created_at=now,
        updated_at=now,
    )
    note.set_checklist([item.model_dump() for item in data.checklist])
    db.add(note)
    db.commit()
    db.refresh(note)
    return serialize_note(note)


def update_note(db: Session, business_id: int, note_id: int, data: NoteIn) -> dict[str, Any]:
    note = _get_note(db, business_id, note_id)
    note.title = data.title or "Untitled note"
    note.content = data.content
    note.category = data.category or "General"
    note.is_pinned = data.is_pinned
    note.set_checklist([item.model_dump() for item in data.checklist])
    note.updated_at = now_utc()
    db.commit()
    db.refresh(note)
    return serialize_note(note)


def delete_note(db: Session, business_id: int, note_id: int) -> None:
    note = _get_note(db, business_id, note_id)
    db.delete(note)
    db.commit()
