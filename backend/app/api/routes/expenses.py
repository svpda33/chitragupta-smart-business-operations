from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_business
from app.database.session import get_db
from app.models.business import Business
from app.schemas.expense import ExpenseIn, ExpenseOut
from app.services import expense_service

router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.get("", response_model=list[ExpenseOut])
def get_expenses(
    biz: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
) -> list:
    return expense_service.list_expenses(db, business_id=biz.id)


@router.post("", response_model=ExpenseOut, status_code=201)
def create_expense(
    data: ExpenseIn,
    biz: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
):
    return expense_service.create_expense(db, data, business_id=biz.id)


@router.delete("/{expense_id}", status_code=204, response_class=Response)
def delete_expense(
    expense_id: int,
    biz: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
):
    expense_service.delete_expense(db, expense_id, business_id=biz.id)
    return Response(status_code=204)
