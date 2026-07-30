# Imported from the submodule rather than the package root: the package's
# __init__ eagerly imports its sentence-transformers splitter, which drags in
# torch even though we don't use it.
from langchain_text_splitters.character import RecursiveCharacterTextSplitter

from src.models import Chunk
from src.utils.text_cleaning import clean_text

splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)


def chunk_pages(pages: list[tuple[int, str]], document_id: str) -> list[Chunk]:
    chunks = []
    chunk_index = 0

    for page_number, text in pages:
        cleaned = clean_text(text)
        if not cleaned:
            continue

        for piece in splitter.split_text(cleaned):
            chunks.append(Chunk(
                document_id=document_id,
                text=piece,
                page=page_number,
                chunk_index=chunk_index,
            ))
            chunk_index += 1

    return chunks
