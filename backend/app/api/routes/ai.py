from datetime import date
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_business
from app.database.session import get_db
from app.models.business import Business
from app.schemas.ai import (
    AiChatRequest,
    AiChatResponse,
    AiConversationCreate,
    AiConversationDetail,
    AiConversationRename,
    AiConversationSummary,
    AiStatusResponse,
)
from app.services import ai_conversation_service, ai_service

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/status", response_model=AiStatusResponse)
def get_status() -> dict:
    return ai_service.get_ai_status()


@router.post("/chat", response_model=AiChatResponse)
def chat(
    data: AiChatRequest,
    db: Session = Depends(get_db),
    business: Business = Depends(get_current_business),
) -> dict:
    return ai_service.chat_with_copilot(
        db, data, today=date.today(), business_id=business.id
    )


@router.get("/conversations", response_model=list[AiConversationSummary])
def list_conversations(
    search: str | None = Query(default=None, max_length=120),
    db: Session = Depends(get_db),
    business: Business = Depends(get_current_business),
) -> list[dict]:
    return ai_conversation_service.list_conversations(
        db, search=search, business_id=business.id
    )


@router.post("/conversations", response_model=AiConversationDetail, status_code=201)
def create_conversation(
    data: AiConversationCreate | None = None,
    db: Session = Depends(get_db),
    business: Business = Depends(get_current_business),
) -> dict:
    return ai_conversation_service.create_conversation(
        db, title=data.title if data else None, business_id=business.id
    )


@router.get("/conversations/{conversation_id}", response_model=AiConversationDetail)
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    business: Business = Depends(get_current_business),
) -> dict:
    return ai_conversation_service.get_conversation_detail(
        db, conversation_id, business_id=business.id
    )


@router.patch("/conversations/{conversation_id}", response_model=AiConversationDetail)
def rename_conversation(
    conversation_id: int,
    data: AiConversationRename,
    db: Session = Depends(get_db),
    business: Business = Depends(get_current_business),
) -> dict:
    return ai_conversation_service.rename_conversation(
        db, conversation_id, data.title, business_id=business.id
    )


@router.delete("/conversations/{conversation_id}", status_code=204, response_class=Response)
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    business: Business = Depends(get_current_business),
) -> Response:
    ai_conversation_service.delete_conversation(
        db, conversation_id, business_id=business.id
    )
    return Response(status_code=204)
