"""Tests for the dual demonstration businesses (100 products) and inventory-aware AI tools."""

from datetime import date
from pathlib import Path
import sys

from fastapi.testclient import TestClient

from app.database.session import get_db
from app.main import app
from app.services import ai_tools

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "backend" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from seed_dual_demo import (  # noqa: E402
    FURNITURE_EMAIL,
    STATIONERY_EMAIL,
    seed_all_demo_businesses,
)


def test_dual_demo_seed_isolation_inventory_and_ai_tools(session_factory):
    def override_get_db():
        s = session_factory()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        # 1. Create a real user FIRST to prove seeding NEVER deletes or overwrites real accounts
        real_client = TestClient(app)
        reg = real_client.post(
            "/api/auth/register",
            json={
                "full_name": "Real User",
                "email": "real.owner@example.in",
                "password": "RealPassword123!",
                "confirm_password": "RealPassword123!",
            },
        )
        assert reg.status_code == 201
        onb = real_client.post(
            "/api/business/onboarding",
            json={"name": "Real Bakery", "owner_name": "Real User", "currency": "INR"},
        )
        assert onb.status_code in (200, 201)
        real_client.post("/api/customers", json={"name": "Real Bakery Client"})

        # 2. Seed both demo businesses into the isolated test DB
        db = session_factory()
        try:
            res = seed_all_demo_businesses(
                db,
                stationery_password="TestStationeryPass!1",
                furniture_password="TestFurniturePass!2",
                reset=True,
            )
            assert res["stationery"]["products"] == 50
            assert res["furniture"]["products"] == 50
        finally:
            db.close()

        # Confirm real user's data is 100% intact
        assert len(real_client.get("/api/customers").json()["items"]) == 1
        assert real_client.get("/api/products").json() == []

        # 3. Sign in independently as Business A (Stationery) and Business B (Furniture)
        client_a = TestClient(app)
        login_a = client_a.post(
            "/api/auth/login",
            json={"email": STATIONERY_EMAIL, "password": "TestStationeryPass!1"},
        )
        assert login_a.status_code == 200
        assert login_a.json()["business"]["name"] == "Urban Stationery & Office Supplies"

        client_b = TestClient(app)
        login_b = client_b.post(
            "/api/auth/login",
            json={"email": FURNITURE_EMAIL, "password": "TestFurniturePass!2"},
        )
        assert login_b.status_code == 200
        assert login_b.json()["business"]["name"] == "Oakwood Furniture Studio"

        # 4. Verify exactly 50 products & exact category counts per business
        prods_a = client_a.get("/api/products").json()
        prods_b = client_b.get("/api/products").json()
        assert len(prods_a) == 50
        assert len(prods_b) == 50

        cats_a = {}
        for p in prods_a:
            cats_a[p["category"]] = cats_a.get(p["category"], 0) + 1
        assert cats_a == {
            "Paper and notebooks": 10,
            "Pens and writing supplies": 10,
            "Office supplies": 10,
            "Office equipment": 10,
            "Art and stationery accessories": 10,
        }

        cats_b = {}
        for p in prods_b:
            cats_b[p["category"]] = cats_b.get(p["category"], 0) + 1
        assert cats_b == {
            "Sofas and seating": 10,
            "Beds and bedroom furniture": 10,
            "Tables and dining furniture": 10,
            "Storage and cabinets": 5,
            "Home and office furniture accessories": 5,
            "Office furniture": 10,
        }

        # 5. Verify inventory summaries, low-stock & out-of-stock alerts, and purchase-cost valuation
        inv_a = client_a.get("/api/inventory/summary").json()
        inv_b = client_b.get("/api/inventory/summary").json()
        assert inv_a["total_active_products"] == 50
        assert inv_b["total_active_products"] == 50
        assert inv_a["low_stock_count"] >= 3
        assert inv_a["out_of_stock_count"] >= 1
        assert inv_b["low_stock_count"] >= 3
        assert inv_b["out_of_stock_count"] >= 1
        assert inv_a["inventory_valuation_paise"] > 0
        assert inv_b["inventory_valuation_paise"] > inv_a["inventory_valuation_paise"]

        # 6. Verify strict isolation across customers, invoices, payments, expenses, notes
        custs_a = {c["name"] for c in client_a.get("/api/customers").json()["items"]}
        custs_b = {c["name"] for c in client_b.get("/api/customers").json()["items"]}
        assert len(custs_a) == 9
        assert len(custs_b) == 9
        assert custs_a.isdisjoint(custs_b)

        invs_a = client_a.get("/api/invoices").json()["items"]
        invs_b = client_b.get("/api/invoices").json()["items"]
        assert len(invs_a) == 11
        assert len(invs_b) == 11
        assert client_b.get(f"/api/invoices/{invs_a[0]['id']}").status_code == 404

        assert len(client_a.get("/api/notes").json()) == 5
        assert len(client_b.get("/api/notes").json()) == 5

        # 7. Verify read-only inventory AI tools are strictly scoped per business
        db = session_factory()
        try:
            biz_a_id = login_a.json()["business"]["id"]
            biz_b_id = login_b.json()["business"]["id"]

            ai_inv_a = ai_tools.get_inventory_summary(db, date.today(), business_id=biz_a_id)
            ai_inv_b = ai_tools.get_inventory_summary(db, date.today(), business_id=biz_b_id)
            assert ai_inv_a["total_active_products"] == 50
            assert ai_inv_b["total_active_products"] == 50
            assert ai_inv_a["inventory_valuation_paise"] != ai_inv_b["inventory_valuation_paise"]

            # Searching for "Sofa" in Stationery returns 0; in Furniture returns > 0
            sofa_in_a = ai_tools.search_products(db, date.today(), query="Sofa", business_id=biz_a_id)
            sofa_in_b = ai_tools.search_products(db, date.today(), query="Sofa", business_id=biz_b_id)
            assert sofa_in_a["match_count"] == 0
            assert sofa_in_b["match_count"] >= 4
        finally:
            db.close()
    finally:
        app.dependency_overrides.clear()
