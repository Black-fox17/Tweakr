from fastapi import APIRouter, status, BackgroundTasks, Depends, Request, HTTPException, Response
from api.core.responses import SUCCESS
from api.db.database import get_db
# from api.utils.send_mail import send_faq_inquiry_mail
from api.utils.success_response import success_response
from api.v1.models.user import User
from api.v1.schemas.documents import DocumentCreate
from api.v1.services.documents import document_service
from sqlalchemy.orm import Session
from typing import Annotated
import base64
from api.v1.models.documents import DocumentModel

document = APIRouter(prefix="/document", tags=["Document"])

@document.post(
    "",
    response_model=success_response,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "FAQ Inquiry created successfully"},
        422: {"description": "Validation Error"},
    },
)
async def create_document(
    data: DocumentCreate, db: Annotated[Session, Depends(get_db)], request: Request
):
    new_document = document_service.create(db, data)
    
    download_url = str(request.url_for("download_document", document_id=new_document.user_id))
    document_service.update(db, new_document.user_id, download_url)
    
    response = success_response(
        message=SUCCESS,
        data={"download_url": download_url},
        status_code=status.HTTP_201_CREATED,
    )
    return response

@document.get(
    "/download/{document_id}",
    responses={
        200: {"description": "File downloaded successfully"},
        404: {"description": "Document not found"},
    },
)
async def download_document(
    document_id: str, db: Annotated[Session, Depends(get_db)]
):
    document_data = db.query(DocumentModel).filter(DocumentModel.user_id == document_id).first()
   
    if not document_data:
        raise HTTPException(status_code=404, detail="Document not found")
   
    base64_data = document_data.data.split(',')[1] if ',' in document_data.data else document_data.data
    file_data = base64.b64decode(base64_data)
   
    # document_service.delete(db, document_data.user_id)
   
    return Response(
        content=file_data,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": "attachment; filename=document.docx"}
    )