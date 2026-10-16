from app.services.embedding_service import embed_texts
from app.services.vector_store import search_chunks


def retrieve_context(question: str, owner_id: int, limit: int = 5) -> list[dict[str, object]]:
    embeddings = embed_texts([question])
    if not embeddings:
        return []
    return search_chunks(embeddings[0], owner_id=owner_id, limit=limit)
