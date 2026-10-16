from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.conversation import Conversation
from app.models.user import User
from app.models.message import Message
from app.schemas.chat import ConversationCreate, ConversationRead, MessageRead

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("/", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
def create_conversation(
    payload: ConversationCreate,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
) -> Conversation:
    conversation = Conversation(owner_id=current_user.id, title=payload.title.strip())
    database.add(conversation)
    database.commit()
    database.refresh(conversation)
    return conversation


@router.get("/", response_model=list[ConversationRead])
def list_conversations(
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
) -> list[Conversation]:
    return list(
        database.scalars(
            select(Conversation)
            .where(Conversation.owner_id == current_user.id)
            .order_by(Conversation.created_at.desc())
        ).all()
    )


@router.get("/{conversation_id}/messages", response_model=list[MessageRead])
def list_messages(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
) -> list[Message]:
    conversation = database.scalar(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.owner_id == current_user.id,
        )
    )
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    return list(
        database.scalars(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at, Message.id)
        ).all()
    )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
) -> None:
    conversation = database.scalar(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.owner_id == current_user.id,
        )
    )
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    database.delete(conversation)
    database.commit()
