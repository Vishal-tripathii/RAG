import logging
import uuid
from pathlib import Path

from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool
from sqlmodel import Session, func, select

from src.db import engine
from src.models import Chunk, Document
from src.services.chunking_service import chunk_pages
from src.services.embedding_service import embed_chunks
from src.services.pdf_service import extract_pages
from src.utils.filenames import sanitize_filename
from src.vector_store import delete_all_points, delete_by_document_id, upsert_chunks

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


async def handle_upload(file: UploadFile) -> dict:
    contents = await file.read()

    # Everything past this point is blocking and never awaits: pdfplumber
    # parsing, ONNX inference, psycopg2, and Qdrant's HTTP client. Run inline in
    # an async handler it all executes on the event loop, so a single upload
    # stalls every other request for the full duration of the ingest. Handing it
    # to the threadpool is what FastAPI already does for sync handlers - this
    # route only has to stay async because reading the body needs await.
    return await run_in_threadpool(_ingest, file.filename, file.content_type, contents)


def _ingest(filename: str | None, content_type: str | None, contents: bytes) -> dict:
    doc_id = str(uuid.uuid4())

    pages = extract_pages(contents)  # raises 400 if nothing extractable (e.g. scanned PDF)
    chunks = chunk_pages(pages, document_id=doc_id)

    logger.info("Extracted %d pages, %d chunks from %s", len(pages), len(chunks), filename)

    embeddings = embed_chunks(chunks)
    upsert_chunks(chunks, embeddings)
    logger.info("Upserted %d vectors into Qdrant", len(chunks))

    safe_filename = sanitize_filename(Path(filename).name)
    save_path = UPLOAD_DIR / f"{doc_id}_{safe_filename}"
    save_path.write_bytes(contents)

    document = Document(
        doc_id=doc_id,
        filename=filename,
        content_type=content_type,
        size_bytes=len(contents),
        saved_path=str(save_path),
    )
    with Session(engine) as session:
        session.add(document)
        session.flush()  # document must exist before chunks are inserted (chunk.document_id FK)
        session.add_all(chunks)
        session.commit()

    return {
        "doc_id": doc_id,
        "filename": filename,
        "content_type": content_type,
        "size_bytes": len(contents),
        "saved_path": str(save_path),
    }


def list_documents() -> list[dict]:
    with Session(engine) as session:
        documents = session.exec(select(Document)).all()
        # One grouped query rather than a per-document COUNT.
        counts = dict(
            session.exec(
                select(Chunk.document_id, func.count()).group_by(Chunk.document_id)
            ).all()
        )
        return [_document_summary(document, counts.get(document.doc_id, 0)) for document in documents]


def get_document(doc_id: str) -> dict | None:
    with Session(engine) as session:
        document = session.get(Document, doc_id)
        if document is None:
            return None
        chunk_count = session.exec(
            select(func.count()).where(Chunk.document_id == doc_id)
        ).one()
        return _document_summary(document, chunk_count)


def _document_summary(document: Document, chunk_count: int) -> dict:
    return {
        "doc_id": document.doc_id,
        "filename": document.filename,
        "content_type": document.content_type,
        "size_bytes": document.size_bytes,
        "uploaded_at": document.uploaded_at,
        "chunks": chunk_count,
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

    delete_all_points()
    return len(documents)


def delete_document(doc_id: str) -> bool:
    with Session(engine) as session:
        document = session.get(Document, doc_id)
        if document is None:
            return False

        chunks = session.exec(select(Chunk).where(Chunk.document_id == doc_id)).all()
        for chunk in chunks:
            session.delete(chunk)

        session.delete(document)
        session.commit()

    delete_by_document_id(doc_id)
    return True
