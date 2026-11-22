from datetime import date, timedelta

from app.services.status import STATUS_PAID, STATUS_PARTIALLY_PAID


def test_end_to_end_customer_invoice_payment_flow(client):
    customer = client.post(
        "/api/customers",
        json={"name": "Workflow Customer", "email": "ap@workflow.in", "phone": "9876543210"},
    )
    assert customer.status_code == 201
    customer_id = customer.json()["id"]

    today = date.today()

    invoice_response = client.post(
        "/api/invoices",
        json={
            "customer_id": customer_id,
            "invoice_date": today.isoformat(),
            "due_date": (today + timedelta(days=10)).isoformat(),
            "description": "Monthly retainer",
            "tax_percent": 18,
            "items": [
                {"description": "Design", "quantity": 2, "unit_price": "1000.00"},
                {"description": "Hosting", "quantity": 1, "unit_price": "250.50"},
            ],
        },
    )
    assert invoice_response.status_code == 201
    invoice = invoice_response.json()
    assert invoice["total_paise"] == 265559
    invoice_id = invoice["id"]

    sent = client.post(f"/api/invoices/{invoice_id}/send")
    assert sent.status_code == 200
    assert sent.json()["lifecycle"] == "sent"

    first = client.post(
        "/api/payments",
        json={"invoice_id": invoice_id, "amount": "1000.00", "method": "bank_transfer", "reference": "NEFT-1"},
    )
    assert first.status_code == 201

    partly = client.get(f"/api/invoices/{invoice_id}").json()
    assert partly["paid_paise"] == 100000
    assert partly["outstanding_paise"] == 165559
    assert partly["status"] == STATUS_PARTIALLY_PAID

    second = client.post(
        "/api/payments",
        json={"invoice_id": invoice_id, "amount": "1655.59", "method": "upi"},
    )
    assert second.status_code == 201

    paid = client.get(f"/api/invoices/{invoice_id}").json()
    assert paid["status"] == STATUS_PAID
    assert paid["outstanding_paise"] == 0
    assert len(paid["payments"]) == 2

    listed = client.get("/api/payments", params={"invoice_id": invoice_id}).json()
    assert listed["total"] == 2

    summary = client.get(f"/api/customers/{customer_id}").json()
    assert summary["invoice_count"] == 1
    assert summary["total_invoiced_paise"] == 265559
    assert summary["total_paid_paise"] == 265559
    assert summary["outstanding_paise"] == 0
    assert summary["overdue_paise"] == 0

    # A paid invoice's customer cannot be deleted while the invoice exists.
    assert client.delete(f"/api/customers/{customer_id}").status_code == 409
