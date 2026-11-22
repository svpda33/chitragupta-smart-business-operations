from datetime import date, timedelta

from app.services.status import derive_invoice_status

TODAY = date(2026, 3, 10)


def test_draft_is_always_draft():
    assert derive_invoice_status("draft", 100000, 0, TODAY - timedelta(days=5), TODAY) == ("draft", 0)


def test_sent_unpaid_not_due_is_pending():
    assert derive_invoice_status("sent", 100000, 0, TODAY + timedelta(days=10), TODAY) == ("pending", 0)


def test_due_today_is_not_overdue():
    assert derive_invoice_status("sent", 100000, 0, TODAY, TODAY) == ("pending", 0)


def test_partly_paid_not_due_is_partially_paid():
    assert derive_invoice_status("sent", 100000, 40000, TODAY + timedelta(days=10), TODAY) == (
        "partially_paid",
        0,
    )


def test_fully_paid_is_paid_even_if_past_due():
    assert derive_invoice_status("sent", 100000, 100000, TODAY - timedelta(days=10), TODAY) == ("paid", 0)


def test_unpaid_past_due_is_overdue_with_days():
    assert derive_invoice_status("sent", 100000, 0, TODAY - timedelta(days=10), TODAY) == ("overdue", 10)


def test_partly_paid_past_due_is_overdue_with_days():
    assert derive_invoice_status("sent", 100000, 25000, TODAY - timedelta(days=3), TODAY) == ("overdue", 3)
