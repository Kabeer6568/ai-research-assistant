from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.prompts import SYSTEM_PROMPT
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.answer import Answer, Source
from app.services.llm_service import generate_completion
from app.services.retrieval_service import retrieve_context


async def generate_answer(
    database: Session,
    user_id: int,
    conversation_id: int,
    question: str,
) -> Answer:
    context = await retrieve_context(database, question, owner_id=user_id)
    history = list(
        database.scalars(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.id.desc())
            .limit(20)
        ).all()
    )
    history.reverse()
    source_text = "\n\n".join(
        f"[S{index}] {item['filename']}: {item['text']}"
        for index, item in enumerate(context, start=1)
    )
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend({"role": message.role, "content": message.content} for message in history)
    messages.append(
        {
            "role": "user",
            "content": (
                "Answer using only the research excerpts below. If they do not support an answer, "
                "say so. Cite supporting excerpts with their [S#] labels; do not invent citations.\n\n"
                f"Research excerpts:\n{source_text or 'No indexed excerpts were found.'}\n\n"
                f"Question: {question}"
            ),
        }
    )
    answer_text = await generate_completion(messages)
    sources = [
        Source(
            citation=f"S{index}",
            document_id=int(item["document_id"]),
            id=int(item["id"]),
            filename=str(item["filename"]),
            excerpt=str(item["text"]),
        )
        for index, item in enumerate(context, start=1)
    ]
    database.add_all(
        [
            Message(conversation_id=conversation_id, role="user", content=question),
            Message(
                conversation_id=conversation_id,
                role="assistant",
                content=answer_text,
                sources=[source.model_dump() for source in sources],
            ),
        ]
    )
    database.commit()
    return Answer(conversation_id=conversation_id, answer=answer_text, sources=sources)
