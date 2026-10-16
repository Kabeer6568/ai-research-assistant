import math
from collections.abc import Sequence

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.document_chunk import DocumentChunk
from app.models.document import Document


def upsert_chunks(
    database: Session,
    owner_id: int,
    document_id: int,
    chunks: Sequence[str],
    embeddings: Sequence[Sequence[float]],
) -> None:
    if len(chunks) != len(embeddings):
        raise ValueError("Every text chunk must have a corresponding embedding.")
    database.execute(
        delete(DocumentChunk).where(
            DocumentChunk.owner_id == owner_id,
            DocumentChunk.document_id == document_id,
        )
    )
    database.add_all(
        DocumentChunk(
            owner_id=owner_id,
            document_id=document_id,
            chunk_index=index,
            content=content,
            embedding=[float(value) for value in embeddings[index]],
        )
        for index, content in enumerate(chunks)
    )
    database.commit()


def search_chunks(
    database: Session,
    query_embedding: Sequence[float],
    owner_id: int,
    limit: int = 5,
) -> list[dict[str, object]]:
    rows = database.execute(
        select(DocumentChunk, Document.filename)
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(
            DocumentChunk.owner_id == owner_id,
            Document.owner_id == owner_id,
        )
    ).all()
    query_norm = math.sqrt(sum(value * value for value in query_embedding))
    if query_norm == 0:
        return []
    ranked: list[tuple[float, DocumentChunk, str]] = []
    for chunk, filename in rows:
        if len(chunk.embedding) != len(query_embedding):
            continue
        chunk_norm = math.sqrt(sum(value * value for value in chunk.embedding))
        if chunk_norm == 0:
            continue
        score = sum(a * b for a, b in zip(query_embedding, chunk.embedding)) / (
            query_norm * chunk_norm
        )
        ranked.append((score, chunk, filename))
    ranked.sort(key=lambda item: item[0], reverse=True)
    return [
        {
            "id": chunk.id,
            "document_id": chunk.document_id,
            "filename": filename,
            "text": chunk.content,
            "score": score,
        }
        for score, chunk, filename in ranked[:limit]
    ]
