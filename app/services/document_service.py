from pathlib import Path
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.document import Document
from app.services.pdf_service import extract_pdf_text
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
