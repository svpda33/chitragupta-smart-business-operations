from datetime import date
from typing import Any
from pydantic import BaseModel


class AgeingBucket(BaseModel):
    label: str
    count: int
    amount_paise: int


class StatusCount(BaseModel):
    status: str
    label: str
    count: int
    amount_paise: int


class DashboardAlert(BaseModel):
    id: str
    type: str  # danger, warning, info, success
    priority: str  # high, medium, low
    title: str
    message: str
    entity_type: str | None = None  # customer, invoice, expense, cashflow
    entity_name: str | None = None
    amount_paise: int | None = None
    date: str | None = None
    action_label: str | None = None
    action_url: str | None = None


class DashboardSummary(BaseModel):
    total_outstanding_paise: int
    total_overdue_paise: int
    overdue_invoices_count: int
    pending_invoices_count: int
    paid_invoices_count: int
    draft_invoices_count: int

    cash_on_hand_paise: int
    safety_cash_threshold_paise: int
    runway_days: int

    total_invoiced_month_paise: int
    total_collected_month_paise: int
    total_invoiced_all_time_paise: int
    total_collected_all_time_paise: int
    collection_efficiency_percent: float

    status_distribution: list[StatusCount]
    ageing_breakdown: list[AgeingBucket]
    actionable_alerts: list[DashboardAlert]
    recent_invoices: list[dict[str, Any]]
    recent_payments: list[dict[str, Any]]
