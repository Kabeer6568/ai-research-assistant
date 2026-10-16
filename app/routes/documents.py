from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_current_user
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentRead
from app.services.document_service import save_document
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
