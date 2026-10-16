from io import BytesIO

from pypdf import PdfReader


def extract_pdf_text(content: bytes) -> str:
    try:
        reader = PdfReader(BytesIO(content), strict=True)
        return "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    except Exception as error:
        raise ValueError("The uploaded file is not a readable PDF.") from error
