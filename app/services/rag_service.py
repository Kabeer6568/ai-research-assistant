from sqlalchemy.orm import Session

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
    context = retrieve_context(question, owner_id=user_id)
    prompt = (
        "Answer using only the supplied research excerpts. If they do not support an answer, say so.\n\n"
        f"Research excerpts:\n{context}\n\nQuestion: {question}"
    )
    answer_text = await generate_completion(prompt)
    database.add_all(
        [
            Message(conversation_id=conversation_id, role="user", content=question),
            Message(conversation_id=conversation_id, role="assistant", content=answer_text),
        ]
    )
    database.commit()
    sources = [
        Source(
            document_id=int(item["document_id"]),
            filename=str(item["filename"]),
            excerpt=str(item["text"]),
        )
        for item in context
    ]
    return Answer(conversation_id=conversation_id, answer=answer_text, sources=sources)
