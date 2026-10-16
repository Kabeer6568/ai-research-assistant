from pathlib import Path
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.exceptions import AIProviderError
from app.models.document import Document
from app.services.embedding_service import embed_texts
from app.services.chunking_service import chunk_text
from app.services.pdf_service import extract_pdf_text
from app.services.vector_store import upsert_chunks
from app.utils.file_validation import safe_filename


def save_document(database: Session, owner_id: int, filename: str, content: bytes) -> Document:
    text = extract_pdf_text(content)
    upload_directory = Path("data/uploads")
    upload_directory.mkdir(parents=True, exist_ok=True)
    stored_path = upload_directory / f"{uuid4().hex}.pdf"
    stored_path.write_bytes(content)
    document = Document(
        owner_id=owner_id,
        filename=safe_filename(filename),
        stored_path=str(stored_path),
        extracted_text=text,
    )
    try:
        database.add(document)
        database.commit()
        database.refresh(document)
    except Exception:
        database.rollback()
        stored_path.unlink(missing_ok=True)
        raise
    return document


async def index_document(database: Session, document: Document) -> Document:
    document.index_status = "pending"
    document.index_error = None
    database.commit()
    try:
        chunks = chunk_text(document.extracted_text)
        if not chunks:
            raise ValueError("This PDF contains no selectable text to index.")
        embeddings = []
        for start in range(0, len(chunks), 64):
            embeddings.extend(
                await embed_texts(
                    chunks[start : start + 64],
                    task_type="RETRIEVAL_DOCUMENT",
                )
            )
        upsert_chunks(
            database,
            owner_id=document.owner_id,
            document_id=document.id,
            chunks=chunks,
            embeddings=embeddings,
        )
    except (AIProviderError, ValueError) as error:
        database.rollback()
        document.index_status = "failed"
        document.index_error = str(error)
        database.commit()
        return document
    document.index_status = "indexed"
    database.commit()
    database.refresh(document)
    return document
