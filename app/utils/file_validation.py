from pathlib import Path

from fastapi import UploadFile

from app.config import get_settings

PDF_SIGNATURE = b"%PDF-"


def safe_filename(filename: str) -> str:
    name = Path(filename.replace("\\", "/")).name.strip()
    return name[:255] or "document.pdf"


async def validate_pdf_upload(file: UploadFile) -> bytes:
    filename = safe_filename(file.filename or "")
    if Path(filename).suffix.lower() != ".pdf":
        raise ValueError("Only PDF files are supported.")
    max_size = get_settings().max_upload_size_mb * 1024 * 1024
    content = await file.read(max_size + 1)
    if len(content) > max_size:
        raise ValueError(f"File exceeds the {get_settings().max_upload_size_mb} MB upload limit.")
    if not content.startswith(PDF_SIGNATURE):
        raise ValueError("The uploaded file does not have a valid PDF signature.")
    return content
