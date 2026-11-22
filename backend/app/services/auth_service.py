"""Authentication, session management, and business onboarding service."""

from datetime import timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import (
    generate_session_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.business import Business
from app.models.setting import Setting
from app.models.user import PasswordResetToken, User, UserSession
from app.schemas.auth import BusinessOnboardingIn, LoginIn, RegisterIn
from app.utils.dates import now_utc

SHORT_SESSION_DAYS = 1
REMEMBER_SESSION_DAYS = 14


def _serialize_user(user: User) -> dict[str, Any]:
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "created_at": user.created_at,
    }


def serialize_business(biz: Business | None) -> dict[str, Any] | None:
    if biz is None:
        return None
    return {
        "id": biz.id,
        "name": biz.name,
        "category": biz.category,
        "description": biz.description,
        "logo_url": biz.logo_url,
        "owner_name": biz.owner_name,
        "email": biz.email,
        "phone": biz.phone,
        "address": biz.address,
        "gstin": biz.gstin,
        "currency": biz.currency,
        "upi_id": biz.upi_id,
        "bank_name": biz.bank_name,
        "bank_account": biz.bank_account,
        "bank_ifsc": biz.bank_ifsc,
        "default_payment_terms_days": biz.default_payment_terms_days,
        "default_tax_percent": biz.default_tax_percent,
        "initial_cash_balance_paise": biz.initial_cash_balance_paise,
        "monthly_recurring_expenses_paise": biz.monthly_recurring_expenses_paise,
        "safety_cash_threshold_paise": biz.safety_cash_threshold_paise,
        "allow_negative_stock": biz.allow_negative_stock,
        "onboarding_completed": biz.onboarding_completed,
        "created_at": biz.created_at,
        "updated_at": biz.updated_at,
    }


def get_primary_business(db: Session, user_id: int) -> Business | None:
    return db.scalar(
        select(Business).where(Business.owner_user_id == user_id).order_by(Business.id.asc()).limit(1)
    )


def _sync_business_to_setting(db: Session, biz: Business) -> Setting:
    setting = db.scalar(select(Setting).where(Setting.business_id == biz.id).limit(1))
    if setting is None:
        setting = Setting(business_id=biz.id)
        db.add(setting)
    setting.business_name = biz.name
    setting.owner_name = biz.owner_name
    setting.email = biz.email
    setting.phone = biz.phone
    setting.address = biz.address
    setting.gstin = biz.gstin
    setting.upi_id = biz.upi_id
    setting.bank_name = biz.bank_name
    setting.bank_account = biz.bank_account
    setting.bank_ifsc = biz.bank_ifsc
    setting.default_payment_terms_days = biz.default_payment_terms_days
    setting.default_tax_percent = biz.default_tax_percent
    setting.initial_cash_balance_paise = biz.initial_cash_balance_paise
    setting.monthly_recurring_expenses_paise = biz.monthly_recurring_expenses_paise
    setting.safety_cash_threshold_paise = biz.safety_cash_threshold_paise
    return setting


def _create_session(db: Session, user: User, remember_me: bool = True) -> tuple[str, int]:
    raw_token = generate_session_token()
    days = REMEMBER_SESSION_DAYS if remember_me else SHORT_SESSION_DAYS
    expires_at = now_utc() + timedelta(days=days)
    session = UserSession(
        user_id=user.id,
        token_hash=hash_token(raw_token),
        expires_at=expires_at,
    )
    db.add(session)
    db.commit()
    return raw_token, days * 86400


def register_user(db: Session, data: RegisterIn) -> tuple[dict[str, Any], str, int]:
    if data.password != data.confirm_password:
        raise AppError(422, "Passwords do not match.", field="confirm_password")

    existing = db.scalar(select(User.id).where(User.email == data.email).limit(1))
    if existing is not None:
        raise AppError(409, "An account with this email already exists.", field="email")

    user = User(
        full_name=data.full_name,
        email=data.email,
        password_hash=hash_password(data.password),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    raw_token, max_age = _create_session(db, user, remember_me=True)
    payload = {
        "user": _serialize_user(user),
        "business": None,
        "onboarding_completed": False,
    }
    return payload, raw_token, max_age


def login_user(db: Session, data: LoginIn) -> tuple[dict[str, Any], str, int]:
    user = db.scalar(select(User).where(User.email == data.email).limit(1))
    if user is None or not user.is_active or not verify_password(data.password, user.password_hash):
        raise AppError(401, "Invalid email or password.")

    raw_token, max_age = _create_session(db, user, remember_me=data.remember_me)
    biz = get_primary_business(db, user.id)
    payload = {
        "user": _serialize_user(user),
        "business": serialize_business(biz),
        "onboarding_completed": bool(biz and biz.onboarding_completed),
    }
    return payload, raw_token, max_age


def logout_session(db: Session, raw_token: str | None) -> None:
    if not raw_token:
        return
    token_h = hash_token(raw_token)
    sess = db.scalar(select(UserSession).where(UserSession.token_hash == token_h).limit(1))
    if sess is not None:
        db.delete(sess)
        db.commit()


def get_user_by_token(db: Session, raw_token: str | None) -> User | None:
    if not raw_token:
        return None
    token_h = hash_token(raw_token)
    sess = db.scalar(select(UserSession).where(UserSession.token_hash == token_h).limit(1))
    if sess is None:
        return None
    now = now_utc()
    exp = sess.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=now.tzinfo)
    if exp < now:
        db.delete(sess)
        db.commit()
        return None
    user = db.get(User, sess.user_id)
    if user is None or not user.is_active:
        return None
    return user


def get_me(db: Session, user: User) -> dict[str, Any]:
    biz = get_primary_business(db, user.id)
    return {
        "user": _serialize_user(user),
        "business": serialize_business(biz),
        "onboarding_completed": bool(biz and biz.onboarding_completed),
    }


def request_password_reset(db: Session, email: str) -> dict[str, Any]:
    user = db.scalar(select(User).where(User.email == email).limit(1))
    if user is not None:
        raw_token = generate_session_token()
        reset_row = PasswordResetToken(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            expires_at=now_utc() + timedelta(hours=1),
        )
        db.add(reset_row)
        db.commit()
    return {
        "status": "recorded",
        "email_dispatched": False,
        "message": (
            "If an account exists for that email, a reset token was recorded. "
            "No SMTP email provider is configured in this environment yet — configure SMTP credentials in backend/.env to enable automated reset emails."
        ),
    }


def complete_onboarding(db: Session, user: User, data: BusinessOnboardingIn) -> dict[str, Any]:
    biz = get_primary_business(db, user.id)
    if biz is None:
        biz = Business(
            owner_user_id=user.id,
            name=data.name,
            owner_name=data.owner_name or user.full_name,
        )
        db.add(biz)

    biz.name = data.name
    biz.category = data.category or "Services & Consulting"
    biz.description = data.description
    biz.owner_name = data.owner_name or user.full_name
    biz.email = data.email or user.email
    biz.phone = data.phone
    biz.address = data.address
    biz.gstin = data.gstin
    biz.currency = data.currency or "INR"
    biz.upi_id = data.upi_id
    biz.bank_name = data.bank_name
    biz.bank_account = data.bank_account
    biz.bank_ifsc = data.bank_ifsc
    biz.default_payment_terms_days = data.default_payment_terms_days
    biz.default_tax_percent = data.default_tax_percent
    if data.initial_cash_balance is not None and str(data.initial_cash_balance).strip() != "":
        biz.initial_cash_balance_paise = data.get_initial_cash_paise()
    if data.safety_cash_threshold is not None and str(data.safety_cash_threshold).strip() != "":
        biz.safety_cash_threshold_paise = data.get_safety_threshold_paise()
    biz.allow_negative_stock = data.allow_negative_stock
    biz.onboarding_completed = True

    db.flush()
    _sync_business_to_setting(db, biz)
    db.commit()
    db.refresh(biz)
    return serialize_business(biz)
