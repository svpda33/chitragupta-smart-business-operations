from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.api.deps import extract_session_token, get_current_business, get_current_user
from app.core.config import get_settings
from app.core.security import SESSION_COOKIE_NAME
from app.database.session import get_db
from app.models.business import Business
from app.models.user import User
from app.schemas.auth import (
    AuthMeOut,
    BusinessOnboardingIn,
    BusinessProfileOut,
    ForgotPasswordIn,
    LoginIn,
    RegisterIn,
)
from app.services import auth_service

router = APIRouter(tags=["auth"])


def _set_session_cookie(response: Response, raw_token: str, max_age: int) -> None:
    is_prod = get_settings().app_env.lower() == "production"
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=raw_token,
        httponly=True,
        samesite="lax",
        secure=is_prod,
        max_age=max_age,
        path="/",
    )


@router.post("/auth/register", response_model=AuthMeOut, status_code=201)
def register(data: RegisterIn, response: Response, db: Session = Depends(get_db)) -> dict:
    payload, raw_token, max_age = auth_service.register_user(db, data)
    _set_session_cookie(response, raw_token, max_age)
    return payload


@router.post("/auth/login", response_model=AuthMeOut)
def login(data: LoginIn, response: Response, db: Session = Depends(get_db)) -> dict:
    payload, raw_token, max_age = auth_service.login_user(db, data)
    _set_session_cookie(response, raw_token, max_age)
    return payload


@router.post("/auth/logout", status_code=204, response_class=Response)
def logout(request: Request, db: Session = Depends(get_db)) -> Response:
    token = extract_session_token(request)
    auth_service.logout_session(db, token)
    resp = Response(status_code=204)
    resp.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
    return resp


@router.get("/auth/me", response_model=AuthMeOut)
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    return auth_service.get_me(db, user)


@router.post("/auth/forgot-password")
def forgot_password(data: ForgotPasswordIn, db: Session = Depends(get_db)) -> dict:
    return auth_service.request_password_reset(db, data.email)


@router.post("/business/onboarding", response_model=BusinessProfileOut, status_code=201)
def complete_onboarding(
    data: BusinessOnboardingIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return auth_service.complete_onboarding(db, user, data)


@router.get("/business/profile", response_model=BusinessProfileOut)
def get_business_profile(biz: Business = Depends(get_current_business)) -> dict:
    return auth_service.serialize_business(biz)


@router.put("/business/profile", response_model=BusinessProfileOut)
def update_business_profile(
    data: BusinessOnboardingIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return auth_service.complete_onboarding(db, user, data)
