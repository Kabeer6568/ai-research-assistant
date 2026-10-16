from sqlalchemy.orm import Session

from app.services.embedding_service import embed_texts
from app.services.vector_store import search_chunks


async def retrieve_context(
    database: Session,
    question: str,
    owner_id: int,
    limit: int = 5,
) -> list[dict[str, object]]:
    embeddings = await embed_texts([question], task_type="RETRIEVAL_QUERY")
    if not embeddings:
        return []
    return search_chunks(database, embeddings[0], owner_id=owner_id, limit=limit)
