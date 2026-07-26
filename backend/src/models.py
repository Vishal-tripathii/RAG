import uuid
from datetime import datetime

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class Document(SQLModel, table=True):
    doc_id: str = Field(primary_key=True)
    filename: str
    content_type: str
    size_bytes: int
    saved_path: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)


class Chunk(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    document_id: str = Field(foreign_key="document.doc_id")
    page: int
    chunk_index: int
    text: str
    chunk_metadata: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
