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
            raise HTTPException(
                status_code=400,
                detail={ 
                    "error": "Please check your mail for a download link",
                }
            )
    
        db.add(data)
        db.commit()
        db.refresh(data)
        return data
    
    def delete(self, db:Annotated[Session, Depends(get_db)], user_id: str):
        data = db.query(DocumentModel).filter(DocumentModel.user_id == user_id).first()
        if data:
            db.delete(data)
            db.commit()

    def cleanup_expired(self, db: Annotated[Session, Depends(get_db)]):
        expired_docs = db.query(DocumentModel).filter(
            DocumentModel.expires_at <= datetime.utcnow()
        ).all()
        
        for doc in expired_docs:
            db.delete(doc)
        db.commit()
        return len(expired_docs)
        
document_service = Document()
