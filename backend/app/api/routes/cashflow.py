from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_business
from app.database.session import get_db
from app.models.business import Business
from app.schemas.cashflow import CashFlowForecastResponse, CashFlowSimulationRequest
from app.services import cashflow_service

router = APIRouter(prefix="/cashflow", tags=["cashflow"])


@router.get("/forecast", response_model=CashFlowForecastResponse)
def get_forecast(
    days: int = Query(default=30, ge=7, le=90),
    delay_days: int = Query(default=0, ge=0, le=90),
    delayed_customer_id: int | None = Query(default=None),
    delayed_invoice_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    business: Business = Depends(get_current_business),
) -> dict:
    return cashflow_service.calculate_cashflow_forecast(
        db,
        days=days,
        delay_days=delay_days,
        delayed_customer_id=delayed_customer_id,
        delayed_invoice_id=delayed_invoice_id,
        today=date.today(),
        business_id=business.id,
    )


@router.post("/simulate", response_model=CashFlowForecastResponse)
def simulate_forecast(
    body: CashFlowSimulationRequest,
    db: Session = Depends(get_db),
    business: Business = Depends(get_current_business),
) -> dict:
    return cashflow_service.calculate_cashflow_forecast(
        db,
        days=body.days,
        delay_days=body.delay_days,
        delayed_customer_id=body.delayed_customer_id,
        delayed_invoice_id=body.delayed_invoice_id,
        today=date.today(),
        business_id=business.id,
    )
