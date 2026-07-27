from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.services.search_service import search_chunks

router = APIRouter()


class SearchRequest(BaseModel):
    # min_length=1 so a blank query is rejected as a 422 rather than being
    # embedded - an empty string produces a valid vector and silently returns
    # arbitrary chunks.
    query: str = Field(min_length=1)
    # None (omitted) defers to SEARCH_TOP_K in the environment; the upper bound
    # stops a single request asking for thousands of chunks.
    top_k: int | None = Field(default=None, ge=1, le=50)


@router.post("/search")
def search_documents(request: SearchRequest):
    results = search_chunks(request.query, top_k=request.top_k)
    return {"query": request.query, "results": results}
