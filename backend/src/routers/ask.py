import json
import logging

from fastapi import APIRouter, HTTPException
from google.genai import errors as genai_errors
from pydantic import BaseModel, Field

from src.services.generation_service import build_prompt, call_llm
from src.services.search_service import search_chunks
from src.services.upload_service import get_filenames

logger = logging.getLogger(__name__)

router = APIRouter()


class AskRequest(BaseModel):
    # min_length=1 so a blank query is rejected as a 422 rather than being
    # embedded - an empty string produces a valid vector and silently returns
    # arbitrary chunks.
    query: str = Field(min_length=1)
    # None (omitted) defers to SEARCH_TOP_K in the environment; the upper bound
    # stops a single request asking for thousands of chunks.
    top_k: int | None = Field(default=None, ge=1, le=50)


@router.post("/ask")
def ask(request: AskRequest):
    results = search_chunks(request.query, top_k=request.top_k)
    logger.info("Retrieved for %r: %s", request.query, json.dumps(results))

    # Resolve each hit's document_id to a real filename in one query, and give
    # each hit the same 1-based number build_prompt below will label it [n]
    # with - so a citation like "[1]" in the answer can be traced straight
    # back to sources[0] without re-deriving the numbering elsewhere.
    filenames = get_filenames(list({r["document_id"] for r in results}))
    for i, r in enumerate(results, start=1):
        r["n"] = i
        r["filename"] = filenames.get(r["document_id"])

    prompt = build_prompt(request.query, results)
    logger.info("Built prompt: %s", json.dumps(prompt))

    try:
        answer = call_llm(prompt)
    except (ValueError, genai_errors.APIError) as e:
        logger.exception("LLM call failed")
        raise HTTPException(status_code=502, detail=f"LLM call failed: {e}")
    logger.info("LLM answer: %s", answer)

    # chunk_index and the raw prompt are internal bookkeeping - useful while
    # building this endpoint, not to a caller. Everything a client needs to
    # render "answer" plus clickable/citable sources is kept.
    sources = [
        {
            "n": r["n"],
            "filename": r["filename"],
            "document_id": r["document_id"],
            "page": r["page"],
            "score": r["score"],
            "text": r["text"],
        }
        for r in results
    ]
    return {"query": request.query, "answer": answer, "sources": sources}
