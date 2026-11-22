from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_business
from app.database.session import get_db
from app.models.business import Business
from app.schemas.setting import SettingIn, SettingOut
from app.services import setting_service

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingOut)
def get_settings(
    db: Session = Depends(get_db),
    business: Business = Depends(get_current_business),
) -> dict:
    return setting_service.get_settings_out(db, business_id=business.id)


@router.put("", response_model=SettingOut)
def update_settings(
    data: SettingIn,
    db: Session = Depends(get_db),
    business: Business = Depends(get_current_business),
) -> dict:
    return setting_service.update_settings(db, data, business_id=business.id)
