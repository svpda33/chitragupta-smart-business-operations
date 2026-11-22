"""Shared test fixtures: a fresh SQLite file per test, overridden get_db, and a TestClient.

The real database (instance/chitragupta.db) is never touched: get_db is overridden
and the lifespan (which runs create_all on the real engine) is not triggered.
"""

from collections.abc import Callable, Iterator
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

import app.models  # noqa: F401  (registers tables on Base.metadata)
from app.database.session import Base, get_db
from app.main import app

DEFAULT_ITEMS = [
    {"description": "Design", "quantity": 2, "unit_price": "1000.00"},
    {"description": "Hosting", "quantity": 1, "unit_price": "250.50"},
]
# 2 x 1000.00 + 1 x 250.50 = 225050 paise subtotal; 18% tax = 40509; total 265559.
DEFAULT_TOTAL_PAISE = 265559


@pytest.fixture()
def session_factory(tmp_path) -> Iterator[sessionmaker]:
    db_file = tmp_path / "test_chitragupta.db"
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    yield factory
    engine.dispose()


@pytest.fixture()
def db(session_factory) -> Iterator[Session]:
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def anon_client(session_factory) -> Iterator[TestClient]:
    """Unauthenticated TestClient against the isolated per-test SQLite DB."""
    def override_get_db() -> Iterator[Session]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture()
def client(session_factory) -> Iterator[TestClient]:
    """Authenticated TestClient with an onboarded default business."""
    def override_get_db() -> Iterator[Session]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        tc = TestClient(app)
        reg = tc.post(
            "/api/auth/register",
            json={
                "full_name": "Test Owner",
                "email": "owner@testbiz.local",
                "password": "TestPassword123!",
                "confirm_password": "TestPassword123!",
            },
        )
        assert reg.status_code == 201, reg.text
        onb = tc.post(
            "/api/business/onboarding",
            json={
                "name": "Test Business Studio",
                "category": "Services & Consulting",
                "owner_name": "Test Owner",
                "email": "owner@testbiz.local",
                "currency": "INR",
                "default_payment_terms_days": 15,
                "default_tax_percent": 18,
                "initial_cash_balance": "250000.00",
                "monthly_recurring_expenses": "65000.00",
                "safety_cash_threshold": "50000.00",
            },
        )
        assert onb.status_code in (200, 201), onb.text
        yield tc
    finally:
        app.dependency_overrides.clear()


@pytest.fixture()
def make_customer(client) -> Callable[..., dict]:
    def _make(name: str = "Acme Traders", **extra) -> dict:
        response = client.post("/api/customers", json={"name": name, **extra})
        assert response.status_code == 201, response.text
        return response.json()

    return _make


@pytest.fixture()
def make_invoice(client) -> Callable[..., dict]:
    """Create a draft invoice.

    invoice_date = today - invoice_days_ago; due_date = today + due_days.
    Defaults give a draft due in 10 days with the 265559-paise example total.
    """

    def _make(
        customer_id: int,
        due_days: int = 10,
        invoice_days_ago: int = 0,
        items: list[dict] | None = None,
        tax_percent: int = 18,
        **extra,
    ) -> dict:
        today = date.today()
        body = {
            "customer_id": customer_id,
            "invoice_date": (today - timedelta(days=invoice_days_ago)).isoformat(),
            "due_date": (today + timedelta(days=due_days)).isoformat(),
            "description": "Consulting services",
            "tax_percent": tax_percent,
            "items": items if items is not None else DEFAULT_ITEMS,
            **extra,
        }
        response = client.post("/api/invoices", json=body)
        assert response.status_code == 201, response.text
        return response.json()

    return _make


@pytest.fixture()
def make_sent_invoice(client, make_invoice) -> Callable[..., dict]:
    def _make(customer_id: int, **kwargs) -> dict:
        invoice = make_invoice(customer_id, **kwargs)
        response = client.post(f"/api/invoices/{invoice['id']}/send")
        assert response.status_code == 200, response.text
        return response.json()

    return _make


@pytest.fixture()
def record_payment(client) -> Callable[..., dict]:
    def _record(invoice_id: int, amount: str, **extra):
        body = {"invoice_id": invoice_id, "amount": amount, "method": "upi", **extra}
        return client.post("/api/payments", json=body)

    return _record
