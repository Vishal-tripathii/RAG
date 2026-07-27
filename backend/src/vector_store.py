from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    FilterSelector,
    MatchValue,
    PointStruct,
    ScoredPoint,
    VectorParams,
)

from src.config import settings
from src.models import Chunk

COLLECTION_NAME = "chunks"
VECTOR_SIZE = 384  # must match embedding_service's model (BAAI/bge-small-en-v1.5) - changing models means recreating this collection

client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)


def init_collection() -> None:
    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )


def upsert_chunks(chunks: list[Chunk], embeddings: list[list[float]]) -> None:
    points = [
        PointStruct(
            id=chunk.id,
            vector=embedding,
            payload={
                "document_id": chunk.document_id,
                "page": chunk.page,
                "chunk_index": chunk.chunk_index,
                "text": chunk.text,
                "chunk_metadata": chunk.chunk_metadata,
            },
        )
        for chunk, embedding in zip(chunks, embeddings)
    ]
    client.upsert(collection_name=COLLECTION_NAME, points=points)


def search(vector: list[float], limit: int, score_threshold: float | None = None) -> list[ScoredPoint]:
    # query_points returns a wrapper object; the hits themselves are on .points
    response = client.query_points(
        collection_name=COLLECTION_NAME,
        query=vector,
        limit=limit,
        with_payload=True,  # the chunk text lives in the payload, not the vector
        # None means "no floor" - Qdrant then returns its best `limit` matches
        # however weak they are. Applied server-side, so weak hits cost nothing.
        score_threshold=score_threshold,
    )
    return response.points


def delete_all_points() -> None:
    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=FilterSelector(filter=Filter()),
    )


def delete_by_document_id(document_id: str) -> None:
    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=FilterSelector(
            filter=Filter(must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))])
        ),
    )
