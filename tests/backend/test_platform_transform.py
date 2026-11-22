"""Tests for Chitragupta SaaS transformation: auth, multi-business isolation,
products/services, inventory ledger & invoice stock deduction, notepad, and uploads.
"""

from datetime import date, timedelta


def _register_and_onboard(tc, email: str, biz_name: str, full_name: str = "Owner"):
    reg = tc.post(
        "/api/auth/register",
        json={
            "full_name": full_name,
            "email": email,
            "password": "StrongPassword123!",
            "confirm_password": "StrongPassword123!",
        },
    )
    assert reg.status_code == 201, reg.text
    onb = tc.post(
        "/api/business/onboarding",
        json={
            "name": biz_name,
            "category": "Retail & Trading",
            "owner_name": full_name,
            "email": email,
            "currency": "INR",
        },
    )
    assert onb.status_code in (200, 201), onb.text
    return reg.json(), onb.json()


def test_unauthenticated_access_blocked_and_auth_lifecycle(anon_client):
    # Protected endpoints reject unauthenticated requests
    assert anon_client.get("/api/dashboard").status_code == 401
    assert anon_client.get("/api/customers").status_code == 401
    assert anon_client.get("/api/products").status_code == 401
    assert anon_client.get("/api/notes").status_code == 401

    # Password mismatch rejected
    bad = anon_client.post(
        "/api/auth/register",
        json={
            "full_name": "Priya Verma",
            "email": "priya@shop.in",
            "password": "StrongPassword123!",
            "confirm_password": "DifferentPassword123!",
        },
    )
    assert bad.status_code == 422

    # Register succeeds and sets session cookie
    reg = anon_client.post(
        "/api/auth/register",
        json={
            "full_name": "Priya Verma",
            "email": "priya@shop.in",
            "password": "StrongPassword123!",
            "confirm_password": "StrongPassword123!",
        },
    )
    assert reg.status_code == 201
    me = anon_client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["onboarding_completed"] is False

    # Before onboarding, business-scoped endpoints return 403/400 (needs onboarding)
    pre_dash = anon_client.get("/api/dashboard")
    assert pre_dash.status_code in (400, 403, 404)

    # Complete onboarding
    onb = anon_client.post(
        "/api/business/onboarding",
        json={
            "name": "Priya Textiles",
            "category": "Retail",
            "owner_name": "Priya Verma",
            "currency": "INR",
        },
    )
    assert onb.status_code in (200, 201)

    # Clean account experience: zero demo customers/invoices
    dash = anon_client.get("/api/dashboard")
    assert dash.status_code == 200
    body = dash.json()
    assert body["total_outstanding_paise"] == 0
    assert body["recent_invoices"] == []

    # Logout invalidates session
    out = anon_client.post("/api/auth/logout")
    assert out.status_code in (200, 204)
    assert anon_client.get("/api/auth/me").status_code == 401

    # Login restores session
    login = anon_client.post(
        "/api/auth/login",
        json={"email": "priya@shop.in", "password": "StrongPassword123!"},
    )
    assert login.status_code == 200
    assert anon_client.get("/api/auth/me").json()["business"]["name"] == "Priya Textiles"


def test_strict_multi_business_isolation(session_factory):
    from fastapi.testclient import TestClient
    from app.database.session import get_db
    from app.main import app

    def override_get_db():
        s = session_factory()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        client_a = TestClient(app)
        client_b = TestClient(app)

        _register_and_onboard(client_a, "alice@alpha.in", "Alpha Crafts", "Alice")
        _register_and_onboard(client_b, "bob@beta.in", "Beta Studios", "Bob")

        # Business A creates customer, product, note, AI conversation
        c_a = client_a.post("/api/customers", json={"name": "Alpha VIP"}).json()
        p_a = client_a.post(
            "/api/products",
            json={
                "name": "Handloom Scarf",
                "item_type": "product",
                "selling_price": "1200.00",
                "stock_quantity": 25,
                "min_stock_threshold": 5,
            },
        ).json()
        n_a = client_a.post(
            "/api/notes",
            json={"title": "Secret Pricing Plan", "content": "Confidential margins"},
        ).json()
        conv_a = client_a.post("/api/ai/conversations", json={"title": "Alpha Cash"}).json()

        # Business B sees NONE of Business A's records
        assert client_b.get("/api/customers").json()["items"] == []
        assert client_b.get(f"/api/customers/{c_a['id']}").status_code == 404

        assert client_b.get("/api/products").json() == []
        assert client_b.get(f"/api/products/{p_a['id']}").status_code == 404

        assert client_b.get("/api/notes").json() == []
        assert client_b.delete(f"/api/notes/{n_a['id']}").status_code == 404

        assert client_b.get("/api/ai/conversations").json() == []
        assert client_b.get(f"/api/ai/conversations/{conv_a['id']}").status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_catalogue_inventory_and_invoice_stock_deduction(client, make_customer):
    cust = make_customer("Retail Buyer")

    # 1. Create physical product (stock=10, low_stock_threshold=4) and a service
    prod_resp = client.post(
        "/api/products",
        json={
            "name": "Wireless Barcode Scanner",
            "sku": "WBS-001",
            "category": "Hardware",
            "item_type": "product",
            "unit": "pcs",
            "selling_price": "2500.00",
            "tax_percent": 18,
            "stock_quantity": 10,
            "min_stock_threshold": 4,
        },
    )
    assert prod_resp.status_code == 201, prod_resp.text
    prod = prod_resp.json()
    assert prod["stock_quantity"] == 10
    assert prod["stock_status"] == "in_stock"

    svc_resp = client.post(
        "/api/products",
        json={
            "name": "On-site Setup Service",
            "sku": "SVC-001",
            "category": "Services",
            "item_type": "service",
            "unit": "hrs",
            "selling_price": "1500.00",
            "tax_percent": 18,
        },
    )
    assert svc_resp.status_code == 201
    svc = svc_resp.json()
    assert svc["stock_status"] == "service"

    # 2. Negative stock protection on manual adjustment
    neg_adj = client.post(
        f"/api/products/{prod['id']}/stock",
        json={"movement_type": "adjustment", "quantity_change": -50, "reason": "Too much"},
    )
    assert neg_adj.status_code in (409, 422)

    # 3. Restock +5 -> stock becomes 15
    restock = client.post(
        f"/api/products/{prod['id']}/stock",
        json={"movement_type": "restock", "quantity_change": 5, "reason": "Supplier delivery"},
    )
    assert restock.status_code in (200, 201)
    assert restock.json()["balance_after"] == 15

    # 4. Create DRAFT invoice linked to product (qty=12) and service (qty=2)
    today = date.today()
    inv_resp = client.post(
        "/api/invoices",
        json={
            "customer_id": cust["id"],
            "invoice_date": today.isoformat(),
            "due_date": (today + timedelta(days=15)).isoformat(),
            "description": "Hardware + Setup",
            "tax_percent": 18,
            "items": [
                {
                    "product_id": prod["id"],
                    "description": prod["name"],
                    "quantity": 12,
                    "unit_price": "2500.00",
                },
                {
                    "product_id": svc["id"],
                    "description": svc["name"],
                    "quantity": 2,
                    "unit_price": "1500.00",
                },
            ],
        },
    )
    assert inv_resp.status_code == 201, inv_resp.text
    inv = inv_resp.json()

    # Draft must NOT deduct stock yet!
    assert client.get(f"/api/products/{prod['id']}").json()["stock_quantity"] == 15

    # 5. Send invoice -> deducts 12 atomically -> remaining stock = 3 (low_stock!)
    send_resp = client.post(f"/api/invoices/{inv['id']}/send")
    assert send_resp.status_code == 200, send_resp.text

    prod_after = client.get(f"/api/products/{prod['id']}").json()
    assert prod_after["stock_quantity"] == 3
    assert prod_after["stock_status"] == "low_stock"

    # Dashboard alerts now include Low Stock alert
    dash = client.get("/api/dashboard").json()
    assert any(a["entity_type"] == "product" for a in dash["actionable_alerts"])

    # 6. Recording partial/full payments must NOT deduct stock again
    pay = client.post(
        "/api/payments",
        json={"invoice_id": inv["id"], "amount": "10000.00", "method": "upi"},
    )
    assert pay.status_code == 201
    assert client.get(f"/api/products/{prod['id']}").json()["stock_quantity"] == 3

    # 7. Inventory summary shows movement ledger
    summary = client.get("/api/inventory/summary").json()
    assert summary["low_stock_count"] == 1
    assert any(m["movement_type"] == "sale" and m["quantity_change"] == -12 for m in summary["recent_movements"])


def test_business_notepad_crud_and_checklist(client):
    create = client.post(
        "/api/notes",
        json={
            "title": "Weekly Supplier Follow-ups",
            "category": "Operations",
            "content": "Confirm delivery schedule.",
            "is_pinned": True,
            "checklist": [
                {"id": "1", "text": "Call packaging vendor", "done": False},
                {"id": "2", "text": "Verify GST filing", "done": True},
            ],
        },
    )
    assert create.status_code == 201, create.text
    note = create.json()
    assert note["is_pinned"] is True
    assert len(note["checklist"]) == 2

    # Search notes
    listed = client.get("/api/notes", params={"search": "Supplier"}).json()
    assert len(listed) == 1

    # Update note
    upd = client.put(
        f"/api/notes/{note['id']}",
        json={
            "title": "Weekly Supplier Follow-ups (Updated)",
            "category": "Operations",
            "content": "Confirmed for Friday.",
            "is_pinned": False,
            "checklist": [
                {"id": "1", "text": "Call packaging vendor", "done": True},
            ],
        },
    )
    assert upd.status_code == 200
    assert upd.json()["checklist"][0]["done"] is True

    # Delete note
    assert client.delete(f"/api/notes/{note['id']}").status_code == 204
    assert client.get("/api/notes").json() == []


def test_business_logo_upload_validation(client):
    # Minimal valid 1x1 PNG bytes
    png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
        b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    # Reject invalid file type
    bad = client.post(
        "/api/uploads/business-logo",
        files={"file": ("evil.exe", b"MZ\x90\x00notanimage", "application/octet-stream")},
    )
    assert bad.status_code == 422

    # Accept valid PNG and serve it back to the owner
    ok = client.post(
        "/api/uploads/business-logo",
        files={"file": ("logo.png", png_bytes, "image/png")},
    )
    assert ok.status_code == 200, ok.text
    logo_url = ok.json()["logo_url"]
    assert logo_url.startswith("/api/uploads/")

    fetched = client.get(logo_url)
    assert fetched.status_code == 200
    assert fetched.headers["content-type"] == "image/png"
