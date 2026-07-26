import io

import pdfplumber
from fastapi import HTTPException


def extract_pages(contents: bytes) -> list[tuple[int, str]]:
    try:
        with pdfplumber.open(io.BytesIO(contents)) as pdf:
            pages = [(i + 1, (page.extract_text() or "")) for i, page in enumerate(pdf.pages)]
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Could not read this file as a PDF: {e}",
        )

    if not any(text.strip() for _, text in pages):
        raise HTTPException(
            status_code=400,
            detail="No extractable text found — is this a scanned PDF? (OCR not supported yet.)",
        )

    return pages
