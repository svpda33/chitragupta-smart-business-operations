from datetime import date, timedelta


def test_payment_on_draft_is_409(client, make_customer, make_invoice, record_payment):
    customer = make_customer("Draft Payer")
    invoice = make_invoice(customer["id"])
    response = record_payment(invoice["id"], "100.00")
    assert response.status_code == 409
    assert response.json()["detail"] == "Payments can only be recorded against sent invoices."


def test_overpayment_is_422_and_invoice_unchanged(client, make_customer, make_sent_invoice, record_payment):
    customer = make_customer("Overpay")
    invoice = make_sent_invoice(customer["id"])

    response = record_payment(invoice["id"], "2700.00")
    assert response.status_code == 422
    assert response.json()["errors"][0]["field"] == "amount"
    assert response.json()["detail"] == (
        "The payment is more than the outstanding balance of ₹2,655.59."
    )

    after = client.get(f"/api/invoices/{invoice['id']}").json()
    assert after["paid_paise"] == 0
    assert after["outstanding_paise"] == 265559
    assert after["payments"] == []


def test_exact_remaining_balance_is_accepted(client, make_customer, make_sent_invoice, record_payment):
    customer = make_customer("Exact")
    invoice = make_sent_invoice(customer["id"])
    assert record_payment(invoice["id"], "2655.59").status_code == 201
    after = client.get(f"/api/invoices/{invoice['id']}").json()
    assert after["status"] == "paid"
    assert after["outstanding_paise"] == 0


def test_payment_validation_rules(client, make_customer, make_sent_invoice, record_payment):
    customer = make_customer("Validation")
    invoice = make_sent_invoice(customer["id"])

    zero = record_payment(invoice["id"], "0")
    assert zero.status_code == 422
    assert zero.json()["errors"][0]["field"] == "amount"

    future = record_payment(
        invoice["id"], "10.00", payment_date=(date.today() + timedelta(days=1)).isoformat()
    )
    assert future.status_code == 422
    assert future.json()["errors"][0]["field"] == "payment_date"

    bad_method = record_payment(invoice["id"], "10.00", method="cheque")
    assert bad_method.status_code == 422
    assert bad_method.json()["errors"][0]["field"] == "method"


def test_record_payment_stores_trimmed_optional_text(client, make_customer, make_sent_invoice, record_payment):
    customer = make_customer("Trimmer")
    invoice = make_sent_invoice(customer["id"])
    response = record_payment(invoice["id"], "100.00", reference="  UTR123  ", notes="   ")
    assert response.status_code == 201
    body = response.json()
    assert body["reference"] == "UTR123"
    assert body["notes"] is None
    assert body["amount_paise"] == 10000
    assert body["invoice_number"] == invoice["invoice_number"]
    assert body["customer_name"] == "Trimmer"
    assert body["status"] == "active"
    assert body["history"][0]["action"] == "payment_recorded"


def test_reverse_keeps_row_and_second_reverse_is_409(client, make_customer, make_sent_invoice, record_payment):
    customer = make_customer("Reverser")
    invoice = make_sent_invoice(customer["id"])
    payment = record_payment(invoice["id"], "1000.00").json()

    reversed_response = client.post(
        f"/api/payments/{payment['id']}/reverse", json={"reason": "Cheque bounced"}
    )
    assert reversed_response.status_code == 200
    body = reversed_response.json()
    assert body["status"] == "reversed"
    assert body["reversal_reason"] == "Cheque bounced"
    assert body["reversed_at"] is not None

    again = client.post(f"/api/payments/{payment['id']}/reverse", json={"reason": "Again please"})
    assert again.status_code == 409
    assert again.json()["detail"] == "This payment has already been reversed."

    still_there = client.get(f"/api/payments/{payment['id']}")
    assert still_there.status_code == 200

    after = client.get(f"/api/invoices/{invoice['id']}").json()
    assert after["paid_paise"] == 0
    assert after["outstanding_paise"] == 265559


def test_reverse_reason_length_is_checked(client, make_customer, make_sent_invoice, record_payment):
    customer = make_customer("Short Reason")
    invoice = make_sent_invoice(customer["id"])
    payment = record_payment(invoice["id"], "100.00").json()
    response = client.post(f"/api/payments/{payment['id']}/reverse", json={"reason": "no"})
    assert response.status_code == 422
    assert response.json()["errors"][0]["field"] == "reason"


def test_reversed_payment_cannot_be_edited(client, make_customer, make_sent_invoice, record_payment):
    customer = make_customer("Frozen")
    invoice = make_sent_invoice(customer["id"])
    payment = record_payment(invoice["id"], "100.00").json()
    client.post(f"/api/payments/{payment['id']}/reverse", json={"reason": "Entered twice"})
    response = client.put(
        f"/api/payments/{payment['id']}",
        json={"amount": "50.00", "payment_date": date.today().isoformat(), "method": "cash"},
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "Reversed payments cannot be edited."


def test_update_payment_recalculates_and_audits(client, make_customer, make_sent_invoice, record_payment):
    customer = make_customer("Editor Pay")
    invoice = make_sent_invoice(customer["id"])
    payment = record_payment(invoice["id"], "1000.00", method="cash").json()

    response = client.put(
        f"/api/payments/{payment['id']}",
        json={
            "amount": "1200.00",
            "payment_date": date.today().isoformat(),
            "method": "upi",
            "reference": "REF-9",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["amount_paise"] == 120000
    assert body["method"] == "upi"
    assert body["reference"] == "REF-9"
    assert body["history"][0]["action"] == "payment_updated"
    assert "amount ₹1,000.00 -> ₹1,200.00" in body["history"][0]["summary"]
    assert "method cash -> upi" in body["history"][0]["summary"]

    invoice_after = client.get(f"/api/invoices/{invoice['id']}").json()
    assert invoice_after["paid_paise"] == 120000
    assert invoice_after["outstanding_paise"] == 265559 - 120000


def test_update_payment_respects_overpayment_excluding_itself(
    client, make_customer, make_sent_invoice, record_payment
):
    customer = make_customer("Edit Limit")
    invoice = make_sent_invoice(customer["id"])
    payment = record_payment(invoice["id"], "2000.00").json()
    # Other paid = 0, so 2655.59 (the full balance) is allowed when editing this payment.
    ok = client.put(
        f"/api/payments/{payment['id']}",
        json={"amount": "2655.59", "payment_date": date.today().isoformat(), "method": "upi"},
    )
    assert ok.status_code == 200
    too_much = client.put(
        f"/api/payments/{payment['id']}",
        json={"amount": "2655.60", "payment_date": date.today().isoformat(), "method": "upi"},
    )
    assert too_much.status_code == 422


def test_payment_list_filters(client, make_customer, make_sent_invoice, record_payment):
    customer = make_customer("Listed Payer")
    invoice = make_sent_invoice(customer["id"])
    first = record_payment(invoice["id"], "100.00").json()
    record_payment(invoice["id"], "200.00")
    client.post(f"/api/payments/{first['id']}/reverse", json={"reason": "Wrong amount"})

    everything = client.get("/api/payments", params={"invoice_id": invoice["id"]}).json()
    assert everything["total"] == 2
    active = client.get("/api/payments", params={"status": "active"}).json()
    assert active["total"] == 1
    assert active["items"][0]["amount_paise"] == 20000
    by_customer = client.get("/api/payments", params={"customer_id": customer["id"]}).json()
    assert by_customer["total"] == 2


def test_payment_404_message(client):
    response = client.get("/api/payments/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Payment not found."
