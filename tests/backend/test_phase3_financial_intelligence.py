from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.payment import Payment


def test_seed_demo_and_dashboard(client: TestClient):
    # Call demo seed
    res = client.post("/api/demo/seed")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["customers_seeded"] > 0
    assert data["invoices_seeded"] > 0
    assert data["expenses_seeded"] > 0

    # Call dashboard
    dash_res = client.get("/api/dashboard")
    assert dash_res.status_code == 200
    dash = dash_res.json()
    assert dash["total_outstanding_paise"] > 0
    assert dash["total_overdue_paise"] > 0
    assert dash["cash_on_hand_paise"] > 0
    assert len(dash["actionable_alerts"]) > 0
    assert len(dash["ageing_breakdown"]) == 5
    assert len(dash["status_distribution"]) == 4


def test_cashflow_forecast_and_whatif(client: TestClient):
    # Ensure data seeded
    client.post("/api/demo/seed")

    # 30 day forecast
    fc_res = client.get("/api/cashflow/forecast?days=30")
    assert fc_res.status_code == 200
    fc = fc_res.json()
    assert fc["horizon_days"] == 30
    assert fc["starting_cash_paise"] > 0
    assert len(fc["timeline"]) == 31
    assert len(fc["customers_with_receivables"]) > 0

    # Simulate 15 day delay on first customer
    cust_id = fc["customers_with_receivables"][0]["customer_id"]
    sim_res = client.post(
        "/api/cashflow/simulate",
        json={"days": 30, "delay_days": 15, "delayed_customer_id": cust_id},
    )
    assert sim_res.status_code == 200
    sim = sim_res.json()
    assert sim["delay_days"] == 15
    assert sim["delayed_customer_id"] == cust_id
    assert "impact_explanation" in sim
    # Verify baseline vs simulated
    assert len(sim["timeline"]) == 31


def test_reminders_and_log(client: TestClient):
    client.post("/api/demo/seed")

    rem_res = client.get("/api/reminders")
    assert rem_res.status_code == 200
    rem = rem_res.json()
    assert len(rem["items"]) > 0

    first_item = rem["items"][0]
    inv_id = first_item["invoice_id"]
    assert "whatsapp" in first_item["templates"]
    assert "email_body" in first_item["templates"]
    assert "sms" in first_item["templates"]

    # Log reminder
    log_res = client.post(f"/api/reminders/{inv_id}/log", json={"channel": "whatsapp", "note": "Sent via direct message"})
    assert log_res.status_code == 200


def test_settings_get_and_put(client: TestClient):
    res = client.get("/api/settings")
    assert res.status_code == 200
    data = res.json()
    assert data["business_name"]

    # Update settings
    data["business_name"] = "Updated Back Office Consulting"
    data["initial_cash_balance"] = "300000.00"
    data["monthly_recurring_expenses"] = "70000.00"
    data["safety_cash_threshold"] = "60000.00"

    put_res = client.put("/api/settings", json=data)
    assert put_res.status_code == 200
    assert put_res.json()["business_name"] == "Updated Back Office Consulting"


def test_expenses_crud(client: TestClient):
    exp_in = {
        "name": "Cloud Backup Server",
        "category": "Software",
        "amount": "4500.00",
        "expense_date": date.today().isoformat(),
        "is_recurring": False,
        "notes": "Emergency offsite backup storage",
    }
    create_res = client.post("/api/expenses", json=exp_in)
    assert create_res.status_code == 201
    exp_id = create_res.json()["id"]

    list_res = client.get("/api/expenses")
    assert list_res.status_code == 200
    assert any(e["id"] == exp_id for e in list_res.json())

    del_res = client.delete(f"/api/expenses/{exp_id}")
    assert del_res.status_code == 204
