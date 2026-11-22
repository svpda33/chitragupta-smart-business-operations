from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_business
from app.database.session import get_db
from app.models.business import Business
from app.services import demo_service

router = APIRouter(prefix="/demo", tags=["demo"])


@router.post("/seed")
def seed_demo(
    force: bool = Query(default=False),
    db: Session = Depends(get_db),
    business: Business = Depends(get_current_business),
) -> dict:
    return demo_service.seed_synthetic_demo_data(
        db, today=date.today(), force=force, business_id=business.id
    )
