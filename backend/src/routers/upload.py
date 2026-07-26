from fastapi import APIRouter, UploadFile, File

from src.services.upload_service import handle_upload, delete_all_documents

router = APIRouter()


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    return await handle_upload(file)


@router.delete("/documents")
async def delete_documents():
    count = delete_all_documents()
    return {"deleted": count}
