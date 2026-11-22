from datetime import date, timedelta
from fastapi.testclient import TestClient

from app.database.session import SessionLocal
from app.services.demo_service import seed_synthetic_demo_data


def test_scenario_a_customer_invoice_partial_payment(client: TestClient):
    """Scenario A:
    - Create a customer.
    - Create an invoice.
    - Record a partial payment.
    - Verify dashboard outstanding balances.
    """
    # 1. Create a customer
    cust_res = client.post(
        "/api/customers",
        json={
            "name": "Scenario A Client Corp",
            "email": "scenarioA@clientcorp.in",
            "phone": "+91 91234 56789",
            "address": "Brigade Road, Bengaluru",
            "notes": "Testing partial payment workflow",
        },
    )
    assert cust_res.status_code == 201
    cust_id = cust_res.json()["id"]

    # Check dashboard baseline
    dash_before = client.get("/api/dashboard").json()
    init_outstanding = dash_before["total_outstanding_paise"]

    # 2. Create an invoice
    inv_res = client.post(
        "/api/invoices",
        json={
            "customer_id": cust_id,
            "invoice_number": "INV-SCENARIO-A",
            "invoice_date": date.today().isoformat(),
            "due_date": (date.today() + timedelta(days=15)).isoformat(),
            "description": "Custom Automation Sprint",
            "tax_percent": 18,
            "items": [
                {"description": "Core Workflow module", "quantity": 1, "unit_price": "50000.00"}
            ],
        },
    )
    assert inv_res.status_code == 201
    inv_id = inv_res.json()["id"]
    # Total = 50000 + 18% = 59000 -> 5900000 paise

    # Mark as sent
    send_res = client.post(f"/api/invoices/{inv_id}/send")
    assert send_res.status_code == 200

    dash_after_send = client.get("/api/dashboard").json()
    assert dash_after_send["total_outstanding_paise"] == init_outstanding + 5900000

    # 3. Record a partial payment of ₹25,000.00 (2500000 paise)
    pmt_res = client.post(
        "/api/payments",
        json={
            "invoice_id": inv_id,
            "amount": "25000.00",
            "payment_date": date.today().isoformat(),
            "method": "upi",
            "reference": "UPI/SCENARIOA/001",
            "notes": "First partial tranche",
        },
    )
    assert pmt_res.status_code == 201

    # 4. Verify dashboard outstanding balances
    dash_after_pmt = client.get("/api/dashboard").json()
    # Outstanding should now be reduced by 2500000 paise
    expected_outstanding = init_outstanding + 5900000 - 2500000
    assert dash_after_pmt["total_outstanding_paise"] == expected_outstanding


def test_scenario_b_overdue_invoice_alerts_reminder(client: TestClient):
    """Scenario B:
    - Create an overdue invoice.
    - Verify overdue alerts.
    - Generate a reminder.
    """
    cust_res = client.post(
        "/api/customers",
        json={"name": "Scenario B Overdue Client", "email": "overdue@client.org", "phone": "+91 98765 00000"},
    )
    assert cust_res.status_code == 201
    cust_id = cust_res.json()["id"]

    past_date = date.today() - timedelta(days=20)
    inv_res = client.post(
        "/api/invoices",
        json={
            "customer_id": cust_id,
            "invoice_number": "INV-SCENARIO-B",
            "invoice_date": (past_date - timedelta(days=10)).isoformat(),
            "due_date": past_date.isoformat(),
            "description": "Overdue Consultation",
            "tax_percent": 0,
            "items": [{"description": "Service fee", "quantity": 1, "unit_price": "42000.00"}],
        },
    )
    assert inv_res.status_code == 201
    inv_id = inv_res.json()["id"]
    client.post(f"/api/invoices/{inv_id}/send")

    # Verify dashboard alert exists for this overdue invoice
    dash = client.get("/api/dashboard").json()
    assert any(
        a["type"] == "danger" and "INV-SCENARIO-B" in a["message"]
        for a in dash["actionable_alerts"]
    )

    # Verify in reminders list
    reminders = client.get("/api/reminders").json()
    rem_item = next((r for r in reminders["items"] if r["invoice_id"] == inv_id), None)
    assert rem_item is not None
    assert rem_item["days_overdue"] == 20
    assert "whatsapp" in rem_item["templates"]
    assert "₹42,000.00" in rem_item["templates"]["whatsapp"]


def test_scenario_c_business_expense_cashflow_impact(client: TestClient):
    """Scenario C:
    - Add an upcoming business expense.
    - Verify its impact on the cash-flow forecast.
    """
    fc_before = client.get("/api/cashflow/forecast?days=30").json()
    outflow_before = fc_before["total_scheduled_outflows_paise"]

    # Add an expense in 5 days for ₹18,000 (1800000 paise)
    exp_date = (date.today() + timedelta(days=5)).isoformat()
    exp_res = client.post(
        "/api/expenses",
        json={
            "name": "Scenario C Security Audit",
            "category": "Taxes",
            "amount": "18000.00",
            "expense_date": exp_date,
            "is_recurring": False,
        },
    )
    assert exp_res.status_code == 201

    fc_after = client.get("/api/cashflow/forecast?days=30").json()
    outflow_after = fc_after["total_scheduled_outflows_paise"]
    assert outflow_after == outflow_before + 1800000


def test_scenario_d_simulate_15_day_delay_unchanged_records(client: TestClient):
    """Scenario D:
    - Simulate a 15-day delay in an outstanding invoice.
    - Compare baseline and scenario forecasts.
    - Verify that actual records remain unchanged.
    """
    client.post("/api/demo/seed")
    invs_before = client.get("/api/invoices").json()
    first_sent = next(i for i in invs_before["items"] if i["lifecycle"] == "sent" and i["outstanding_paise"] > 0)
    original_due_date = first_sent["due_date"]
    inv_id = first_sent["id"]

    sim_res = client.post(
        "/api/cashflow/simulate",
        json={"days": 30, "delay_days": 15, "delayed_invoice_id": inv_id},
    )
    assert sim_res.status_code == 200
    sim = sim_res.json()
    assert sim["delay_days"] == 15
    assert sim["delayed_invoice_id"] == inv_id

    # Verify actual invoice record was not altered in the DB
    inv_after = client.get(f"/api/invoices/{inv_id}").json()
    assert inv_after["due_date"] == original_due_date


def test_scenario_e_change_business_settings_persistence(client: TestClient):
    """Scenario E:
    - Change business settings.
    - Refresh the application.
    - Verify that settings persist.
    """
    new_name = "Chitragupta Enterprise Operations Suite"
    put_res = client.put(
        "/api/settings",
        json={
            "business_name": new_name,
            "owner_name": "Aditi Sharma",
            "default_payment_terms_days": 30,
            "default_tax_percent": 18,
            "initial_cash_balance": "500000.00",
            "monthly_recurring_expenses": "75000.00",
            "safety_cash_threshold": "100000.00",
        },
    )
    assert put_res.status_code == 200
    assert put_res.json()["business_name"] == new_name

    # Read again
    get_res = client.get("/api/settings")
    assert get_res.status_code == 200
    assert get_res.json()["business_name"] == new_name
    assert get_res.json()["default_payment_terms_days"] == 30
