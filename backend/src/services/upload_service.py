import logging
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlmodel import Session, select

from src.db import engine
from src.models import Chunk, Document
from src.services.chunking_service import chunk_pages
from src.services.pdf_service import extract_pages
from src.utils.filenames import sanitize_filename

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


async def handle_upload(file: UploadFile) -> dict:
    doc_id = str(uuid.uuid4())
    contents = await file.read()

    pages = extract_pages(contents)  # raises 400 if nothing extractable (e.g. scanned PDF)
    chunks = chunk_pages(pages, document_id=doc_id)

    logger.info("Extracted %d pages, %d chunks from %s", len(pages), len(chunks), file.filename)
    for chunk in chunks:
        logger.debug("chunk %d: %s", chunk.chunk_index + 1, chunk.text)

    safe_filename = sanitize_filename(Path(file.filename).name)
    save_path = UPLOAD_DIR / f"{doc_id}_{safe_filename}"
    save_path.write_bytes(contents)

    document = Document(
        doc_id=doc_id,
        filename=file.filename,
        content_type=file.content_type,
        size_bytes=len(contents),
        saved_path=str(save_path),
    )
    with Session(engine) as session:
        session.add(document)
        session.add_all(chunks)
        session.commit()

    return {
        "doc_id": doc_id,
        "filename": file.filename,
        "content_type": file.content_type,
        "size_bytes": len(contents),
        "saved_path": str(save_path),
    }


def delete_all_documents() -> int:
    with Session(engine) as session:
        chunks = session.exec(select(Chunk)).all()
        for chunk in chunks:
            session.delete(chunk)

        documents = session.exec(select(Document)).all()
        for document in documents:
            session.delete(document)
        session.commit()
        return len(documents)
