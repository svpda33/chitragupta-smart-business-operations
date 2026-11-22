"""Tests for the Gemini Finance Copilot backend service, tools, security, and API routes."""

from datetime import date
import json
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.services import ai_service, ai_tools


def _make_fake_settings(api_key: str | None = "test-fake-key-not-real", model: str = "gemini-2.5-flash"):
    return Settings(
        gemini_api_key=api_key,
        gemini_model=model,
        ai_request_timeout_seconds=15,
    )


class _FakeModelsAPI:
    """Fake google-genai models API that simulates model listing and multi-round tool calling."""

    def __init__(self, responses: list[SimpleNamespace], available_models: list[str] | None = None, raise_error: Exception | None = None):
        self._responses = list(responses)
        self._available = available_models if available_models is not None else ["models/gemini-2.5-flash"]
        self._raise_error = raise_error
        self.calls: list[dict] = []

    def list(self):
        return [
            SimpleNamespace(name=m, supported_actions=["generateContent"])
            for m in self._available
        ]

    def generate_content(self, model: str, contents, config=None):
        self.calls.append({"model": model, "contents": contents})
        if self._raise_error:
            raise self._raise_error
        return self._responses.pop(0)


class _FakeGenAIClient:
    def __init__(self, models_api: _FakeModelsAPI):
        self.models = models_api


def test_ai_status_and_missing_api_key(client: TestClient):
    """Test 1: Missing GEMINI_API_KEY returns clear 503 configuration error and status reports unconfigured."""
    with patch.object(ai_service, "get_settings", return_value=_make_fake_settings(api_key=None)):
        status_res = client.get("/api/ai/status")
        assert status_res.status_code == 200
        assert status_res.json()["configured"] is False

        chat_res = client.post("/api/ai/chat", json={"message": "Give me a financial summary."})
        assert chat_res.status_code == 503
        assert "GEMINI_API_KEY" in chat_res.json()["detail"]


def test_ai_gemini_api_failure_handled_gracefully(client: TestClient):
    """Test 2: Upstream Gemini API failure returns clean 502 without leaking API keys."""
    secret_key = "SUPER-SECRET-TEST-KEY-999999"
    fake_models = _FakeModelsAPI(responses=[], raise_error=RuntimeError(f"Connection failed for {secret_key}"))
    fake_client = _FakeGenAIClient(fake_models)

    with (
        patch.object(ai_service, "get_settings", return_value=_make_fake_settings(api_key=secret_key)),
        patch.object(ai_service, "_create_genai_client", return_value=fake_client),
    ):
        res = client.post("/api/ai/chat", json={"message": "What is my balance?"})
        assert res.status_code == 502
        body = res.json()
        assert "failed to respond" in body["detail"].lower()
        assert secret_key not in json.dumps(body)


def test_ai_successful_tool_calling_financial_overview(client: TestClient):
    """Test 3 & 4: Successful assistant response with real backend tool execution and evidence."""
    client.post("/api/demo/seed?force=true")

    tool_call_resp = SimpleNamespace(
        function_calls=[SimpleNamespace(name="get_financial_overview", args={})],
        candidates=[],
        text="",
    )
    final_resp = SimpleNamespace(
        function_calls=[],
        candidates=[],
        text="As of today, your total outstanding receivables are ₹3,28,160.00 with ₹1,79,360.00 overdue.",
    )
    fake_models = _FakeModelsAPI(responses=[tool_call_resp, final_resp])
    fake_client = _FakeGenAIClient(fake_models)

    with (
        patch.object(ai_service, "get_settings", return_value=_make_fake_settings()),
        patch.object(ai_service, "_create_genai_client", return_value=fake_client),
    ):
        res = client.post("/api/ai/chat", json={"message": "Give me a complete financial health summary."})
        assert res.status_code == 200
        data = res.json()
        assert data["model"] == "gemini-2.5-flash"
        assert data["as_of_date"] == date.today().isoformat()
        assert "get_financial_overview" in data["tools_used"]
        assert len(data["evidence"]) >= 3
        assert any(e["label"] == "Total Outstanding" and e["kind"] == "actual" for e in data["evidence"])
        assert len(data["suggested_actions"]) >= 1
        assert "₹3,28,160.00" in data["reply"]


def test_ai_overdue_invoice_query(client: TestClient):
    """Test 5: Overdue invoice queries invoke get_overdue_invoices and return verified overdue evidence."""
    client.post("/api/demo/seed?force=true")

    tool_call_resp = SimpleNamespace(
        function_calls=[SimpleNamespace(name="get_overdue_invoices", args={})],
        candidates=[],
        text="",
    )
    final_resp = SimpleNamespace(
        function_calls=[],
        candidates=[],
        text="You have 3 overdue invoices requiring immediate follow-up, led by INV-0004.",
    )
    fake_models = _FakeModelsAPI(responses=[tool_call_resp, final_resp])

    with (
        patch.object(ai_service, "get_settings", return_value=_make_fake_settings()),
        patch.object(ai_service, "_create_genai_client", return_value=_FakeGenAIClient(fake_models)),
    ):
        res = client.post("/api/ai/chat", json={"message": "Which invoices need immediate attention?"})
        assert res.status_code == 200
        data = res.json()
        assert "get_overdue_invoices" in data["tools_used"]
        assert any(e["label"] == "Overdue Balance" for e in data["evidence"])
        assert any(a["url"] == "/reminders" for a in data["suggested_actions"])


def test_ai_cashflow_forecast_explanation(client: TestClient):
    """Test 6: Forecast queries invoke get_cashflow_forecast and label evidence as forecast."""
    client.post("/api/demo/seed?force=true")

    tool_call_resp = SimpleNamespace(
        function_calls=[SimpleNamespace(name="get_cashflow_forecast", args={"days": 60})],
        candidates=[],
        text="",
    )
    final_resp = SimpleNamespace(
        function_calls=[],
        candidates=[],
        text="Based on your 60-day forecast estimate, cash remains above your safety reserve.",
    )
    fake_models = _FakeModelsAPI(responses=[tool_call_resp, final_resp])

    with (
        patch.object(ai_service, "get_settings", return_value=_make_fake_settings()),
        patch.object(ai_service, "_create_genai_client", return_value=_FakeGenAIClient(fake_models)),
    ):
        res = client.post("/api/ai/chat", json={"message": "Explain my 60-day cash-flow forecast."})
        assert res.status_code == 200
        data = res.json()
        assert "get_cashflow_forecast" in data["tools_used"]
        assert any(e["kind"] == "forecast" for e in data["evidence"])
        assert any(a["url"] == "/cash-flow" for a in data["suggested_actions"])


def test_ai_whatif_simulation_does_not_mutate_records(client: TestClient):
    """Test 7 & 8: What-if simulation via AI never modifies actual database records, and unknown tools are rejected."""
    client.post("/api/demo/seed?force=true")

    invs_before = client.get("/api/invoices?page_size=100").json()
    pmts_before = client.get("/api/payments?page_size=100").json()

    tool_call_resp = SimpleNamespace(
        function_calls=[
            SimpleNamespace(name="simulate_payment_delay", args={"delay_days": 15, "days": 30}),
            SimpleNamespace(name="drop_all_tables", args={}),  # unauthorized tool attempt
        ],
        candidates=[],
        text="",
    )
    final_resp = SimpleNamespace(
        function_calls=[],
        candidates=[],
        text="Simulated a 15-day delay for your top debtor without modifying any actual records.",
    )
    fake_models = _FakeModelsAPI(responses=[tool_call_resp, final_resp])

    with (
        patch.object(ai_service, "get_settings", return_value=_make_fake_settings()),
        patch.object(ai_service, "_create_genai_client", return_value=_FakeGenAIClient(fake_models)),
    ):
        res = client.post("/api/ai/chat", json={"message": "What happens if my biggest customer pays 15 days late?"})
        assert res.status_code == 200
        data = res.json()
        assert "simulate_payment_delay" in data["tools_used"]
        assert any(e["kind"] == "simulation" for e in data["evidence"])

    # Verify zero mutations to database records
    invs_after = client.get("/api/invoices?page_size=100").json()
    pmts_after = client.get("/api/payments?page_size=100").json()
    assert invs_after == invs_before
    assert pmts_after == pmts_before


def test_ai_tools_redact_sensitive_pii_and_banking_info(client: TestClient, db):
    """Test 9: Sensitive personal & banking info is never included in tool outputs sent to Gemini."""
    client.post("/api/demo/seed?force=true")
    today = date.today()

    outputs = [
        ai_tools.get_financial_overview(db, today=today),
        ai_tools.get_top_debtors(db, today=today, limit=10),
        ai_tools.get_overdue_invoices(db, today=today),
        ai_tools.get_customer_summary(db, today=today, customer_query="Apex Learning"),
        ai_tools.get_invoice_details(db, today=today, invoice_query="INV-0004"),
        ai_tools.get_cashflow_forecast(db, today=today, days=30),
        ai_tools.simulate_payment_delay(db, today=today, delay_days=15),
        ai_tools.get_upcoming_expenses(db, today=today, days=30),
        ai_tools.generate_payment_reminder(db, today=today, invoice_query="INV-0004", channel="whatsapp"),
    ]

    serialized = json.dumps(outputs)

    # Sensitive banking, tax, and personal contact info from demo seed must NEVER appear in AI context
    sensitive_values = [
        "50100456789012",              # bank account number
        "HDFC0001234",                 # IFSC code
        "aditi.consulting@okhdfcbank", # UPI ID
        "29AAAAA1234A1Z8",             # GSTIN
        "+91 98765 43210",             # owner phone
        "aditi.sharma@chitragupta.local",  # owner email
        "finance@apexlearning.edu.in", # customer email
        "+91 99000 45678",             # customer phone
        "88 Jayanagar 4th Block",      # customer street address
    ]
    for secret in sensitive_values:
        assert secret not in serialized, f"Sensitive value leaked into AI tool output: {secret}"

    # Verify reminder draft explicitly states it was not sent automatically
    reminder_out = outputs[-1]
    assert reminder_out["sent_automatically"] is False
    assert "draft" in reminder_out


def test_ai_conversation_persistence_lifecycle(client: TestClient):
    """Test 10: Persistent conversation history CRUD, search, continuation with bounded context, rename & delete."""
    client.post("/api/demo/seed?force=true")

    # 1. Start a chat without conversation_id -> auto-creates a persisted conversation
    resp1 = SimpleNamespace(function_calls=[], candidates=[], text="Your cash balance is healthy.")
    resp2 = SimpleNamespace(function_calls=[], candidates=[], text="Follow up with Apex Learning Academy first.")
    fake_models = _FakeModelsAPI(responses=[resp1, resp2])
    fake_client = _FakeGenAIClient(fake_models)

    with (
        patch.object(ai_service, "get_settings", return_value=_make_fake_settings()),
        patch.object(ai_service, "_create_genai_client", return_value=fake_client),
    ):
        chat1 = client.post("/api/ai/chat", json={"message": "How is my cash health?"})
        assert chat1.status_code == 200
        c1_data = chat1.json()
        conv_id = c1_data["conversation_id"]
        assert conv_id is not None
        assert "cash health" in c1_data["conversation_title"].lower()

        # 2. Continue the same conversation -> backend loads prior persisted messages as context
        chat2 = client.post(
            "/api/ai/chat",
            json={"message": "Who should I chase first?", "conversation_id": conv_id},
        )
        assert chat2.status_code == 200
        assert chat2.json()["conversation_id"] == conv_id
        # Second Gemini call should include prior 2 messages + new prompt = 3 contents
        assert len(fake_models.calls[1]["contents"]) == 3

    # 3. List and search conversations
    list_res = client.get("/api/ai/conversations")
    assert list_res.status_code == 200
    items = list_res.json()
    assert len(items) == 1
    assert items[0]["id"] == conv_id
    assert items[0]["message_count"] == 4

    search_res = client.get("/api/ai/conversations?search=Apex")
    assert search_res.status_code == 200
    assert len(search_res.json()) == 1

    # 4. Get full conversation detail
    detail_res = client.get(f"/api/ai/conversations/{conv_id}")
    assert detail_res.status_code == 200
    assert len(detail_res.json()["messages"]) == 4

    # 5. Rename conversation
    rename_res = client.patch(
        f"/api/ai/conversations/{conv_id}",
        json={"title": "Q4 Cash Review"},
    )
    assert rename_res.status_code == 200
    assert rename_res.json()["title"] == "Q4 Cash Review"

    # 6. Delete conversation
    del_res = client.delete(f"/api/ai/conversations/{conv_id}")
    assert del_res.status_code == 204
    assert client.get(f"/api/ai/conversations/{conv_id}").status_code == 404

