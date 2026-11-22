from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.expense import Expense
from app.schemas.expense import ExpenseIn


def list_expenses(db: Session, business_id: int | None = None) -> list[Expense]:
    stmt = select(Expense)
    if business_id is not None:
        stmt = stmt.where(Expense.business_id == business_id)
    stmt = stmt.order_by(Expense.expense_date.asc(), Expense.id.asc())
    return list(db.scalars(stmt).all())


def create_expense(db: Session, data: ExpenseIn, business_id: int | None = None) -> Expense:
    amount_paise = data.amount_paise()
    record = Expense(
        business_id=business_id,
        name=data.name,
        category=data.category,
        amount_paise=amount_paise,
        expense_date=data.expense_date,
        is_recurring=data.is_recurring,
        day_of_month=data.day_of_month or data.expense_date.day,
        notes=data.notes,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def delete_expense(db: Session, expense_id: int, business_id: int | None = None) -> None:
    stmt = select(Expense).where(Expense.id == expense_id)
    if business_id is not None:
        stmt = stmt.where(Expense.business_id == business_id)
    record = db.scalar(stmt.limit(1))
    if not record:
        raise AppError(404, "Expense not found.")
    db.delete(record)
    db.commit()
