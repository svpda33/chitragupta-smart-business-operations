def test_create_customer_returns_201_and_zero_summary(client):
    response = client.post(
        "/api/customers",
        json={"name": "  Acme Traders  ", "email": "accounts@acme.in", "phone": "+91 98765-43210"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Acme Traders"
    assert body["email"] == "accounts@acme.in"
    assert body["phone"] == "+91 98765-43210"
    assert body["invoice_count"] == 0
    assert body["outstanding_paise"] == 0
    assert body["overdue_paise"] == 0


def test_blank_optional_fields_become_null(client):
    body = client.post("/api/customers", json={"name": "Blank Co", "email": "  ", "notes": ""}).json()
    assert body["email"] is None
    assert body["notes"] is None


def test_invalid_email_is_422_with_field(client):
    response = client.post("/api/customers", json={"name": "Bad Mail", "email": "not-an-email"})
    assert response.status_code == 422
    assert response.json()["errors"][0]["field"] == "email"


def test_invalid_phone_is_422_with_field(client):
    response = client.post("/api/customers", json={"name": "Bad Phone", "phone": "12ab"})
    assert response.status_code == 422
    assert response.json()["errors"][0]["field"] == "phone"


def test_duplicate_name_is_case_insensitive_409(client, make_customer):
    make_customer("Acme Traders")
    response = client.post("/api/customers", json={"name": "acme traders"})
    assert response.status_code == 409
    assert response.json()["detail"] == "A customer with this name already exists."
    assert response.json()["errors"][0]["field"] == "name"


def test_update_allows_keeping_own_name(client, make_customer):
    customer = make_customer("Solo Name")
    response = client.put(
        f"/api/customers/{customer['id']}",
        json={"name": "Solo Name", "address": "12 MG Road"},
    )
    assert response.status_code == 200
    assert response.json()["address"] == "12 MG Road"


def test_update_to_another_customers_name_is_409(client, make_customer):
    make_customer("First")
    second = make_customer("Second")
    response = client.put(f"/api/customers/{second['id']}", json={"name": "first"})
    assert response.status_code == 409


def test_get_missing_customer_is_404(client):
    response = client.get("/api/customers/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Customer not found."


def test_list_is_paginated_sorted_by_name_and_searchable(client, make_customer):
    make_customer("Zeta Foods", email="zeta@example.com")
    make_customer("Alpha Labs", phone="9876543210")
    make_customer("Mango Mart")

    page = client.get("/api/customers", params={"page": 1, "page_size": 2}).json()
    assert page["total"] == 3
    assert page["page"] == 1
    assert page["page_size"] == 2
    assert [c["name"] for c in page["items"]] == ["Alpha Labs", "Mango Mart"]

    second = client.get("/api/customers", params={"page": 2, "page_size": 2}).json()
    assert [c["name"] for c in second["items"]] == ["Zeta Foods"]

    by_email = client.get("/api/customers", params={"search": "zeta@"}).json()
    assert by_email["total"] == 1
    by_phone = client.get("/api/customers", params={"search": "98765"}).json()
    assert by_phone["items"][0]["name"] == "Alpha Labs"


def test_page_size_above_100_is_422(client):
    assert client.get("/api/customers", params={"page_size": 101}).status_code == 422


def test_customer_summary_for_sent_unpaid_invoice(client, make_customer, make_sent_invoice):
    customer = make_customer("Summary Co")
    make_sent_invoice(customer["id"])
    body = client.get(f"/api/customers/{customer['id']}").json()
    assert body["invoice_count"] == 1
    assert body["total_invoiced_paise"] == 265559
    assert body["total_paid_paise"] == 0
    assert body["outstanding_paise"] == 265559
    assert body["overdue_paise"] == 0


def test_customer_summary_counts_overdue(client, make_customer, make_sent_invoice):
    customer = make_customer("Late Payer")
    make_sent_invoice(customer["id"], due_days=-10, invoice_days_ago=30)
    body = client.get(f"/api/customers/{customer['id']}").json()
    assert body["overdue_paise"] == 265559
    assert body["outstanding_paise"] == 265559


def test_draft_invoice_is_counted_but_adds_no_money(client, make_customer, make_invoice):
    customer = make_customer("Draft Only")
    make_invoice(customer["id"])
    body = client.get(f"/api/customers/{customer['id']}").json()
    assert body["invoice_count"] == 1
    assert body["total_invoiced_paise"] == 0
    assert body["outstanding_paise"] == 0


def test_delete_customer_with_invoice_is_409(client, make_customer, make_invoice):
    customer = make_customer("Has Invoices")
    make_invoice(customer["id"])
    response = client.delete(f"/api/customers/{customer['id']}")
    assert response.status_code == 409
    assert response.json()["detail"] == (
        "This customer has invoices and cannot be deleted. Keep the record to preserve payment history."
    )
    assert client.get(f"/api/customers/{customer['id']}").status_code == 200


def test_delete_customer_without_invoices_returns_204(client, make_customer):
    customer = make_customer("Temporary Co")
    response = client.delete(f"/api/customers/{customer['id']}")
    assert response.status_code == 204
    assert client.get(f"/api/customers/{customer['id']}").status_code == 404
