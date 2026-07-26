from fastapi import APIRouter, File, HTTPException, UploadFile

from src.services.upload_service import delete_all_documents, delete_document, handle_upload

router = APIRouter()


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    return await handle_upload(file)


@router.delete("/documents")
async def delete_documents():
    count = delete_all_documents()
    return {"deleted": count}


@router.delete("/documents/{doc_id}")
async def delete_document_endpoint(doc_id: str):
    if not delete_document(doc_id):
        raise HTTPException(status_code=404, detail="Document not found")
    return {"deleted": doc_id}
