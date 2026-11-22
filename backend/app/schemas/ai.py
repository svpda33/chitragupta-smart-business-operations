from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class ChatMessageIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class AiChatRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    message: str = Field(min_length=1, max_length=2000)
    history: list[ChatMessageIn] = Field(default_factory=list, max_length=20)
    conversation_id: int | None = None


class EvidenceItem(BaseModel):
    label: str
    value: str
    note: str | None = None
    kind: Literal["actual", "forecast", "simulation"] = "actual"


class SuggestedAction(BaseModel):
    label: str
    url: str


class AiChatResponse(BaseModel):
    reply: str
    model: str
    as_of_date: str
    tools_used: list[str] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    suggested_actions: list[SuggestedAction] = Field(default_factory=list)
    conversation_id: int | None = None
    conversation_title: str | None = None
    message_id: int | None = None
    created_at: datetime | None = None


class AiStatusResponse(BaseModel):
    configured: bool
    configured_model: str
    message: str


class AiConversationCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str | None = Field(default=None, max_length=160)


class AiConversationRename(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=160)


class AiMessageOut(BaseModel):
    id: int
    conversation_id: int
    role: Literal["user", "assistant"]
    content: str
    model: str | None = None
    as_of_date: str | None = None
    tools_used: list[str] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    suggested_actions: list[SuggestedAction] = Field(default_factory=list)
    created_at: datetime


class AiConversationSummary(BaseModel):
    id: int
    title: str
    message_count: int
    last_message_preview: str | None = None
    created_at: datetime
    updated_at: datetime


class AiConversationDetail(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list[AiMessageOut] = Field(default_factory=list)
