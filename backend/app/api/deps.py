"""FastAPI authentication and multi-business authorization dependencies."""

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import SESSION_COOKIE_NAME
from app.database.session import get_db
from app.models.business import Business
from app.models.user import User
from app.services import auth_service


def extract_session_token(request: Request) -> str | None:
    cookie_token = request.cookies.get(SESSION_COOKIE_NAME)
    if cookie_token:
        return cookie_token
    auth_header = request.headers.get("Authorization") or ""
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip() or None
    return None


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = extract_session_token(request)
    user = auth_service.get_user_by_token(db, token)
    if user is None:
        raise AppError(401, "Authentication required. Please sign in to continue.")
    return user


def get_current_business(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Business:
    biz = auth_service.get_primary_business(db, user.id)
    if biz is None:
        raise AppError(
            403,
            "Business profile not set up yet. Complete onboarding to access workspace data.",
        )
    return biz
