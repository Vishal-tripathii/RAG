import logging

from src.services.embedding_service import embed_text
from src.vector_store import COLLECTION_NAME, search

logger = logging.getLogger(__name__)


def search_chunks(query: str, top_k: int = 5) -> list[dict]:
    logger.info("Query: %s", query)

    query_vector = embed_text(query)
    logger.debug("Query embedding[:5]: %s", query_vector[:5])

    search_request = {"collection": COLLECTION_NAME, "vector[:5]": query_vector[:5], "top_k": top_k}
    logger.debug("Searching Qdrant: %s", search_request)

    points = search(query_vector, top_k=top_k)

    results = [
        {
            "score": point.score,
            "document_id": point.payload["document_id"],
            "page": point.payload["page"],
            "chunk_index": point.payload["chunk_index"],
            "text": point.payload["text"],
        }
        for point in points
    ]
    logger.info("Query results: %s", results)
    return results
