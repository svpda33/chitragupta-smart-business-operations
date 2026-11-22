from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ChecklistItem(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    text: str = Field(min_length=1, max_length=300)
    done: bool = False


class NoteIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(default="Untitled note", min_length=1, max_length=160)
    content: str = Field(default="", max_length=20000)
    category: str = Field(default="General", min_length=1, max_length=48)
    is_pinned: bool = False
    checklist: list[ChecklistItem] = Field(default_factory=list, max_length=100)


class NoteOut(BaseModel):
    id: int
    business_id: int
    title: str
    content: str
    category: str
    is_pinned: bool
    checklist: list[dict]
    created_at: datetime
    updated_at: datetime
