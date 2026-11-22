from typing import Any
from pydantic import BaseModel, Field


class CustomerDelayOption(BaseModel):
    customer_id: int
    customer_name: str
    outstanding_paise: int
    invoice_count: int


class InvoiceDelayOption(BaseModel):
    invoice_id: int
    invoice_number: str
    customer_id: int
    customer_name: str
    outstanding_paise: int
    due_date: Any


class CashFlowPoint(BaseModel):
    date: str
    day_label: str
    inflow_baseline_paise: int
    inflow_simulated_paise: int
    outflow_paise: int
    balance_baseline_paise: int
    balance_simulated_paise: int
    safety_threshold_paise: int
    is_below_safety_baseline: bool
    is_below_safety_simulated: bool


class CashFlowSimulationRequest(BaseModel):
    days: int = Field(default=30, ge=7, le=90)
    delay_days: int = Field(default=0, ge=0, le=90)
    delayed_customer_id: int | None = None
    delayed_invoice_id: int | None = None


class CashFlowForecastResponse(BaseModel):
    horizon_days: int
    delay_days: int
    delayed_customer_id: int | None
    delayed_customer_name: str | None
    delayed_invoice_id: int | None = None
    delayed_invoice_number: str | None = None

    starting_cash_paise: int
    baseline_ending_cash_paise: int
    simulated_ending_cash_paise: int
    total_expected_inflows_paise: int
    total_scheduled_outflows_paise: int

    baseline_min_balance_paise: int
    simulated_min_balance_paise: int
    safety_threshold_paise: int

    shortfall_detected: bool
    shortfall_date: str | None
    runway_days_baseline: int
    runway_days_simulated: int
    affected_expenses: list[dict[str, Any]] = []
    impact_explanation: str = ""

    timeline: list[CashFlowPoint]
    customers_with_receivables: list[CustomerDelayOption]
    pending_invoices: list[InvoiceDelayOption] = []
