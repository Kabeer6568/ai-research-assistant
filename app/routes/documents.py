from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_current_user
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentRead
from app.services.document_service import index_document, save_document
from app.utils.file_validation import validate_pdf_upload
from app.database import get_db

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
) -> Document:
    try:
        content = await validate_pdf_upload(file)
        document = save_document(database, owner_id=current_user.id, filename=file.filename or "document.pdf", content=content)
        document = await index_document(database, document)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    finally:
        await file.close()
    return document


@router.get("/", response_model=list[DocumentRead])
def list_documents(
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
) -> list[Document]:
    return list(
        database.scalars(
            select(Document).where(Document.owner_id == current_user.id).order_by(Document.created_at.desc())
        ).all()
    )


@router.post("/{document_id}/index", response_model=DocumentRead)
async def reindex_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
) -> Document:
    document = database.scalar(
        select(Document).where(
            Document.id == document_id,
            Document.owner_id == current_user.id,
        )
    )
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    return await index_document(database, document)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
) -> None:
    document = database.scalar(
        select(Document).where(
            Document.id == document_id,
            Document.owner_id == current_user.id,
        )
    )
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    stored_path = Path(document.stored_path)
    database.delete(document)
    database.commit()
    stored_path.unlink(missing_ok=True)
