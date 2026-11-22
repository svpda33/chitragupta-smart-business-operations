"""Persistence service for AI Finance Copilot conversations and messages."""

import json
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.ai_conversation import AiConversation, AiMessage
from app.utils.dates import now_utc

DEFAULT_TITLE = "New conversation"
MAX_AUTO_TITLE_LEN = 72


def _loads_list(raw: str | None) -> list:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return []


def _derive_title_from_message(text: str) -> str:
    cleaned = " ".join(text.strip().split())
    if not cleaned:
        return DEFAULT_TITLE
    if len(cleaned) <= MAX_AUTO_TITLE_LEN:
        return cleaned
    return cleaned[: MAX_AUTO_TITLE_LEN - 1].rstrip() + "…"


def serialize_message(msg: AiMessage) -> dict[str, Any]:
    return {
        "id": msg.id,
        "conversation_id": msg.conversation_id,
        "role": msg.role,
        "content": msg.content,
        "model": msg.model,
        "as_of_date": msg.as_of_date,
        "tools_used": _loads_list(msg.tools_used_json),
        "evidence": _loads_list(msg.evidence_json),
        "suggested_actions": _loads_list(msg.suggested_actions_json),
        "created_at": msg.created_at,
    }


def list_conversations(
    db: Session, search: str | None = None, business_id: int | None = None
) -> list[dict[str, Any]]:
    stmt = select(AiConversation).order_by(AiConversation.updated_at.desc(), AiConversation.id.desc())
    if business_id is not None:
        stmt = stmt.where(AiConversation.business_id == business_id)

    if search and search.strip():
        term = f"%{search.strip()}%"
        msg_match_ids = select(AiMessage.conversation_id).where(AiMessage.content.ilike(term))
        stmt = stmt.where(
            or_(
                AiConversation.title.ilike(term),
                AiConversation.id.in_(msg_match_ids),
            )
        )

    conversations = list(db.scalars(stmt.limit(100)).all())
    if not conversations:
        return []

    conv_ids = [c.id for c in conversations]
    counts_rows = db.execute(
        select(AiMessage.conversation_id, func.count(AiMessage.id))
        .where(AiMessage.conversation_id.in_(conv_ids))
        .group_by(AiMessage.conversation_id)
    ).all()
    counts_map = {cid: int(cnt) for cid, cnt in counts_rows}

    # Fetch last message preview per conversation
    last_msg_map: dict[int, str] = {}
    all_msgs = db.execute(
        select(AiMessage.conversation_id, AiMessage.content)
        .where(AiMessage.conversation_id.in_(conv_ids))
        .order_by(AiMessage.id.desc())
    ).all()
    for cid, content in all_msgs:
        if cid not in last_msg_map:
            snippet = " ".join(content.strip().split())
            last_msg_map[cid] = snippet[:110] + ("…" if len(snippet) > 110 else "")

    return [
        {
            "id": c.id,
            "title": c.title,
            "message_count": counts_map.get(c.id, 0),
            "last_message_preview": last_msg_map.get(c.id),
            "created_at": c.created_at,
            "updated_at": c.updated_at,
        }
        for c in conversations
    ]


def create_conversation(
    db: Session, title: str | None = None, business_id: int | None = None
) -> dict[str, Any]:
    clean_title = (title or "").strip() or DEFAULT_TITLE
    now = now_utc()
    conv = AiConversation(
        business_id=business_id, title=clean_title, created_at=now, updated_at=now
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return {
        "id": conv.id,
        "title": conv.title,
        "created_at": conv.created_at,
        "updated_at": conv.updated_at,
        "messages": [],
    }


def get_conversation_entity(
    db: Session, conversation_id: int, business_id: int | None = None
) -> AiConversation:
    conv = db.get(AiConversation, conversation_id)
    if conv is None or (business_id is not None and conv.business_id != business_id):
        raise AppError(404, "Conversation not found.")
    return conv


def get_conversation_detail(
    db: Session, conversation_id: int, business_id: int | None = None
) -> dict[str, Any]:
    conv = get_conversation_entity(db, conversation_id, business_id=business_id)
    msgs = list(
        db.scalars(
            select(AiMessage)
            .where(AiMessage.conversation_id == conv.id)
            .order_by(AiMessage.id.asc())
        ).all()
    )
    return {
        "id": conv.id,
        "title": conv.title,
        "created_at": conv.created_at,
        "updated_at": conv.updated_at,
        "messages": [serialize_message(m) for m in msgs],
    }


def rename_conversation(
    db: Session, conversation_id: int, title: str, business_id: int | None = None
) -> dict[str, Any]:
    conv = get_conversation_entity(db, conversation_id, business_id=business_id)
    clean_title = title.strip()
    if not clean_title:
        raise AppError(422, "Conversation title cannot be empty.", field="title")
    conv.title = clean_title[:160]
    conv.updated_at = now_utc()
    db.commit()
    db.refresh(conv)
    return get_conversation_detail(db, conv.id, business_id=business_id)


def delete_conversation(
    db: Session, conversation_id: int, business_id: int | None = None
) -> None:
    conv = get_conversation_entity(db, conversation_id, business_id=business_id)
    db.delete(conv)
    db.commit()


def get_recent_messages_for_context(
    db: Session, conversation_id: int, limit: int = 8
) -> list[dict[str, str]]:
    """Return the last N messages (bounded context) in chronological order for Gemini."""
    rows = list(
        db.scalars(
            select(AiMessage)
            .where(AiMessage.conversation_id == conversation_id)
            .order_by(AiMessage.id.desc())
            .limit(limit)
        ).all()
    )
    rows.reverse()
    return [{"role": m.role, "content": m.content} for m in rows]


def append_exchange(
    db: Session,
    conversation_id: int | None,
    user_text: str,
    assistant_reply: str,
    model: str,
    as_of_date: str,
    tools_used: list[str],
    evidence: list[dict[str, Any]],
    suggested_actions: list[dict[str, Any]],
    business_id: int | None = None,
) -> tuple[AiConversation, AiMessage]:
    """Persist the user prompt and assistant response atomically in SQLite."""
    now = now_utc()
    if conversation_id is not None:
        conv = get_conversation_entity(db, conversation_id, business_id=business_id)
        if conv.title == DEFAULT_TITLE:
            conv.title = _derive_title_from_message(user_text)
        conv.updated_at = now
    else:
        conv = AiConversation(
            business_id=business_id,
            title=_derive_title_from_message(user_text),
            created_at=now,
            updated_at=now,
        )
        db.add(conv)
        db.flush()

    user_msg = AiMessage(
        conversation_id=conv.id,
        role="user",
        content=user_text,
        created_at=now,
    )
    assistant_msg = AiMessage(
        conversation_id=conv.id,
        role="assistant",
        content=assistant_reply,
        model=model,
        as_of_date=as_of_date,
        tools_used_json=json.dumps(tools_used),
        evidence_json=json.dumps(evidence),
        suggested_actions_json=json.dumps(suggested_actions),
        created_at=now_utc(),
    )
    db.add(user_msg)
    db.add(assistant_msg)
    conv.updated_at = assistant_msg.created_at
    db.commit()
    db.refresh(conv)
    db.refresh(assistant_msg)
    return conv, assistant_msg
