from datetime import date, timedelta
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.expense import Expense
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.product import Product
from app.services.payment_service import PAYMENT_ACTIVE, paid_totals
from app.services.setting_service import get_or_create_settings
from app.services.status import (
    LIFECYCLE_DRAFT,
    LIFECYCLE_SENT,
    STATUS_DRAFT,
    STATUS_OVERDUE,
    STATUS_PAID,
    STATUS_PARTIALLY_PAID,
    STATUS_PENDING,
    derive_invoice_status,
)
from app.utils.money import paise_to_rupees_text


def get_dashboard_summary(
    db: Session, today: date | None = None, business_id: int | None = None
) -> dict:
    if today is None:
        today = date.today()

    first_day_of_month = date(today.year, today.month, 1)

    settings = get_or_create_settings(db, business_id=business_id)
    initial_cash = settings.initial_cash_balance_paise
    safety_threshold = settings.safety_cash_threshold_paise

    # Check expenses
    exp_stmt = select(Expense)
    if business_id is not None:
        exp_stmt = exp_stmt.where(Expense.business_id == business_id)
    db_expenses = list(db.scalars(exp_stmt).all())
    if db_expenses:
        monthly_expenses = sum(e.amount_paise for e in db_expenses if e.is_recurring)
        if monthly_expenses == 0:
            monthly_expenses = settings.monthly_recurring_expenses_paise
    else:
        monthly_expenses = settings.monthly_recurring_expenses_paise

    # All invoices
    inv_stmt = (
        select(Invoice, Customer.name.label("customer_name"))
        .join(Customer, Invoice.customer_id == Customer.id)
        .order_by(Invoice.invoice_date.desc(), Invoice.id.desc())
    )
    if business_id is not None:
        inv_stmt = inv_stmt.where(Invoice.business_id == business_id)
    invoices = db.execute(inv_stmt).all()

    invoice_ids = [inv.Invoice.id for inv in invoices]
    paid_map = paid_totals(db, invoice_ids)

    total_outstanding_paise = 0
    total_overdue_paise = 0
    overdue_count = 0
    pending_count = 0
    paid_count = 0
    draft_count = 0

    total_invoiced_month_paise = 0
    total_invoiced_all_time_paise = 0

    ageing = {
        "current": {"label": "Current / Not Due", "count": 0, "amount_paise": 0},
        "1_15": {"label": "1–15 Days Overdue", "count": 0, "amount_paise": 0},
        "16_30": {"label": "16–30 Days Overdue", "count": 0, "amount_paise": 0},
        "31_60": {"label": "31–60 Days Overdue", "count": 0, "amount_paise": 0},
        "60_plus": {"label": "60+ Days Overdue", "count": 0, "amount_paise": 0},
    }

    customer_receivables: dict[str, int] = {}
    overdue_list = []
    upcoming_due_list = []
    recent_invoices = []

    for row in invoices:
        inv = row.Invoice
        customer_name = row.customer_name
        paid = paid_map.get(inv.id, 0)
        status, days_overdue = derive_invoice_status(inv.lifecycle, inv.total_paise, paid, inv.due_date, today)
        outstanding = max(0, inv.total_paise - paid) if inv.lifecycle == LIFECYCLE_SENT else 0

        if inv.lifecycle == LIFECYCLE_DRAFT:
            draft_count += 1
        else:
            total_invoiced_all_time_paise += inv.total_paise
            if inv.invoice_date >= first_day_of_month:
                total_invoiced_month_paise += inv.total_paise

            if status == STATUS_PAID:
                paid_count += 1
            else:
                total_outstanding_paise += outstanding
                customer_receivables[customer_name] = customer_receivables.get(customer_name, 0) + outstanding

                if status == STATUS_OVERDUE:
                    overdue_count += 1
                    total_overdue_paise += outstanding
                    overdue_list.append({
                        "invoice_id": inv.id,
                        "invoice_number": inv.invoice_number,
                        "customer_name": customer_name,
                        "outstanding_paise": outstanding,
                        "days_overdue": days_overdue,
                        "due_date": inv.due_date.isoformat(),
                    })

                    if days_overdue <= 15:
                        ageing["1_15"]["count"] += 1
                        ageing["1_15"]["amount_paise"] += outstanding
                    elif days_overdue <= 30:
                        ageing["16_30"]["count"] += 1
                        ageing["16_30"]["amount_paise"] += outstanding
                    elif days_overdue <= 60:
                        ageing["31_60"]["count"] += 1
                        ageing["31_60"]["amount_paise"] += outstanding
                    else:
                        ageing["60_plus"]["count"] += 1
                        ageing["60_plus"]["amount_paise"] += outstanding
                else:
                    pending_count += 1
                    ageing["current"]["count"] += 1
                    ageing["current"]["amount_paise"] += outstanding

                    days_left = (inv.due_date - today).days
                    if 0 <= days_left <= 5:
                        upcoming_due_list.append({
                            "invoice_id": inv.id,
                            "invoice_number": inv.invoice_number,
                            "customer_name": customer_name,
                            "outstanding_paise": outstanding,
                            "due_date": inv.due_date.isoformat(),
                            "days_left": days_left,
                        })

        if len(recent_invoices) < 6:
            recent_invoices.append({
                "id": inv.id,
                "invoice_number": inv.invoice_number,
                "customer_name": customer_name,
                "invoice_date": inv.invoice_date.isoformat(),
                "due_date": inv.due_date.isoformat(),
                "total_paise": inv.total_paise,
                "paid_paise": paid,
                "outstanding_paise": outstanding,
                "status": status,
                "lifecycle": inv.lifecycle,
                "days_overdue": days_overdue,
            })

    # Payments metrics
    payments_stmt = (
        select(Payment, Invoice.invoice_number, Customer.name.label("customer_name"))
        .join(Invoice, Payment.invoice_id == Invoice.id)
        .join(Customer, Payment.customer_id == Customer.id)
        .order_by(Payment.payment_date.desc(), Payment.id.desc())
    )
    if business_id is not None:
        payments_stmt = payments_stmt.where(Payment.business_id == business_id)
    all_payments = db.execute(payments_stmt).all()

    total_collected_all_time_paise = 0
    total_collected_month_paise = 0
    recent_payments = []

    for row in all_payments:
        pmt = row.Payment
        if pmt.status == PAYMENT_ACTIVE:
            total_collected_all_time_paise += pmt.amount_paise
            if pmt.payment_date >= first_day_of_month:
                total_collected_month_paise += pmt.amount_paise

        if len(recent_payments) < 6:
            recent_payments.append({
                "id": pmt.id,
                "invoice_id": pmt.invoice_id,
                "invoice_number": row.invoice_number,
                "customer_name": row.customer_name,
                "amount_paise": pmt.amount_paise,
                "payment_date": pmt.payment_date.isoformat(),
                "method": pmt.method,
                "status": pmt.status,
                "reference": pmt.reference,
            })

    # Collection efficiency
    denom = total_collected_all_time_paise + total_outstanding_paise
    collection_efficiency = (
        round((total_collected_all_time_paise / denom) * 100, 1) if denom > 0 else 100.0
    )

    # Cash on hand
    cash_on_hand_paise = max(0, initial_cash + total_collected_all_time_paise - (monthly_expenses // 2))

    # Runway in days
    if monthly_expenses > 0:
        daily_burn_paise = max(1, monthly_expenses // 30)
        runway_days = int(cash_on_hand_paise // daily_burn_paise)
    else:
        runway_days = 999

    # Generate Actionable Alerts
    alerts = []
    alert_idx = 1

    # 1. Invoice Overdue Alerts
    overdue_list.sort(key=lambda x: x["outstanding_paise"], reverse=True)
    if overdue_list:
        for top_overdue in overdue_list[:2]:
            amt_str = f"₹{paise_to_rupees_text(top_overdue['outstanding_paise'])}"
            priority = "high" if top_overdue["days_overdue"] > 14 else "medium"
            alerts.append({
                "id": f"alert-{alert_idx}",
                "type": "danger",
                "priority": priority,
                "title": f"Overdue Invoice: {top_overdue['customer_name']}",
                "message": f"Invoice {top_overdue['invoice_number']} for {amt_str} is {top_overdue['days_overdue']} days overdue (due {top_overdue['due_date']}).",
                "entity_type": "invoice",
                "entity_name": top_overdue["invoice_number"],
                "amount_paise": top_overdue["outstanding_paise"],
                "date": top_overdue["due_date"],
                "action_label": "Chase payment",
                "action_url": f"/reminders",
            })
            alert_idx += 1

    # 2. Payment Due Soon Alert
    if upcoming_due_list:
        top_upcoming = upcoming_due_list[0]
        amt_str = f"₹{paise_to_rupees_text(top_upcoming['outstanding_paise'])}"
        days_str = "today" if top_upcoming["days_left"] == 0 else f"in {top_upcoming['days_left']} day(s)"
        alerts.append({
            "id": f"alert-{alert_idx}",
            "type": "warning",
            "priority": "medium",
            "title": f"Payment Due Soon: {top_upcoming['customer_name']}",
            "message": f"Invoice {top_upcoming['invoice_number']} for {amt_str} is due {days_str} ({top_upcoming['due_date']}).",
            "entity_type": "invoice",
            "entity_name": top_upcoming["invoice_number"],
            "amount_paise": top_upcoming["outstanding_paise"],
            "date": top_upcoming["due_date"],
            "action_label": "Send advance reminder",
            "action_url": "/reminders",
        })
        alert_idx += 1

    # 3. Large Customer Concentration Risk
    if total_outstanding_paise > 0:
        for cust_name, cust_amt in customer_receivables.items():
            ratio = (cust_amt / total_outstanding_paise) * 100
            if ratio >= 40:
                alerts.append({
                    "id": f"alert-{alert_idx}",
                    "type": "warning",
                    "priority": "high",
                    "title": f"Concentration Risk: {cust_name}",
                    "message": f"{cust_name} owes {ratio:.0f}% (₹{paise_to_rupees_text(cust_amt)}) of your total outstanding receivables.",
                    "entity_type": "customer",
                    "entity_name": cust_name,
                    "amount_paise": cust_amt,
                    "date": today.isoformat(),
                    "action_label": "View customer details",
                    "action_url": f"/invoices",
                })
                alert_idx += 1
                break

    # 4. Cash Reserve & Shortage Alert
    if cash_on_hand_paise < safety_threshold:
        alerts.append({
            "id": f"alert-{alert_idx}",
            "type": "danger",
            "priority": "high",
            "title": "Projected Cash Shortage Alert",
            "message": f"Cash on hand (₹{paise_to_rupees_text(cash_on_hand_paise)}) is below safety reserve ₹{paise_to_rupees_text(safety_threshold)}. Estimated runway is {runway_days} days.",
            "entity_type": "cashflow",
            "entity_name": "Cash Reserve",
            "amount_paise": cash_on_hand_paise,
            "date": today.isoformat(),
            "action_label": "View Cash Flow",
            "action_url": "/cash-flow",
        })
        alert_idx += 1

    # 5. Upcoming Business Expense Alert
    upcoming_expenses = [e for e in db_expenses if e.expense_date >= today and e.expense_date <= today + timedelta(days=7)]
    if upcoming_expenses:
        exp = upcoming_expenses[0]
        alerts.append({
            "id": f"alert-{alert_idx}",
            "type": "info",
            "priority": "medium",
            "title": f"Upcoming Expense: {exp.name}",
            "message": f"Scheduled payout of ₹{paise_to_rupees_text(exp.amount_paise)} ({exp.category}) is due on {exp.expense_date.isoformat()}.",
            "entity_type": "expense",
            "entity_name": exp.name,
            "amount_paise": exp.amount_paise,
            "date": exp.expense_date.isoformat(),
            "action_label": "View Cash Flow",
            "action_url": "/cash-flow",
        })
        alert_idx += 1

    # 6. Low-Stock / Out-of-Stock Inventory Alerts
    if business_id is not None:
        low_stock_products = list(
            db.scalars(
                select(Product)
                .where(
                    Product.business_id == business_id,
                    Product.item_type == "product",
                    Product.is_active == True,  # noqa: E712
                    Product.stock_quantity <= Product.min_stock_threshold,
                )
                .order_by(Product.stock_quantity.asc(), Product.name.asc())
                .limit(2)
            ).all()
        )
        for prod in low_stock_products:
            is_out = prod.stock_quantity <= 0
            alerts.append({
                "id": f"alert-{alert_idx}",
                "type": "danger" if is_out else "warning",
                "priority": "high" if is_out else "medium",
                "title": f"{'Out of Stock' if is_out else 'Low Stock'}: {prod.name}",
                "message": (
                    f"{prod.name} has 0 {prod.unit} left in stock. Restock soon to avoid invoice blocks."
                    if is_out
                    else f"{prod.name} is down to {prod.stock_quantity} {prod.unit} (reorder threshold: {prod.min_stock_threshold})."
                ),
                "entity_type": "product",
                "entity_name": prod.name,
                "amount_paise": prod.selling_price_paise,
                "date": today.isoformat(),
                "action_label": "Restock in Inventory",
                "action_url": "/inventory",
            })
            alert_idx += 1

    # 7. Important Payment Received Alert
    recent_active_pmts = [p for p in recent_payments if p["status"] == PAYMENT_ACTIVE]
    if recent_active_pmts:
        top_pmt = recent_active_pmts[0]
        alerts.append({
            "id": f"alert-{alert_idx}",
            "type": "success",
            "priority": "low",
            "title": f"Payment Received: {top_pmt['customer_name']}",
            "message": f"Received ₹{paise_to_rupees_text(top_pmt['amount_paise'])} for invoice {top_pmt['invoice_number']} via {top_pmt['method']}.",
            "entity_type": "payment",
            "entity_name": top_pmt["invoice_number"],
            "amount_paise": top_pmt["amount_paise"],
            "date": top_pmt["payment_date"],
            "action_label": "View Payments",
            "action_url": "/payments",
        })
        alert_idx += 1

    status_distribution = [
        {"status": "pending", "label": "Pending", "count": pending_count, "amount_paise": ageing["current"]["amount_paise"]},
        {"status": "overdue", "label": "Overdue", "count": overdue_count, "amount_paise": total_overdue_paise},
        {"status": "paid", "label": "Paid", "count": paid_count, "amount_paise": total_collected_all_time_paise},
        {"status": "draft", "label": "Draft", "count": draft_count, "amount_paise": 0},
    ]

    ageing_breakdown = [
        ageing["current"],
        ageing["1_15"],
        ageing["16_30"],
        ageing["31_60"],
        ageing["60_plus"],
    ]

    return {
        "total_outstanding_paise": total_outstanding_paise,
        "total_overdue_paise": total_overdue_paise,
        "overdue_invoices_count": overdue_count,
        "pending_invoices_count": pending_count,
        "paid_invoices_count": paid_count,
        "draft_invoices_count": draft_count,
        "cash_on_hand_paise": cash_on_hand_paise,
        "safety_cash_threshold_paise": safety_threshold,
        "runway_days": runway_days,
        "total_invoiced_month_paise": total_invoiced_month_paise,
        "total_collected_month_paise": total_collected_month_paise,
        "total_invoiced_all_time_paise": total_invoiced_all_time_paise,
        "total_collected_all_time_paise": total_collected_all_time_paise,
        "collection_efficiency_percent": collection_efficiency,
        "status_distribution": status_distribution,
        "ageing_breakdown": ageing_breakdown,
        "actionable_alerts": alerts,
        "recent_invoices": recent_invoices,
        "recent_payments": recent_payments,
    }
