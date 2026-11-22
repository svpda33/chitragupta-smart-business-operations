import json
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.business import Business
from app.models.setting import Setting
from app.schemas.setting import SettingIn
from app.utils.money import rupees_to_paise


DEFAULT_EXPENSES = [
    {"name": "Office Rent & Workspace", "amount_paise": 2500000, "day_of_month": 5},
    {"name": "Software Subscriptions & Cloud", "amount_paise": 1000000, "day_of_month": 10},
    {"name": "Contractor / Assistant Stipend", "amount_paise": 2000000, "day_of_month": 1},
    {"name": "High-Speed Internet & Utilities", "amount_paise": 1000000, "day_of_month": 15},
]


def get_or_create_settings(db: Session, business_id: int | None = None) -> Setting:
    stmt = select(Setting)
    if business_id is not None:
        stmt = stmt.where(Setting.business_id == business_id)
    stmt = stmt.limit(1)
    record = db.execute(stmt).scalar_one_or_none()
    if not record:
        biz = db.get(Business, business_id) if business_id is not None else None
        if biz is not None:
            record = Setting(
                business_id=biz.id,
                business_name=biz.name,
                owner_name=biz.owner_name,
                email=biz.email,
                phone=biz.phone,
                address=biz.address,
                gstin=biz.gstin,
                upi_id=biz.upi_id,
                bank_name=biz.bank_name,
                bank_account=biz.bank_account,
                bank_ifsc=biz.bank_ifsc,
                default_payment_terms_days=biz.default_payment_terms_days,
                default_tax_percent=biz.default_tax_percent,
                initial_cash_balance_paise=biz.initial_cash_balance_paise,
                monthly_recurring_expenses_paise=biz.monthly_recurring_expenses_paise,
                safety_cash_threshold_paise=biz.safety_cash_threshold_paise,
                expenses_json="[]",
            )
        else:
            record = Setting(
                business_id=business_id,
                business_name="My Business",
                owner_name="Business Owner",
                email=None,
                phone=None,
                address=None,
                gstin=None,
                upi_id=None,
                bank_name=None,
                bank_account=None,
                bank_ifsc=None,
                default_payment_terms_days=15,
                default_tax_percent=18,
                initial_cash_balance_paise=0,
                monthly_recurring_expenses_paise=0,
                safety_cash_threshold_paise=5000000,
                expenses_json="[]",
            )
        db.add(record)
        db.commit()
        db.refresh(record)
    return record


def get_settings_out(db: Session, business_id: int | None = None) -> dict:
    record = get_or_create_settings(db, business_id=business_id)
    biz = db.get(Business, business_id) if business_id is not None else None
    return _to_dict(record, biz)


def update_settings(db: Session, data: SettingIn, business_id: int | None = None) -> dict:
    record = get_or_create_settings(db, business_id=business_id)

    record.business_name = data.business_name
    record.owner_name = data.owner_name
    record.email = data.email
    record.phone = data.phone
    record.address = data.address
    record.gstin = data.gstin
    record.upi_id = data.upi_id
    record.bank_name = data.bank_name
    record.bank_account = data.bank_account
    record.bank_ifsc = data.bank_ifsc

    record.default_payment_terms_days = data.default_payment_terms_days
    record.default_tax_percent = data.default_tax_percent

    record.initial_cash_balance_paise = data.get_initial_cash_paise()
    record.monthly_recurring_expenses_paise = data.get_monthly_expenses_paise()
    record.safety_cash_threshold_paise = data.get_safety_threshold_paise()

    if data.expenses:
        expenses_list = [
            {
                "name": exp.name,
                "amount_paise": exp.get_amount_paise(),
                "day_of_month": exp.day_of_month,
            }
            for exp in data.expenses
        ]
        # auto-sync monthly recurring expenses to sum of breakdown if provided
        record.expenses_json = json.dumps(expenses_list)
        sum_expenses = sum(item["amount_paise"] for item in expenses_list)
        if sum_expenses > 0:
            record.monthly_recurring_expenses_paise = sum_expenses
    elif data.expenses is not None and len(data.expenses) == 0:
        pass

    biz = db.get(Business, business_id) if business_id is not None else None
    if biz is not None:
        biz.name = data.business_name
        biz.owner_name = data.owner_name
        if data.category is not None:
            biz.category = data.category
        if data.description is not None:
            biz.description = data.description
        if data.currency:
            biz.currency = data.currency
        if data.allow_negative_stock is not None:
            biz.allow_negative_stock = data.allow_negative_stock
        biz.email = data.email
        biz.phone = data.phone
        biz.address = data.address
        biz.gstin = data.gstin
        biz.upi_id = data.upi_id
        biz.bank_name = data.bank_name
        biz.bank_account = data.bank_account
        biz.bank_ifsc = data.bank_ifsc
        biz.default_payment_terms_days = data.default_payment_terms_days
        biz.default_tax_percent = data.default_tax_percent
        biz.initial_cash_balance_paise = record.initial_cash_balance_paise
        biz.monthly_recurring_expenses_paise = record.monthly_recurring_expenses_paise
        biz.safety_cash_threshold_paise = record.safety_cash_threshold_paise

    db.commit()
    db.refresh(record)
    if biz is not None:
        db.refresh(biz)
    return _to_dict(record, biz)


def _to_dict(record: Setting, biz: Business | None = None) -> dict:
    return {
        "business_name": record.business_name,
        "owner_name": record.owner_name,
        "category": biz.category if biz else None,
        "description": biz.description if biz else None,
        "logo_url": biz.logo_url if biz else None,
        "currency": biz.currency if biz else "INR",
        "allow_negative_stock": biz.allow_negative_stock if biz else False,
        "email": record.email,
        "phone": record.phone,
        "address": record.address,
        "gstin": record.gstin,
        "upi_id": record.upi_id,
        "bank_name": record.bank_name,
        "bank_account": record.bank_account,
        "bank_ifsc": record.bank_ifsc,
        "default_payment_terms_days": record.default_payment_terms_days,
        "default_tax_percent": record.default_tax_percent,
        "initial_cash_balance_paise": record.initial_cash_balance_paise,
        "monthly_recurring_expenses_paise": record.monthly_recurring_expenses_paise,
        "safety_cash_threshold_paise": record.safety_cash_threshold_paise,
        "expenses": record.get_expenses(),
        "updated_at": record.updated_at,
    }
