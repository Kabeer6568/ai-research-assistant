from pydantic import BaseModel


class Source(BaseModel):
    document_id: int
    filename: str
    excerpt: str


class Answer(BaseModel):
    conversation_id: int
    answer: str
    sources: list[Source]
