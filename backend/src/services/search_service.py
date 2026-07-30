import logging

from src.config import settings
from src.services.embedding_service import embed_query
from src.vector_store import search

logger = logging.getLogger(__name__)

def search_chunks(query: str, top_k: int | None = None) -> list[dict]:
    # None means the caller didn't specify, so fall back to the configured
    # default. Resolved here rather than as a function default so a change to
    # .env takes effect without the value being frozen at import time.
    limit = top_k if top_k is not None else settings.search_top_k

    vector = embed_query(query)
    hits = search(vector, limit=limit, score_threshold=settings.search_score_threshold)

    # Logged with the threshold because "0 results" is ambiguous otherwise -
    # nothing stored, or everything filtered out by too high a cutoff.
    logger.info(
        "Query %r matched %d chunks (threshold=%s)",
        query, len(hits), settings.search_score_threshold,
    )

    return [
        {
            # Cosine similarity, so higher is closer. Qdrant always returns its
            # best matches - a low score here means nothing relevant was stored,
            # not that the search failed.
            "score": hit.score,
            "text": hit.payload["text"],
            "document_id": hit.payload["document_id"],
            "page": hit.payload["page"],
            "chunk_index": hit.payload["chunk_index"],
        }
        for hit in hits
    ]
