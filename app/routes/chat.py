from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.conversation import Conversation
from app.models.user import User
from app.schemas.answer import Answer
from app.schemas.chat import ChatRequest
from app.services.rag_service import generate_answer

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=Answer)
async def chat(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
) -> Answer:
    conversation = None
    if payload.conversation_id is not None:
        conversation = database.scalar(
            select(Conversation).where(
                Conversation.id == payload.conversation_id,
                Conversation.owner_id == current_user.id,
            )
        )
        if conversation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    else:
        conversation = Conversation(owner_id=current_user.id, title=payload.question[:200])
        database.add(conversation)
        database.flush()

    try:
        return await generate_answer(database, current_user.id, conversation.id, payload.question)
    except NotImplementedError as error:
        database.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Answer generation is not configured yet. Add an embedding and language-model provider.",
        ) from error
