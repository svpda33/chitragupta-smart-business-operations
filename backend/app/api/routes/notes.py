from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_business
from app.database.session import get_db
from app.models.business import Business
from app.schemas.note import NoteIn, NoteOut
from app.services import note_service

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("", response_model=list[NoteOut])
def list_notes(
    search: str | None = Query(default=None, max_length=120),
    category: str | None = Query(default=None, max_length=48),
    biz: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
) -> list[dict]:
    return note_service.list_notes(db, biz.id, search=search, category=category)


@router.post("", response_model=NoteOut, status_code=201)
def create_note(
    data: NoteIn,
    biz: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
) -> dict:
    return note_service.create_note(db, biz.id, data)


@router.put("/{note_id}", response_model=NoteOut)
def update_note(
    note_id: int,
    data: NoteIn,
    biz: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
) -> dict:
    return note_service.update_note(db, biz.id, note_id, data)


@router.delete("/{note_id}", status_code=204, response_class=Response)
def delete_note(
    note_id: int,
    biz: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
) -> Response:
    note_service.delete_note(db, biz.id, note_id)
    return Response(status_code=204)
