from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.conversation import Conversation
from app.models.user import User
from app.schemas.chat import ConversationCreate, ConversationRead

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
