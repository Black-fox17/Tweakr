from fastapi import Depends, HTTPException
from api.core.base.services import Service
from api.v1.models.documents import DocumentModel
from api.v1.schemas.documents import DocumentCreate
from sqlalchemy.orm import Session
from typing import Annotated, Optional, Any, List, Dict
from api.db.database import get_db
import hashlib
from datetime import timedelta, datetime

class Document:
    def __init__(self) -> None:
        super().__init__()

    def create(self, db: Annotated[Session, Depends(get_db)], data: DocumentCreate):
        """Create a temporary data download option"""

        # Check if this exact receipt file has been used before
        existing_data = db.query(DocumentModel).filter(
            DocumentModel.user_id == data.user_id
        ).first()
        
        if existing_data:
            self.delete(db,existing_data.user_id)
        
        document_data = DocumentModel(**data.model_dump(), expires_at=datetime.utcnow() + timedelta(hours=24))

        db.add(document_data)
        db.commit()
        db.refresh(document_data)
        return document_data
        

    def delete(self, db:Annotated[Session, Depends(get_db)], user_id: str):
        data = db.query(DocumentModel).filter(DocumentModel.user_id == user_id).first()
        if data:
            db.delete(data)
            db.commit()

    def update(self, db: Annotated[Session, Depends(get_db)], user_id: str, document_url: str):
        document_data = db.query(DocumentModel).filter(DocumentModel.user_id == user_id).first()
        
        if not document_data:
            raise HTTPException(status_code=404, detail="Document not found")
        # Update the document URL
        document_data.download_url = document_url

        
        db.commit()
        db.refresh(document_data)
        return document_data
    def cleanup_expired(self, db: Annotated[Session, Depends(get_db)]):
        expired_docs = db.query(DocumentModel).filter(
            DocumentModel.expires_at <= datetime.utcnow()
        ).all()
        
        for doc in expired_docs:
            db.delete(doc)
        db.commit()
        return len(expired_docs)
        
document_service = Document()
