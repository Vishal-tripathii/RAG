from fastapi import APIRouter
from pydantic import BaseModel

from src.services.query_service import search_chunks

router = APIRouter()


class QueryRequest(BaseModel):
    query: str
    top_k: int = 5


@router.post("/query")
async def query(request: QueryRequest):
    return {"results": search_chunks(request.query, top_k=request.top_k)}
