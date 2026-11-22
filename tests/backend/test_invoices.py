from datetime import date, timedelta

from app.services.invoice_service import compute_totals


def test_compute_totals_hand_checked():
    # 2 x 1000.00 = 200000 ; 1 x 250.50 = 25050 ; subtotal 225050
    # tax 18% = (225050 * 18 + 50) // 100 = 40509 ; total 265559
    assert compute_totals([(2, 100000), (1, 25050)], 18) == (225050, 40509, 265559)


def test_compute_totals_zero_tax_and_rounding():
    assert compute_totals([(1, 1)], 0) == (1, 0, 1)
    # 1 paise at 50% = 0.5 paise -> rounds half up to 1
    assert compute_totals([(1, 1)], 50) == (1, 1, 2)


def test_create_invoice_totals_and_numbering(client, make_customer, make_invoice):
    customer = make_customer("Invoice Customer")
    first = make_invoice(customer["id"])
    assert first["invoice_number"] == "INV-0001"
    assert first["subtotal_paise"] == 225050
    assert first["tax_paise"] == 40509
    assert first["total_paise"] == 265559
    assert first["status"] == "draft"
    assert first["lifecycle"] == "draft"
    assert first["paid_paise"] == 0
    assert first["outstanding_paise"] == 265559
    assert [i["line_total_paise"] for i in first["items"]] == [200000, 25050]
    assert first["history"][0]["action"] == "created"
    assert first["history"][0]["summary"] == "Invoice INV-0001 created"

    second = make_invoice(customer["id"])
    assert second["invoice_number"] == "INV-0002"


def test_create_invoice_for_missing_customer_is_404(client, make_invoice):
    response = client.post(
        "/api/invoices",
        json={
            "customer_id": 999,
            "invoice_date": date.today().isoformat(),
            "due_date": date.today().isoformat(),
            "description": "x",
            "items": [{"description": "a", "quantity": 1, "unit_price": "10"}],
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Customer not found."


def test_due_date_before_invoice_date_is_422(client, make_customer):
    customer = make_customer("Date Check")
    today = date.today()
    response = client.post(
        "/api/invoices",
        json={
            "customer_id": customer["id"],
            "invoice_date": today.isoformat(),
            "due_date": (today - timedelta(days=1)).isoformat(),
            "description": "x",
            "items": [{"description": "a", "quantity": 1, "unit_price": "10"}],
        },
    )
    assert response.status_code == 422
    assert response.json()["errors"][0]["field"] == "due_date"


def test_more_than_50_items_is_422(client, make_customer, make_invoice):
    customer = make_customer("Too Many")
    items = [{"description": f"Line {n}", "quantity": 1, "unit_price": "1"} for n in range(51)]
    response = client.post(
        "/api/invoices",
        json={
            "customer_id": customer["id"],
            "invoice_date": date.today().isoformat(),
            "due_date": date.today().isoformat(),
            "description": "x",
            "items": items,
        },
    )
    assert response.status_code == 422


def test_zero_price_and_bad_quantity_are_422(client, make_customer):
    customer = make_customer("Bad Lines")
    base = {
        "customer_id": customer["id"],
        "invoice_date": date.today().isoformat(),
        "due_date": date.today().isoformat(),
        "description": "x",
    }
    zero_price = client.post(
        "/api/invoices",
        json={**base, "items": [{"description": "a", "quantity": 1, "unit_price": "0"}]},
    )
    assert zero_price.status_code == 422
    zero_qty = client.post(
        "/api/invoices",
        json={**base, "items": [{"description": "a", "quantity": 0, "unit_price": "10"}]},
    )
    assert zero_qty.status_code == 422


def test_three_decimal_price_is_422(client, make_customer):
    customer = make_customer("Decimal Check")
    today = date.today().isoformat()
    response = client.post(
        "/api/invoices",
        json={
            "customer_id": customer["id"],
            "invoice_date": today,
            "due_date": today,
            "description": "x",
            "items": [{"description": "a", "quantity": 1, "unit_price": "10.505"}],
        },
    )
    assert response.status_code == 422
    assert response.json()["errors"][0]["field"] == "items.0.unit_price"


def test_duplicate_supplied_number_is_409(client, make_customer, make_invoice):
    customer = make_customer("Numbers")
    make_invoice(customer["id"], invoice_number="MANUAL-1")
    response = client.post(
        "/api/invoices",
        json={
            "customer_id": customer["id"],
            "invoice_number": "MANUAL-1",
            "invoice_date": date.today().isoformat(),
            "due_date": date.today().isoformat(),
            "description": "x",
            "items": [{"description": "a", "quantity": 1, "unit_price": "10"}],
        },
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "An invoice with this number already exists."


def test_send_only_draft_and_sets_sent(client, make_customer, make_invoice):
    customer = make_customer("Sender")
    invoice = make_invoice(customer["id"])
    sent = client.post(f"/api/invoices/{invoice['id']}/send")
    assert sent.status_code == 200
    body = sent.json()
    assert body["lifecycle"] == "sent"
    assert body["status"] == "pending"
    assert body["sent_at"] is not None
    assert body["history"][0]["action"] == "sent"

    again = client.post(f"/api/invoices/{invoice['id']}/send")
    assert again.status_code == 409
    assert again.json()["detail"] == "Only draft invoices can be sent."


def test_sent_invoice_cannot_be_deleted(client, make_customer, make_sent_invoice):
    customer = make_customer("Keeper")
    invoice = make_sent_invoice(customer["id"])
    response = client.delete(f"/api/invoices/{invoice['id']}")
    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Only draft invoices can be deleted. Sent invoices are part of the payment record."
    )


def test_draft_invoice_can_be_deleted(client, make_customer, make_invoice):
    customer = make_customer("Deleter")
    invoice = make_invoice(customer["id"])
    assert client.delete(f"/api/invoices/{invoice['id']}").status_code == 204
    assert client.get(f"/api/invoices/{invoice['id']}").status_code == 404


def test_update_draft_recomputes_totals(client, make_customer, make_invoice):
    customer = make_customer("Editor")
    invoice = make_invoice(customer["id"])
    today = date.today()
    response = client.put(
        f"/api/invoices/{invoice['id']}",
        json={
            "customer_id": customer["id"],
            "invoice_date": today.isoformat(),
            "due_date": (today + timedelta(days=10)).isoformat(),
            "description": "Consulting services (revised)",
            "tax_percent": 0,
            "items": [{"description": "Design", "quantity": 1, "unit_price": "1000.00"}],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["subtotal_paise"] == 100000
    assert body["tax_paise"] == 0
    assert body["total_paise"] == 100000
    assert body["invoice_number"] == invoice["invoice_number"]
    assert body["history"][0]["action"] == "updated"


def test_update_with_payment_is_409_for_amounts_but_allows_description(
    client, make_customer, make_sent_invoice, record_payment
):
    customer = make_customer("Locked")
    invoice = make_sent_invoice(customer["id"])
    assert record_payment(invoice["id"], "1000.00").status_code == 201

    today = date.today()
    base = {
        "customer_id": customer["id"],
        "invoice_date": today.isoformat(),
        "due_date": (today + timedelta(days=10)).isoformat(),
        "description": "Consulting services",
        "tax_percent": 18,
        "items": [
            {"description": "Design", "quantity": 2, "unit_price": "1000.00"},
            {"description": "Hosting", "quantity": 1, "unit_price": "250.50"},
        ],
    }
    locked = client.put(
        f"/api/invoices/{invoice['id']}",
        json={**base, "tax_percent": 10},
    )
    assert locked.status_code == 409
    assert locked.json()["detail"] == (
        "This invoice has payments recorded. Reverse the payments before changing its amounts."
    )

    description_only = client.put(
        f"/api/invoices/{invoice['id']}",
        json={**base, "description": "Renamed work", "notes": "Thank you"},
    )
    assert description_only.status_code == 200
    assert description_only.json()["description"] == "Renamed work"
    assert description_only.json()["total_paise"] == 265559


def test_list_filters_by_derived_status_and_paginates(client, make_customer, make_invoice, make_sent_invoice):
    customer = make_customer("Lister")
    make_invoice(customer["id"])
    make_sent_invoice(customer["id"], due_days=-10, invoice_days_ago=30)
    make_sent_invoice(customer["id"], due_days=10)

    overdue = client.get("/api/invoices", params={"status": "overdue"}).json()
    assert overdue["total"] == 1
    assert overdue["items"][0]["status"] == "overdue"
    assert overdue["items"][0]["days_overdue"] == 10

    drafts = client.get("/api/invoices", params={"status": "draft"}).json()
    assert drafts["total"] == 1

    everything = client.get("/api/invoices", params={"page": 1, "page_size": 2}).json()
    assert everything["total"] == 3
    assert len(everything["items"]) == 2

    bad_status = client.get("/api/invoices", params={"status": "cancelled"})
    assert bad_status.status_code == 422


def test_invoice_404_message(client):
    response = client.get("/api/invoices/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Invoice not found."
