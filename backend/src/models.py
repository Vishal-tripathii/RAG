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
    # SHA-256 of the raw file bytes. Indexed + unique so "has this exact file
    # already been uploaded" is one B-tree lookup, not a table scan - and so
    # the database itself rejects a duplicate insert if two requests race.
    content_hash: str = Field(index=True, unique=True)
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)


class Chunk(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    document_id: str = Field(foreign_key="document.doc_id")
    page: int
    chunk_index: int
    text: str
    chunk_metadata: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
