"""Controlled, read-only financial tools exposed to the Gemini Finance Copilot.

Rules enforced here:
- All monetary math is performed by existing Python services in integer paise.
- Strict read-only access: no tool mutates database state.
- Sensitive personal and banking information (bank account numbers, IFSC, UPI IDs,
  GSTIN, emails, phone numbers, street addresses) is never sent to the AI model.
"""

from datetime import date, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.services import (
    cashflow_service,
    customer_service,
    dashboard_service,
    expense_service,
    inventory_service,
    invoice_service,
    payment_service,
    reminder_service,
    setting_service,
)
from app.utils.money import paise_to_rupees_text


def _rs(paise: int) -> str:
    return f"₹{paise_to_rupees_text(paise)}"


def _redact_sensitive_payment_details(text: str, settings) -> str:
    """Ensure raw bank account numbers, IFSC, UPI IDs, and phone numbers are never sent to Gemini."""
    redacted = text
    for secret_val, placeholder in [
        (settings.bank_account, "[Bank Account from Settings]"),
        (settings.bank_ifsc, "[IFSC from Settings]"),
        (settings.upi_id, "[UPI ID from Settings]"),
        (settings.phone, "[Business Phone from Settings]"),
        (settings.email, "[Business Email from Settings]"),
        (settings.gstin, "[GSTIN from Settings]"),
    ]:
        if secret_val and secret_val.strip():
            redacted = redacted.replace(secret_val.strip(), placeholder)
    return redacted


def _resolve_customer(
    db: Session, customer_query: str | None, business_id: int | None = None
) -> dict | None:
    if not customer_query:
        return None
    q = str(customer_query).strip()
    if not q:
        return None
    if q.isdigit():
        try:
            return customer_service.get_customer(db, int(q), business_id=business_id)
        except Exception:
            pass
    items, _ = customer_service.list_customers(
        db, search=q, page=1, page_size=20, business_id=business_id
    )
    if items:
        for item in items:
            if item["name"].lower() == q.lower():
                return item
        return items[0]
    all_items, _ = customer_service.list_customers(
        db, page=1, page_size=100, business_id=business_id
    )
    for item in all_items:
        if q.lower() in item["name"].lower():
            return item
    return None


def _resolve_invoice(
    db: Session, invoice_query: str | None, today: date, business_id: int | None = None
) -> dict | None:
    if not invoice_query:
        return None
    q = str(invoice_query).strip()
    if not q:
        return None
    if q.isdigit():
        try:
            return invoice_service.get_invoice_detail(
                db, int(q), today=today, business_id=business_id
            )
        except Exception:
            pass
    items, _ = invoice_service.list_invoices(
        db, search=q, page=1, page_size=20, today=today, business_id=business_id
    )
    if items:
        for item in items:
            if item["invoice_number"].lower() == q.lower():
                return invoice_service.get_invoice_detail(
                    db, item["id"], today=today, business_id=business_id
                )
        return invoice_service.get_invoice_detail(
            db, items[0]["id"], today=today, business_id=business_id
        )
    return None


# ---------------------------------------------------------------------------
# Tool Implementations (Read-Only)
# ---------------------------------------------------------------------------

def get_financial_overview(
    db: Session, today: date, business_id: int | None = None
) -> dict[str, Any]:
    summary = dashboard_service.get_dashboard_summary(db, today=today, business_id=business_id)
    return {
        "as_of_date": today.isoformat(),
        "data_type": "actual_ledger_metrics",
        "total_outstanding": _rs(summary["total_outstanding_paise"]),
        "total_outstanding_paise": summary["total_outstanding_paise"],
        "total_overdue": _rs(summary["total_overdue_paise"]),
        "total_overdue_paise": summary["total_overdue_paise"],
        "overdue_invoices_count": summary["overdue_invoices_count"],
        "pending_invoices_count": summary["pending_invoices_count"],
        "paid_invoices_count": summary["paid_invoices_count"],
        "draft_invoices_count": summary["draft_invoices_count"],
        "estimated_cash_on_hand": _rs(summary["cash_on_hand_paise"]),
        "cash_on_hand_paise": summary["cash_on_hand_paise"],
        "safety_cash_threshold": _rs(summary["safety_cash_threshold_paise"]),
        "safety_cash_threshold_paise": summary["safety_cash_threshold_paise"],
        "estimated_runway_days": summary["runway_days"],
        "invoiced_this_month": _rs(summary["total_invoiced_month_paise"]),
        "collected_this_month": _rs(summary["total_collected_month_paise"]),
        "invoiced_all_time": _rs(summary["total_invoiced_all_time_paise"]),
        "collected_all_time": _rs(summary["total_collected_all_time_paise"]),
        "collection_efficiency_percent": summary["collection_efficiency_percent"],
        "ageing_breakdown": [
            {
                "bucket": b["label"],
                "invoice_count": b["count"],
                "amount": _rs(b["amount_paise"]),
            }
            for b in summary["ageing_breakdown"]
        ],
        "active_alerts": [
            {
                "priority": a["priority"],
                "type": a["type"],
                "title": a["title"],
                "message": a["message"],
                "date": a["date"],
            }
            for a in summary["actionable_alerts"]
        ],
    }


def get_top_debtors(
    db: Session, today: date, limit: int = 5, business_id: int | None = None
) -> dict[str, Any]:
    limit = max(1, min(int(limit or 5), 20))
    customers, _ = customer_service.list_customers(
        db, page=1, page_size=100, business_id=business_id
    )
    total_outstanding = sum(c["outstanding_paise"] for c in customers)

    debtors = [c for c in customers if c["outstanding_paise"] > 0]
    debtors.sort(key=lambda c: c["outstanding_paise"], reverse=True)

    rows = []
    for c in debtors[:limit]:
        share = round((c["outstanding_paise"] / total_outstanding) * 100, 1) if total_outstanding > 0 else 0.0
        rows.append({
            "customer_id": c["id"],
            "customer_name": c["name"],
            "invoice_count": c["invoice_count"],
            "total_invoiced": _rs(c["total_invoiced_paise"]),
            "total_paid": _rs(c["total_paid_paise"]),
            "outstanding": _rs(c["outstanding_paise"]),
            "outstanding_paise": c["outstanding_paise"],
            "overdue": _rs(c["overdue_paise"]),
            "overdue_paise": c["overdue_paise"],
            "concentration_percent": share,
        })

    return {
        "as_of_date": today.isoformat(),
        "data_type": "actual_ledger_metrics",
        "total_outstanding_all_customers": _rs(total_outstanding),
        "debtors_count": len(debtors),
        "top_debtors": rows,
    }


def get_overdue_invoices(
    db: Session, today: date, business_id: int | None = None
) -> dict[str, Any]:
    items, total = invoice_service.list_invoices(
        db, status="overdue", page=1, page_size=100, today=today, business_id=business_id
    )
    items.sort(key=lambda x: (-x["days_overdue"], -x["outstanding_paise"]))
    total_overdue_paise = sum(i["outstanding_paise"] for i in items)

    return {
        "as_of_date": today.isoformat(),
        "data_type": "actual_ledger_metrics",
        "overdue_count": total,
        "total_overdue": _rs(total_overdue_paise),
        "total_overdue_paise": total_overdue_paise,
        "invoices": [
            {
                "invoice_id": i["id"],
                "invoice_number": i["invoice_number"],
                "customer_name": i["customer_name"],
                "description": i["description"],
                "due_date": i["due_date"].isoformat() if hasattr(i["due_date"], "isoformat") else str(i["due_date"]),
                "days_overdue": i["days_overdue"],
                "total": _rs(i["total_paise"]),
                "paid": _rs(i["paid_paise"]),
                "outstanding": _rs(i["outstanding_paise"]),
                "outstanding_paise": i["outstanding_paise"],
            }
            for i in items
        ],
    }


def get_customer_summary(
    db: Session, today: date, customer_query: str, business_id: int | None = None
) -> dict[str, Any]:
    cust = _resolve_customer(db, customer_query, business_id=business_id)
    if not cust:
        return {
            "found": False,
            "as_of_date": today.isoformat(),
            "message": f"No customer matched '{customer_query}'.",
        }

    invs, _ = invoice_service.list_invoices(
        db, customer_id=cust["id"], page=1, page_size=50, today=today, business_id=business_id
    )
    pmts, _ = payment_service.list_payments(
        db, customer_id=cust["id"], page=1, page_size=50, business_id=business_id
    )

    return {
        "found": True,
        "as_of_date": today.isoformat(),
        "data_type": "actual_ledger_metrics",
        "customer_id": cust["id"],
        "customer_name": cust["name"],
        "invoice_count": cust["invoice_count"],
        "total_invoiced": _rs(cust["total_invoiced_paise"]),
        "total_paid": _rs(cust["total_paid_paise"]),
        "outstanding": _rs(cust["outstanding_paise"]),
        "overdue": _rs(cust["overdue_paise"]),
        "invoices": [
            {
                "invoice_number": i["invoice_number"],
                "status": i["status"],
                "due_date": i["due_date"].isoformat() if hasattr(i["due_date"], "isoformat") else str(i["due_date"]),
                "days_overdue": i["days_overdue"],
                "total": _rs(i["total_paise"]),
                "paid": _rs(i["paid_paise"]),
                "outstanding": _rs(i["outstanding_paise"]),
            }
            for i in invs
        ],
        "recent_payments": [
            {
                "invoice_number": p["invoice_number"],
                "payment_date": p["payment_date"].isoformat() if hasattr(p["payment_date"], "isoformat") else str(p["payment_date"]),
                "amount": _rs(p["amount_paise"]),
                "method": p["method"],
                "status": p["status"],
            }
            for p in pmts[:10]
        ],
    }


def get_invoice_details(
    db: Session, today: date, invoice_query: str, business_id: int | None = None
) -> dict[str, Any]:
    inv = _resolve_invoice(db, invoice_query, today=today, business_id=business_id)
    if not inv:
        return {
            "found": False,
            "as_of_date": today.isoformat(),
            "message": f"No invoice matched '{invoice_query}'.",
        }

    return {
        "found": True,
        "as_of_date": today.isoformat(),
        "data_type": "actual_ledger_metrics",
        "invoice_id": inv["id"],
        "invoice_number": inv["invoice_number"],
        "customer_name": inv["customer_name"],
        "description": inv["description"],
        "lifecycle": inv["lifecycle"],
        "status": inv["status"],
        "invoice_date": inv["invoice_date"].isoformat() if hasattr(inv["invoice_date"], "isoformat") else str(inv["invoice_date"]),
        "due_date": inv["due_date"].isoformat() if hasattr(inv["due_date"], "isoformat") else str(inv["due_date"]),
        "days_overdue": inv["days_overdue"],
        "subtotal": _rs(inv["subtotal_paise"]),
        "tax_percent": inv["tax_percent"],
        "tax": _rs(inv["tax_paise"]),
        "total": _rs(inv["total_paise"]),
        "paid": _rs(inv["paid_paise"]),
        "outstanding": _rs(inv["outstanding_paise"]),
        "items": [
            {
                "description": it["description"],
                "quantity": it["quantity"],
                "unit_price": _rs(it["unit_price_paise"]),
                "line_total": _rs(it["line_total_paise"]),
            }
            for it in inv["items"]
        ],
        "payments": [
            {
                "payment_date": p["payment_date"].isoformat() if hasattr(p["payment_date"], "isoformat") else str(p["payment_date"]),
                "amount": _rs(p["amount_paise"]),
                "method": p["method"],
                "status": p["status"],
            }
            for p in inv["payments"]
        ],
    }


def get_cashflow_forecast(
    db: Session, today: date, days: int = 30, business_id: int | None = None
) -> dict[str, Any]:
    days = int(days or 30)
    if days not in (30, 60, 90):
        days = 30 if days < 45 else (60 if days < 75 else 90)

    fc = cashflow_service.calculate_cashflow_forecast(
        db, days=days, today=today, business_id=business_id
    )
    return {
        "as_of_date": today.isoformat(),
        "data_type": "forecast_estimate",
        "note": "Forecast figures are estimates based on unpaid invoice due dates and scheduled expenses, not guaranteed cash.",
        "horizon_days": fc["horizon_days"],
        "starting_cash": _rs(fc["starting_cash_paise"]),
        "starting_cash_paise": fc["starting_cash_paise"],
        "expected_inflows": _rs(fc["total_expected_inflows_paise"]),
        "scheduled_outflows": _rs(fc["total_scheduled_outflows_paise"]),
        "projected_ending_cash": _rs(fc["baseline_ending_cash_paise"]),
        "projected_ending_cash_paise": fc["baseline_ending_cash_paise"],
        "projected_min_balance": _rs(fc["baseline_min_balance_paise"]),
        "projected_min_balance_paise": fc["baseline_min_balance_paise"],
        "safety_reserve_threshold": _rs(fc["safety_threshold_paise"]),
        "shortfall_detected": fc["shortfall_detected"],
        "shortfall_date": fc["shortfall_date"],
        "estimated_runway_days": fc["runway_days_baseline"],
        "headroom_above_safety_reserve": _rs(fc["baseline_min_balance_paise"] - fc["safety_threshold_paise"]),
        "impact_summary": fc["impact_explanation"],
    }


def simulate_payment_delay(
    db: Session,
    today: date,
    delay_days: int = 15,
    customer_query: str | None = None,
    invoice_query: str | None = None,
    days: int = 30,
    business_id: int | None = None,
) -> dict[str, Any]:
    delay_days = max(1, min(int(delay_days or 15), 90))
    days = int(days or 30)
    if days not in (30, 60, 90):
        days = 30 if days < 45 else (60 if days < 75 else 90)

    delayed_customer_id = None
    delayed_invoice_id = None

    if invoice_query:
        inv = _resolve_invoice(db, invoice_query, today=today, business_id=business_id)
        if inv:
            delayed_invoice_id = inv["id"]
    elif customer_query:
        cust = _resolve_customer(db, customer_query, business_id=business_id)
        if cust:
            delayed_customer_id = cust["id"]
    else:
        # If user asks "my biggest customer" without naming them, pick top debtor automatically
        customers, _ = customer_service.list_customers(
            db, page=1, page_size=100, business_id=business_id
        )
        debtors = [c for c in customers if c["outstanding_paise"] > 0]
        if debtors:
            debtors.sort(key=lambda c: c["outstanding_paise"], reverse=True)
            delayed_customer_id = debtors[0]["id"]

    sim = cashflow_service.calculate_cashflow_forecast(
        db,
        days=days,
        delay_days=delay_days,
        delayed_customer_id=delayed_customer_id,
        delayed_invoice_id=delayed_invoice_id,
        today=today,
        business_id=business_id,
    )

    ending_diff = sim["simulated_ending_cash_paise"] - sim["baseline_ending_cash_paise"]
    min_diff = sim["simulated_min_balance_paise"] - sim["baseline_min_balance_paise"]

    return {
        "as_of_date": today.isoformat(),
        "data_type": "what_if_simulation",
        "records_modified": False,
        "horizon_days": sim["horizon_days"],
        "delay_days": sim["delay_days"],
        "target_customer": sim["delayed_customer_name"],
        "target_invoice": sim["delayed_invoice_number"],
        "baseline_ending_cash": _rs(sim["baseline_ending_cash_paise"]),
        "simulated_ending_cash": _rs(sim["simulated_ending_cash_paise"]),
        "ending_cash_difference": _rs(ending_diff),
        "baseline_min_balance": _rs(sim["baseline_min_balance_paise"]),
        "simulated_min_balance": _rs(sim["simulated_min_balance_paise"]),
        "min_balance_difference": _rs(min_diff),
        "safety_reserve_threshold": _rs(sim["safety_threshold_paise"]),
        "shortfall_detected": sim["shortfall_detected"],
        "shortfall_date": sim["shortfall_date"],
        "runway_days_baseline": sim["runway_days_baseline"],
        "runway_days_simulated": sim["runway_days_simulated"],
        "affected_expenses": [
            {"name": e["name"], "date": e["date"], "amount": _rs(e["amount_paise"])}
            for e in sim["affected_expenses"]
        ],
        "impact_explanation": sim["impact_explanation"],
    }


def get_upcoming_expenses(
    db: Session, today: date, days: int = 30, business_id: int | None = None
) -> dict[str, Any]:
    days = max(1, min(int(days or 30), 90))
    db_expenses = expense_service.list_expenses(db, business_id=business_id)
    db_recurring = [e for e in db_expenses if e.is_recurring]
    db_oneoff = [e for e in db_expenses if not e.is_recurring]
    settings = setting_service.get_or_create_settings(db, business_id=business_id)
    settings_expenses = settings.get_expenses()

    occurrences = []
    total_paise = 0

    for offset in range(days + 1):
        cur_date = today + timedelta(days=offset)
        if db_recurring:
            for exp in db_recurring:
                if cur_date.day == exp.day_of_month:
                    total_paise += exp.amount_paise
                    occurrences.append({
                        "date": cur_date.isoformat(),
                        "name": exp.name,
                        "category": exp.category,
                        "amount": _rs(exp.amount_paise),
                        "is_recurring": True,
                    })
        elif settings_expenses:
            for exp in settings_expenses:
                if cur_date.day == exp.get("day_of_month", 1):
                    amt = exp.get("amount_paise", 0)
                    total_paise += amt
                    occurrences.append({
                        "date": cur_date.isoformat(),
                        "name": exp.get("name", "Recurring Expense"),
                        "category": "Recurring",
                        "amount": _rs(amt),
                        "is_recurring": True,
                    })
        for exp in db_oneoff:
            if exp.expense_date == cur_date:
                total_paise += exp.amount_paise
                occurrences.append({
                    "date": cur_date.isoformat(),
                    "name": exp.name,
                    "category": exp.category,
                    "amount": _rs(exp.amount_paise),
                    "is_recurring": False,
                })

    return {
        "as_of_date": today.isoformat(),
        "horizon_days": days,
        "total_upcoming_expenses": _rs(total_paise),
        "total_upcoming_expenses_paise": total_paise,
        "count": len(occurrences),
        "expenses": occurrences[:25],
    }


def generate_payment_reminder(
    db: Session,
    today: date,
    invoice_query: str,
    channel: str = "whatsapp",
    business_id: int | None = None,
) -> dict[str, Any]:
    channel = (channel or "whatsapp").strip().lower()
    if channel not in ("whatsapp", "email", "sms"):
        channel = "whatsapp"

    inv = _resolve_invoice(db, invoice_query, today=today, business_id=business_id)
    if not inv:
        return {
            "found": False,
            "as_of_date": today.isoformat(),
            "message": f"No invoice matched '{invoice_query}'.",
        }

    if inv["outstanding_paise"] <= 0:
        return {
            "found": True,
            "as_of_date": today.isoformat(),
            "invoice_number": inv["invoice_number"],
            "message": f"Invoice {inv['invoice_number']} has no outstanding balance to remind.",
        }

    settings = setting_service.get_or_create_settings(db, business_id=business_id)
    due_date_obj = inv["due_date"]
    days_to_due = (due_date_obj - today).days
    urgency, urgency_label, templates = reminder_service.generate_5_templates(
        customer_name=inv["customer_name"],
        invoice_number=inv["invoice_number"],
        amount_text=paise_to_rupees_text(inv["outstanding_paise"]),
        due_date_text=due_date_obj.strftime("%d %b %Y"),
        days_overdue=inv["days_overdue"],
        days_to_due=days_to_due,
        settings=settings,
    )

    # Redact sensitive banking/UPI numbers before returning to Gemini context
    safe_whatsapp = _redact_sensitive_payment_details(templates["whatsapp"], settings)
    safe_email_body = _redact_sensitive_payment_details(templates["email_body"], settings)
    safe_sms = _redact_sensitive_payment_details(templates["sms"], settings)

    draft = {
        "whatsapp": safe_whatsapp,
        "email_subject": templates["email_subject"],
        "email_body": safe_email_body,
        "sms": safe_sms,
    }

    return {
        "found": True,
        "as_of_date": today.isoformat(),
        "sent_automatically": False,
        "disclaimer": "Draft only — no message has been sent automatically. Use the Reminders page to copy or open in WhatsApp/Email.",
        "invoice_number": inv["invoice_number"],
        "customer_name": inv["customer_name"],
        "outstanding": _rs(inv["outstanding_paise"]),
        "days_overdue": inv["days_overdue"],
        "urgency": urgency,
        "urgency_label": urgency_label,
        "requested_channel": channel,
        "draft": draft,
    }


def get_inventory_summary(
    db: Session, today: date, business_id: int | None = None
) -> dict[str, Any]:
    if business_id is None:
        return {"error": "Business context required for inventory lookup."}
    summary = inventory_service.get_inventory_summary(db, business_id=business_id)
    return {
        "as_of_date": today.isoformat(),
        "data_type": "actual_inventory_ledger",
        "total_active_products": summary["total_active_products"],
        "total_active_services": summary["total_active_services"],
        "total_stock_units": summary["total_stock_units"],
        "low_stock_count": summary["low_stock_count"],
        "out_of_stock_count": summary["out_of_stock_count"],
        "inventory_valuation_purchase_cost": _rs(summary["inventory_valuation_paise"]),
        "inventory_valuation_paise": summary["inventory_valuation_paise"],
        "valued_products_count": summary["valued_products_count"],
        "items_needing_restock": [
            {
                "name": item["name"],
                "sku": item["sku"],
                "category": item["category"],
                "stock_quantity": item["stock_quantity"],
                "min_stock_threshold": item["min_stock_threshold"],
                "unit": item["unit"],
                "stock_status": item["stock_status"],
                "selling_price": _rs(item["selling_price_paise"]),
            }
            for item in summary["low_stock_items"]
        ],
        "recent_movements": [
            {
                "product_name": m["product_name"],
                "sku": m["sku"],
                "movement_type": m["movement_type"],
                "quantity_change": m["quantity_change"],
                "balance_after": m["balance_after"],
                "reason": m["reason"],
            }
            for m in summary["recent_movements"][:10]
        ],
    }


def search_products(
    db: Session,
    today: date,
    query: str | None = None,
    category: str | None = None,
    stock_status: str | None = None,
    business_id: int | None = None,
) -> dict[str, Any]:
    if business_id is None:
        return {"error": "Business context required for product search."}
    items = inventory_service.list_products(
        db,
        business_id=business_id,
        search=query or None,
        category=category or None,
        stock_filter=stock_status or None,
        include_inactive=False,
    )
    return {
        "as_of_date": today.isoformat(),
        "data_type": "actual_inventory_ledger",
        "match_count": len(items),
        "products": [
            {
                "name": p["name"],
                "sku": p["sku"],
                "category": p["category"],
                "item_type": p["item_type"],
                "selling_price": _rs(p["selling_price_paise"]),
                "cost_price": _rs(p["cost_price_paise"]) if p["cost_price_paise"] is not None else None,
                "tax_percent": p["tax_percent"],
                "stock_quantity": p["stock_quantity"],
                "min_stock_threshold": p["min_stock_threshold"],
                "unit": p["unit"],
                "stock_status": p["stock_status"],
            }
            for p in items[:25]
        ],
    }
