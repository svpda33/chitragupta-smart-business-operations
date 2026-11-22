"""Gemini Finance Copilot orchestration service using the official google-genai SDK.

Security & trust guarantees:
- API key is read exclusively from backend environment/config; never hardcoded, logged, or exposed.
- Only whitelisted read-only financial tools in ai_tools.py can be invoked.
- Model availability is verified against the API key instead of blindly assuming a model ID.
- Verified Python-computed evidence figures are returned alongside the model's explanation.
"""

from datetime import date
import logging
from typing import Any

from google import genai
from google.genai import types
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.schemas.ai import AiChatRequest
from app.services import ai_conversation_service, ai_tools

logger = logging.getLogger(__name__)

MAX_HISTORY_MESSAGES = 8
MAX_TOOL_ROUNDS = 5

_RESOLVED_MODEL_CACHE: dict[tuple[str, str], str] = {}

SYSTEM_INSTRUCTION = """You are the Chitragupta Finance Copilot — an AI financial operations assistant built for a one-person Indian micro-business.

STRICT RULES:
1. ALWAYS call the provided read-only tools to fetch real Chitragupta figures before answering financial questions. Never invent or guess rupee amounts, customer names, invoice numbers, or dates.
2. All calculations are performed by Python backend services. Present those verified figures clearly in INR (₹).
3. ALWAYS clearly distinguish:
   - **Actual ledger figures** (outstanding receivables, overdue amounts, collected payments, invoiced totals)
   - **Forecast estimates** (30/60/90-day cash projections — never guaranteed cash)
   - **What-If simulations** (non-destructive delay scenarios — actual records are never modified)
4. Always mention the `as_of_date` used for the figures.
5. For reminder drafts, NEVER claim a message was sent automatically — clearly note it is a ready-to-use draft.
6. Never make financial guarantees or legal/tax promises. If information is missing or a customer/invoice is not found, state that plainly.
7. Be concise, practical, structured with clear bullet points, and focused on actionable next steps for a solo business owner.
"""


def _build_tool_declarations() -> list[types.FunctionDeclaration]:
    return [
        types.FunctionDeclaration(
            name="get_financial_overview",
            description="Get actual ledger KPIs: total outstanding, total overdue, collected payments, invoiced amounts, estimated cash on hand, safety reserve, runway days, ageing breakdown, and active business alerts.",
            parameters=types.Schema(type=types.Type.OBJECT, properties={}),
        ),
        types.FunctionDeclaration(
            name="get_top_debtors",
            description="Get customers with the highest outstanding balances, overdue amounts, and receivables concentration percentages.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "limit": types.Schema(
                        type=types.Type.INTEGER,
                        description="Maximum number of top debtors to return (1 to 20, default 5).",
                    ),
                },
            ),
        ),
        types.FunctionDeclaration(
            name="get_overdue_invoices",
            description="List all currently overdue sent invoices with customer names, due dates, days overdue, and outstanding balances.",
            parameters=types.Schema(type=types.Type.OBJECT, properties={}),
        ),
        types.FunctionDeclaration(
            name="get_customer_summary",
            description="Get financial summary, invoices, and payment history for a specific customer by name or ID.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "customer_query": types.Schema(
                        type=types.Type.STRING,
                        description="Customer name (full or partial) or numeric customer ID.",
                    ),
                },
                required=["customer_query"],
            ),
        ),
        types.FunctionDeclaration(
            name="get_invoice_details",
            description="Get full details, line items, status, payments, and outstanding balance for a specific invoice by invoice number (e.g. INV-0004) or ID.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "invoice_query": types.Schema(
                        type=types.Type.STRING,
                        description="Invoice number (e.g. INV-0004) or numeric invoice ID.",
                    ),
                },
                required=["invoice_query"],
            ),
        ),
        types.FunctionDeclaration(
            name="get_cashflow_forecast",
            description="Get 30, 60, or 90-day cash-flow forecast estimates including expected inflows, scheduled outflows, projected ending cash, minimum balance, safety reserve comparison, and shortage alerts.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "days": types.Schema(
                        type=types.Type.INTEGER,
                        description="Forecast horizon in days: 30, 60, or 90 (default 30).",
                    ),
                },
            ),
        ),
        types.FunctionDeclaration(
            name="simulate_payment_delay",
            description="Run a read-only what-if simulation for delayed customer payment (7, 15, or 30 days) without modifying any database records. If neither customer_query nor invoice_query is provided, automatically simulates the biggest debtor.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "delay_days": types.Schema(
                        type=types.Type.INTEGER,
                        description="Number of days the payment is delayed (e.g. 7, 15, or 30).",
                    ),
                    "customer_query": types.Schema(
                        type=types.Type.STRING,
                        description="Optional customer name or ID to delay.",
                    ),
                    "invoice_query": types.Schema(
                        type=types.Type.STRING,
                        description="Optional invoice number or ID to delay.",
                    ),
                    "days": types.Schema(
                        type=types.Type.INTEGER,
                        description="Forecast horizon in days: 30, 60, or 90 (default 30).",
                    ),
                },
            ),
        ),
        types.FunctionDeclaration(
            name="get_upcoming_expenses",
            description="List upcoming scheduled recurring and one-off business expenses for the next N days (default 30).",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "days": types.Schema(
                        type=types.Type.INTEGER,
                        description="Lookahead window in days (1 to 90, default 30).",
                    ),
                },
            ),
        ),
        types.FunctionDeclaration(
            name="generate_payment_reminder",
            description="Generate a personalized WhatsApp, email, or SMS payment reminder draft for an unpaid sent invoice. Does NOT send automatically.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "invoice_query": types.Schema(
                        type=types.Type.STRING,
                        description="Invoice number (e.g. INV-0004) or numeric invoice ID.",
                    ),
                    "channel": types.Schema(
                        type=types.Type.STRING,
                        description="Preferred channel: whatsapp, email, or sms (default whatsapp).",
                    ),
                },
                required=["invoice_query"],
            ),
        ),
        types.FunctionDeclaration(
            name="get_inventory_summary",
            description="Get actual inventory ledger summary: total active products, total stock units, low-stock count, out-of-stock count, purchase-cost inventory valuation, items needing restock, and recent stock movements.",
            parameters=types.Schema(type=types.Type.OBJECT, properties={}),
        ),
        types.FunctionDeclaration(
            name="search_products",
            description="Search the signed-in business's product and service catalogue by name/SKU query, category, or stock status (in_stock, low_stock, out_of_stock).",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "query": types.Schema(
                        type=types.Type.STRING,
                        description="Optional product name or SKU search string.",
                    ),
                    "category": types.Schema(
                        type=types.Type.STRING,
                        description="Optional product category filter.",
                    ),
                    "stock_status": types.Schema(
                        type=types.Type.STRING,
                        description="Optional stock status filter: in_stock, low_stock, or out_of_stock.",
                    ),
                },
            ),
        ),
    ]


def _execute_tool(
    db: Session,
    today: date,
    name: str,
    args: dict[str, Any],
    business_id: int | None = None,
) -> dict[str, Any]:
    """Strictly dispatch only to whitelisted read-only financial tools."""
    args = args or {}
    if name == "get_financial_overview":
        return ai_tools.get_financial_overview(db, today=today, business_id=business_id)
    if name == "get_top_debtors":
        return ai_tools.get_top_debtors(
            db, today=today, limit=args.get("limit", 5), business_id=business_id
        )
    if name == "get_overdue_invoices":
        return ai_tools.get_overdue_invoices(db, today=today, business_id=business_id)
    if name == "get_customer_summary":
        return ai_tools.get_customer_summary(
            db, today=today, customer_query=args.get("customer_query", ""), business_id=business_id
        )
    if name == "get_invoice_details":
        return ai_tools.get_invoice_details(
            db, today=today, invoice_query=args.get("invoice_query", ""), business_id=business_id
        )
    if name == "get_cashflow_forecast":
        return ai_tools.get_cashflow_forecast(
            db, today=today, days=args.get("days", 30), business_id=business_id
        )
    if name == "simulate_payment_delay":
        return ai_tools.simulate_payment_delay(
            db,
            today=today,
            delay_days=args.get("delay_days", 15),
            customer_query=args.get("customer_query"),
            invoice_query=args.get("invoice_query"),
            days=args.get("days", 30),
            business_id=business_id,
        )
    if name == "get_upcoming_expenses":
        return ai_tools.get_upcoming_expenses(
            db, today=today, days=args.get("days", 30), business_id=business_id
        )
    if name == "generate_payment_reminder":
        return ai_tools.generate_payment_reminder(
            db,
            today=today,
            invoice_query=args.get("invoice_query", ""),
            channel=args.get("channel", "whatsapp"),
            business_id=business_id,
        )
    if name == "get_inventory_summary":
        return ai_tools.get_inventory_summary(db, today=today, business_id=business_id)
    if name == "search_products":
        return ai_tools.search_products(
            db,
            today=today,
            query=args.get("query"),
            category=args.get("category"),
            stock_status=args.get("stock_status"),
            business_id=business_id,
        )
    return {"error": f"Tool '{name}' is not permitted."}


def _extract_evidence_and_actions(
    tool_outputs: list[tuple[str, dict[str, Any]]]
) -> tuple[list[dict], list[dict]]:
    evidence: list[dict] = []
    actions: list[dict] = []
    seen_evidence: set[str] = set()
    seen_urls: set[str] = set()

    def add_ev(label: str, value: str, kind: str = "actual", note: str | None = None):
        if label not in seen_evidence and value is not None:
            seen_evidence.add(label)
            evidence.append({"label": label, "value": value, "kind": kind, "note": note})

    def add_act(label: str, url: str):
        if url not in seen_urls:
            seen_urls.add(url)
            actions.append({"label": label, "url": url})

    for name, data in tool_outputs:
        if not isinstance(data, dict) or data.get("error"):
            continue
        if name == "get_financial_overview":
            add_ev("Total Outstanding", data.get("total_outstanding"), "actual")
            add_ev("Total Overdue", data.get("total_overdue"), "actual", f"{data.get('overdue_invoices_count', 0)} overdue")
            add_ev("Estimated Cash on Hand", data.get("estimated_cash_on_hand"), "actual", f"~{data.get('estimated_runway_days', 0)}d runway")
            add_ev("Collected All-Time", data.get("collected_all_time"), "actual")
            add_act("Open Dashboard", "/")
            if data.get("overdue_invoices_count", 0) > 0:
                add_act("Chase Overdue Reminders", "/reminders")
        elif name == "get_top_debtors":
            debtors = data.get("top_debtors") or []
            if debtors:
                top = debtors[0]
                add_ev(
                    f"Top Debtor: {top['customer_name']}",
                    top["outstanding"],
                    "actual",
                    f"{top['concentration_percent']}% of receivables",
                )
            add_act("View Customers", "/customers")
        elif name == "get_overdue_invoices":
            add_ev("Overdue Balance", data.get("total_overdue"), "actual", f"{data.get('overdue_count', 0)} invoice(s)")
            add_act("Open Payment Reminders", "/reminders")
            add_act("View Overdue Invoices", "/invoices?status=overdue")
        elif name == "get_customer_summary" and data.get("found"):
            add_ev(f"{data['customer_name']} Outstanding", data.get("outstanding"), "actual")
            if data.get("customer_id"):
                add_act(f"Open {data['customer_name']}", f"/customers/{data['customer_id']}")
        elif name == "get_invoice_details" and data.get("found"):
            add_ev(f"{data['invoice_number']} Outstanding", data.get("outstanding"), "actual", f"Status: {data.get('status')}")
            if data.get("invoice_id"):
                add_act(f"View {data['invoice_number']}", f"/invoices/{data['invoice_id']}")
        elif name == "get_cashflow_forecast":
            h = data.get("horizon_days", 30)
            add_ev(f"{h}-Day Projected Cash", data.get("projected_ending_cash"), "forecast", f"Min: {data.get('projected_min_balance')}")
            add_ev(f"{h}-Day Expected Inflows", data.get("expected_inflows"), "forecast")
            add_ev(f"{h}-Day Scheduled Outflows", data.get("scheduled_outflows"), "forecast")
            add_act("Open Cash Flow Forecast", "/cash-flow")
        elif name == "simulate_payment_delay":
            d = data.get("delay_days", 15)
            target = data.get("target_invoice") or data.get("target_customer") or "Payments"
            add_ev(
                f"Simulated Ending Cash (+{d}d)",
                data.get("simulated_ending_cash"),
                "simulation",
                f"vs Baseline {data.get('baseline_ending_cash')} ({target})",
            )
            add_ev(
                f"Simulated Min Balance (+{d}d)",
                data.get("simulated_min_balance"),
                "simulation",
                "Shortfall detected" if data.get("shortfall_detected") else "Above safety reserve",
            )
            add_act("Open What-If Simulator", "/cash-flow")
        elif name == "get_upcoming_expenses":
            add_ev(
                f"Upcoming Expenses ({data.get('horizon_days', 30)}d)",
                data.get("total_upcoming_expenses"),
                "forecast",
                f"{data.get('count', 0)} scheduled item(s)",
            )
            add_act("Manage Expenses in Cash Flow", "/cash-flow")
        elif name == "generate_payment_reminder" and data.get("found"):
            add_ev(
                f"Reminder Draft ({data.get('invoice_number')})",
                data.get("outstanding"),
                "actual",
                "Draft only — not sent automatically",
            )
            add_act("Copy / Send on Reminders Page", "/reminders")
        elif name == "get_inventory_summary":
            add_ev(
                "Active Products",
                f"{data.get('total_active_products', 0)} items ({data.get('total_stock_units', 0)} units)",
                "actual",
            )
            add_ev(
                "Inventory Valuation (Cost)",
                data.get("inventory_valuation_purchase_cost"),
                "actual",
                f"{data.get('low_stock_count', 0)} low · {data.get('out_of_stock_count', 0)} out of stock",
            )
            add_act("Open Inventory Ledger", "/inventory")
            add_act("Open Catalogue", "/catalogue")
        elif name == "search_products":
            add_ev("Catalogue Matches", f"{data.get('match_count', 0)} item(s)", "actual")
            add_act("Open Catalogue", "/catalogue")

    return evidence[:6], actions[:4]


PREFERRED_FLASH_MODELS = (
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-3.8-flash",
)


def _normalize_model_id(name: str) -> str:
    return name[len("models/"):] if name.startswith("models/") else name


def _is_retryable_model_error(exc: Exception) -> bool:
    msg = str(exc)
    return any(code in msg for code in ("404", "NOT_FOUND", "503", "UNAVAILABLE", "504", "DEADLINE_EXCEEDED"))


def _get_candidate_models(client: Any, preferred_model: str, api_key: str) -> list[str]:
    """Return an ordered list of supported Gemini Flash models available to this API key."""
    cache_key = (api_key[-6:] if len(api_key) >= 6 else api_key, preferred_model)
    normalized_pref = _normalize_model_id(preferred_model)

    cached = _RESOLVED_MODEL_CACHE.get(cache_key)
    candidates: list[str] = []
    if cached:
        candidates.append(cached)

    try:
        models = list(client.models.list())
        available_names: list[str] = []
        for m in models:
            m_name = _normalize_model_id(getattr(m, "name", "") or "")
            actions = getattr(m, "supported_actions", None) or getattr(m, "supported_generation_methods", None) or []
            if m_name and (not actions or any("generateContent" in str(a) for a in actions)):
                available_names.append(m_name)

        # Prefer newer 3.x Flash models if configured model is legacy 2.5
        if normalized_pref in available_names and not normalized_pref.startswith("gemini-2.5"):
            if normalized_pref not in candidates:
                candidates.append(normalized_pref)

        for cand in PREFERRED_FLASH_MODELS:
            if cand in available_names and cand not in candidates:
                candidates.append(cand)

        if normalized_pref in available_names and normalized_pref not in candidates:
            candidates.append(normalized_pref)

        if not candidates:
            flash_models = [
                n for n in available_names
                if "gemini" in n and "flash" in n and "embedding" not in n and "image" not in n and "audio" not in n
            ]
            if flash_models:
                candidates.extend(sorted(flash_models, reverse=True))
    except Exception:
        logger.debug("Model availability listing skipped; using configured model %s", normalized_pref)

    if not candidates:
        candidates.append(normalized_pref)
    return candidates


def resolve_available_model(client: Any, preferred_model: str, api_key: str) -> str:
    """Verify model availability against the API key and select a supported Gemini Flash model."""
    return _get_candidate_models(client, preferred_model, api_key)[0]


def _create_genai_client(api_key: str, timeout_seconds: int):
    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=timeout_seconds * 1000),
    )


def get_ai_status() -> dict[str, Any]:
    settings = get_settings()
    configured = bool(settings.gemini_api_key)
    return {
        "configured": configured,
        "configured_model": settings.gemini_model,
        "message": (
            "Gemini API key is configured."
            if configured
            else "GEMINI_API_KEY is not configured. Add it to backend/.env and restart the backend server."
        ),
    }


def chat_with_copilot(
    db: Session,
    req: AiChatRequest,
    today: date | None = None,
    business_id: int | None = None,
) -> dict[str, Any]:
    if today is None:
        today = date.today()

    settings = get_settings()
    if not settings.gemini_api_key:
        raise AppError(
            503,
            "Gemini Finance Copilot is not configured yet. Please add GEMINI_API_KEY to backend/.env and restart the backend server.",
        )

    try:
        client = _create_genai_client(settings.gemini_api_key, settings.ai_request_timeout_seconds)
    except Exception as exc:
        logger.warning("Failed to initialize Gemini client: %s", type(exc).__name__)
        raise AppError(502, "Could not initialize the Gemini AI client. Please check your configuration.") from exc

    candidate_models = _get_candidate_models(client, settings.gemini_model, settings.gemini_api_key)
    model_name = candidate_models[0]
    cache_key = (
        settings.gemini_api_key[-6:] if len(settings.gemini_api_key) >= 6 else settings.gemini_api_key,
        settings.gemini_model,
    )

    def _call_model(call_contents, call_config):
        nonlocal model_name
        last_exc = None
        ordered = [model_name] + [m for m in candidate_models if m != model_name]
        for cand in ordered:
            try:
                resp = client.models.generate_content(
                    model=cand,
                    contents=call_contents,
                    config=call_config,
                )
                model_name = cand
                _RESOLVED_MODEL_CACHE[cache_key] = cand
                return resp
            except Exception as exc:
                last_exc = exc
                if _is_retryable_model_error(exc) and cand != ordered[-1]:
                    logger.warning("Model %s unavailable (%s); trying fallback Flash model.", cand, type(exc).__name__)
                    continue
                raise
        raise last_exc  # pragma: no cover

    tool_config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        tools=[types.Tool(function_declarations=_build_tool_declarations())],
        temperature=0.2,
    )

    # Build bounded conversation context (prefer persisted SQLite history when conversation_id is supplied)
    contents: list[types.Content] = []
    if req.conversation_id is not None:
        # Validate existence and business ownership before calling Gemini
        ai_conversation_service.get_conversation_entity(
            db, req.conversation_id, business_id=business_id
        )
        persisted_history = ai_conversation_service.get_recent_messages_for_context(
            db, req.conversation_id, limit=MAX_HISTORY_MESSAGES
        )
        for msg in persisted_history:
            role = "model" if msg["role"] == "assistant" else "user"
            contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])]))
    else:
        for msg in req.history[-MAX_HISTORY_MESSAGES:]:
            role = "model" if msg.role == "assistant" else "user"
            contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg.content)]))
    contents.append(types.Content(role="user", parts=[types.Part.from_text(text=req.message)]))

    tools_used: list[str] = []
    tool_outputs: list[tuple[str, dict[str, Any]]] = []
    final_text = ""

    try:
        for _round in range(MAX_TOOL_ROUNDS):
            response = _call_model(contents, tool_config)

            function_calls = getattr(response, "function_calls", None) or []
            if not function_calls:
                final_text = (getattr(response, "text", None) or "").strip()
                break

            # Append model's tool-request turn
            candidates = getattr(response, "candidates", None) or []
            if candidates and getattr(candidates[0], "content", None):
                contents.append(candidates[0].content)
            else:
                call_parts = [
                    types.Part.from_function_call(name=fc.name, args=dict(fc.args or {}))
                    for fc in function_calls
                ]
                contents.append(types.Content(role="model", parts=call_parts))

            # Execute requested read-only backend tools and return results
            response_parts = []
            for fc in function_calls:
                fn_name = fc.name
                fn_args = dict(fc.args or {})
                result = _execute_tool(
                    db, today=today, name=fn_name, args=fn_args, business_id=business_id
                )
                if fn_name not in tools_used:
                    tools_used.append(fn_name)
                tool_outputs.append((fn_name, result))
                response_parts.append(
                    types.Part.from_function_response(
                        name=fn_name,
                        response={"result": result},
                    )
                )

            contents.append(types.Content(role="user", parts=response_parts))
        else:
            # Final synthesis call if loop hit max rounds
            response = _call_model(
                contents,
                types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0.2,
                ),
            )
            final_text = (getattr(response, "text", None) or "").strip()

    except AppError:
        raise
    except Exception as exc:
        # Never log or expose the API key
        logger.warning("Gemini API request failed: %s", type(exc).__name__)
        raise AppError(
            502,
            "The Gemini AI service failed to respond. Please check your GEMINI_API_KEY, model quota, or network connection and try again.",
        ) from exc

    if not final_text:
        final_text = "I retrieved your business data, but could not generate a summary right now. Please try rephrasing your question."

    evidence, suggested_actions = _extract_evidence_and_actions(tool_outputs)

    conv, saved_msg = ai_conversation_service.append_exchange(
        db=db,
        conversation_id=req.conversation_id,
        user_text=req.message,
        assistant_reply=final_text,
        model=model_name,
        as_of_date=today.isoformat(),
        tools_used=tools_used,
        evidence=evidence,
        suggested_actions=suggested_actions,
        business_id=business_id,
    )

    return {
        "reply": final_text,
        "model": model_name,
        "as_of_date": today.isoformat(),
        "tools_used": tools_used,
        "evidence": evidence,
        "suggested_actions": suggested_actions,
        "conversation_id": conv.id,
        "conversation_title": conv.title,
        "message_id": saved_msg.id,
        "created_at": saved_msg.created_at,
    }
