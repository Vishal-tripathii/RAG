import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlmodel import Session, select

from src.db import engine
from src.models import Document

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


async def handle_upload(file: UploadFile) -> dict:
    doc_id = str(uuid.uuid4())
    contents = await file.read()

    safe_filename = Path(file.filename).name  # strip any path components from the name
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
        documents = session.exec(select(Document)).all()
        for document in documents:
            session.delete(document)
        session.commit()
        return len(documents)
