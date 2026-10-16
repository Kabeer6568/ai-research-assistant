from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from app.schemas.answer import Source


class ChatRequest(BaseModel):
    question: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=5000)]
    conversation_id: int | None = None


class ConversationCreate(BaseModel):
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]


class ConversationRead(BaseModel):
    id: int
    title: str


class MessageRead(BaseModel):
    id: int
    role: str
    content: str
    sources: list[Source] = Field(default_factory=list)
