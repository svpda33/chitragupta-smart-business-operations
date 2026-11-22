from datetime import date, timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.expense import Expense
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.services.payment_service import PAYMENT_ACTIVE, paid_totals
from app.services.setting_service import get_or_create_settings
from app.services.status import LIFECYCLE_SENT
from app.utils.money import paise_to_rupees_text


def calculate_cashflow_forecast(
    db: Session,
    days: int = 30,
    delay_days: int = 0,
    delayed_customer_id: int | None = None,
    delayed_invoice_id: int | None = None,
    today: date | None = None,
    business_id: int | None = None,
) -> dict:
    if today is None:
        today = date.today()

    if days not in (30, 60, 90):
        if days < 45:
            days = 30
        elif days < 75:
            days = 60
        else:
            days = 90

    settings = get_or_create_settings(db, business_id=business_id)
    initial_cash = settings.initial_cash_balance_paise
    safety_threshold = settings.safety_cash_threshold_paise
    settings_expenses = settings.get_expenses()

    # Total collected all time for current cash position
    total_collected_stmt = select(Payment.amount_paise).where(Payment.status == PAYMENT_ACTIVE)
    if business_id is not None:
        total_collected_stmt = total_collected_stmt.where(Payment.business_id == business_id)
    active_pmts = db.execute(total_collected_stmt).scalars().all()
    total_collected = sum(active_pmts)

    # Database expenses
    exp_stmt = select(Expense)
    if business_id is not None:
        exp_stmt = exp_stmt.where(Expense.business_id == business_id)
    db_expenses = list(db.scalars(exp_stmt).all())
    db_recurring = [e for e in db_expenses if e.is_recurring]
    db_oneoff = [e for e in db_expenses if not e.is_recurring]

    # Calculate monthly burn
    if db_recurring:
        monthly_burn = sum(e.amount_paise for e in db_recurring)
    else:
        monthly_burn = settings.monthly_recurring_expenses_paise

    # Starting cash balance
    starting_cash = max(0, initial_cash + total_collected - (monthly_burn // 2))

    # Fetch sent invoices with customers
    invoices_stmt = (
        select(Invoice, Customer.name.label("customer_name"))
        .join(Customer, Invoice.customer_id == Customer.id)
        .where(Invoice.lifecycle == LIFECYCLE_SENT)
    )
    if business_id is not None:
        invoices_stmt = invoices_stmt.where(Invoice.business_id == business_id)
    invoices_rows = db.execute(invoices_stmt).all()
    invoice_ids = [row.Invoice.id for row in invoices_rows]
    paid_map = paid_totals(db, invoice_ids)

    customer_agg: dict[int, dict] = {}
    pending_invoices = []
    delayed_invoice_number = None

    for row in invoices_rows:
        inv = row.Invoice
        customer_name = row.customer_name
        paid = paid_map.get(inv.id, 0)
        outstanding = max(0, inv.total_paise - paid)

        if outstanding > 0:
            if inv.customer_id not in customer_agg:
                customer_agg[inv.customer_id] = {
                    "customer_id": inv.customer_id,
                    "customer_name": customer_name,
                    "outstanding_paise": 0,
                    "invoice_count": 0,
                }
            customer_agg[inv.customer_id]["outstanding_paise"] += outstanding
            customer_agg[inv.customer_id]["invoice_count"] += 1

            if delayed_invoice_id and inv.id == delayed_invoice_id:
                delayed_invoice_number = inv.invoice_number

            pending_invoices.append({
                "invoice_id": inv.id,
                "invoice_number": inv.invoice_number,
                "customer_id": inv.customer_id,
                "customer_name": customer_name,
                "due_date": inv.due_date,
                "outstanding_paise": outstanding,
            })

    customers_with_receivables = sorted(
        customer_agg.values(), key=lambda x: x["outstanding_paise"], reverse=True
    )

    delayed_customer_name = None
    if delayed_customer_id:
        cust = db.get(Customer, delayed_customer_id)
        if cust and (business_id is None or cust.business_id == business_id):
            delayed_customer_name = cust.name

    # Inflow mapping per day
    baseline_inflows_by_date: dict[date, int] = {}
    simulated_inflows_by_date: dict[date, int] = {}

    for inv in pending_invoices:
        # Baseline expected arrival:
        # If already overdue, expect it staggered in 2 to 6 days
        if inv["due_date"] < today:
            offset = (inv["invoice_id"] % 5) + 2
            base_exp_date = today + timedelta(days=offset)
        else:
            base_exp_date = inv["due_date"]

        # Simulation shift:
        apply_delay = False
        if delayed_invoice_id is not None:
            if inv["invoice_id"] == delayed_invoice_id:
                apply_delay = True
        elif delayed_customer_id is not None:
            if inv["customer_id"] == delayed_customer_id:
                apply_delay = True
        elif delay_days > 0:
            apply_delay = True

        sim_exp_date = base_exp_date + timedelta(days=delay_days) if apply_delay else base_exp_date

        baseline_inflows_by_date[base_exp_date] = (
            baseline_inflows_by_date.get(base_exp_date, 0) + inv["outstanding_paise"]
        )
        simulated_inflows_by_date[sim_exp_date] = (
            simulated_inflows_by_date.get(sim_exp_date, 0) + inv["outstanding_paise"]
        )

    # Build timeline daily
    timeline = []
    current_baseline_balance = starting_cash
    current_simulated_balance = starting_cash

    total_expected_inflows = 0
    total_scheduled_outflows = 0

    baseline_min_balance = starting_cash
    simulated_min_balance = starting_cash
    shortfall_detected = False
    shortfall_date = None
    affected_expenses = []

    for day_idx in range(days + 1):
        cur_date = today + timedelta(days=day_idx)

        # Inflow
        inflow_base = baseline_inflows_by_date.get(cur_date, 0)
        inflow_sim = simulated_inflows_by_date.get(cur_date, 0)

        # Outflow from recurring and one-off expenses
        outflow = 0
        cur_day_expense_items = []
        if db_recurring:
            for exp in db_recurring:
                if cur_date.day == exp.day_of_month:
                    outflow += exp.amount_paise
                    cur_day_expense_items.append({"name": exp.name, "amount_paise": exp.amount_paise, "category": exp.category, "date": cur_date.isoformat()})
        elif settings_expenses:
            for exp in settings_expenses:
                if cur_date.day == exp.get("day_of_month", 1):
                    amt = exp.get("amount_paise", 0)
                    outflow += amt
                    cur_day_expense_items.append({"name": exp.get("name", "Expense"), "amount_paise": amt, "category": "Recurring", "date": cur_date.isoformat()})
        else:
            if cur_date.day in (1, 15):
                amt = monthly_burn // 2
                outflow += amt
                cur_day_expense_items.append({"name": "Operating Expenses", "amount_paise": amt, "category": "Operating", "date": cur_date.isoformat()})

        for exp in db_oneoff:
            if exp.expense_date == cur_date:
                outflow += exp.amount_paise
                cur_day_expense_items.append({"name": exp.name, "amount_paise": exp.amount_paise, "category": exp.category, "date": cur_date.isoformat()})

        total_expected_inflows += inflow_base
        total_scheduled_outflows += outflow

        current_baseline_balance = current_baseline_balance + inflow_base - outflow
        current_simulated_balance = current_simulated_balance + inflow_sim - outflow

        if current_baseline_balance < baseline_min_balance:
            baseline_min_balance = current_baseline_balance
        if current_simulated_balance < simulated_min_balance:
            simulated_min_balance = current_simulated_balance

        is_below_safety_base = current_baseline_balance < safety_threshold
        is_below_safety_sim = current_simulated_balance < safety_threshold

        if is_below_safety_sim:
            if not shortfall_detected:
                shortfall_detected = True
                shortfall_date = cur_date.isoformat()
            for exp_item in cur_day_expense_items:
                if not any(ae["name"] == exp_item["name"] and ae["date"] == exp_item["date"] for ae in affected_expenses):
                    affected_expenses.append(exp_item)

        day_label = cur_date.strftime("%d %b")
        timeline.append({
            "date": cur_date.isoformat(),
            "day_label": day_label,
            "inflow_baseline_paise": inflow_base,
            "inflow_simulated_paise": inflow_sim,
            "outflow_paise": outflow,
            "balance_baseline_paise": current_baseline_balance,
            "balance_simulated_paise": current_simulated_balance,
            "safety_threshold_paise": safety_threshold,
            "is_below_safety_baseline": is_below_safety_base,
            "is_below_safety_simulated": is_below_safety_sim,
        })

    if monthly_burn > 0:
        daily_burn_paise = max(1, monthly_burn // 30)
        runway_baseline = int(current_baseline_balance // daily_burn_paise)
        runway_simulated = int(current_simulated_balance // daily_burn_paise)
    else:
        runway_baseline = 999
        runway_simulated = 999

    # Generate impact explanation
    impact_explanation = []
    if delay_days > 0:
        target_name = delayed_invoice_number or delayed_customer_name or "customer payments"
        diff_min = baseline_min_balance - simulated_min_balance
        if diff_min > 0:
            impact_explanation.append(
                f"A {delay_days}-day delay in {target_name} temporarily reduces your available cash dip by ₹{paise_to_rupees_text(diff_min)}."
            )
        if shortfall_detected and shortfall_date:
            impact_explanation.append(
                f"WARNING: On {shortfall_date}, cash reserves drop below your safety threshold of ₹{paise_to_rupees_text(safety_threshold)}."
            )
            if affected_expenses:
                exp_names = ", ".join(e["name"] for e in affected_expenses[:3])
                impact_explanation.append(
                    f"Expenses that fall during the shortage window: {exp_names}."
                )
        else:
            impact_explanation.append(
                "Even with this simulated delay, your cash balance remains above the safety threshold throughout the period."
            )
    else:
        impact_explanation.append(
            "Baseline projection: your projected ending cash is ₹" + paise_to_rupees_text(current_baseline_balance) + "."
        )

    return {
        "horizon_days": days,
        "delay_days": delay_days,
        "delayed_customer_id": delayed_customer_id,
        "delayed_customer_name": delayed_customer_name,
        "delayed_invoice_id": delayed_invoice_id,
        "delayed_invoice_number": delayed_invoice_number,
        "starting_cash_paise": starting_cash,
        "baseline_ending_cash_paise": current_baseline_balance,
        "simulated_ending_cash_paise": current_simulated_balance,
        "total_expected_inflows_paise": total_expected_inflows,
        "total_scheduled_outflows_paise": total_scheduled_outflows,
        "baseline_min_balance_paise": baseline_min_balance,
        "simulated_min_balance_paise": simulated_min_balance,
        "safety_threshold_paise": safety_threshold,
        "shortfall_detected": shortfall_detected,
        "shortfall_date": shortfall_date,
        "runway_days_baseline": max(0, runway_baseline),
        "runway_days_simulated": max(0, runway_simulated),
        "affected_expenses": affected_expenses,
        "impact_explanation": " ".join(impact_explanation),
        "timeline": timeline,
        "customers_with_receivables": customers_with_receivables,
        "pending_invoices": pending_invoices,
    }
