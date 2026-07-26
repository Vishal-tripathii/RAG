from datetime import datetime

from sqlmodel import Field, SQLModel


class Document(SQLModel, table=True):
    doc_id: str = Field(primary_key=True)
    filename: str
    content_type: str
    size_bytes: int
    saved_path: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
