from fastapi import APIRouter, File, HTTPException, UploadFile

from src.services.upload_service import delete_all_documents, delete_document, handle_upload

router = APIRouter()


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    return await handle_upload(file)


# Plain `def`, not `async def`: both of these do blocking Postgres and Qdrant
# I/O, and FastAPI runs sync handlers in a threadpool rather than on the event
# loop. As async handlers they blocked it for the length of the delete.
@router.delete("/documents")
def delete_documents():
    count = delete_all_documents()
    return {"deleted": count}


@router.delete("/documents/{doc_id}")
def delete_document_endpoint(doc_id: str):
    if not delete_document(doc_id):
        raise HTTPException(status_code=404, detail="Document not found")
    return {"deleted": doc_id}
