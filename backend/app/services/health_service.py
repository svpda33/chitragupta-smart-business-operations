from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.schemas.health import HealthResponse

APP_VERSION = "0.1.0"


def get_health_status(db: Session) -> str:
    try:
        db.execute(text("SELECT 1"))
        return "ok"
    except SQLAlchemyError:
        return "error"


def build_health_response(db: Session, settings: Settings) -> HealthResponse:
    return HealthResponse(
        status="ok",
        app="Chitragupta",
        environment=settings.app_env,
        database=get_health_status(db),
        version=APP_VERSION,
    )
