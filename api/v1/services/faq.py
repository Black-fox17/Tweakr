from fastapi import Depends
from api.core.base.services import Service
from api.v1.models.faq import FAQ
from api.v1.schemas.faq import CreateFAQ
from sqlalchemy.orm import Session
from typing import Annotated, Optional, Any
from api.db.database import get_db


class FAQService(Service):
    """FAQ Service."""

    def __init__(self) -> None:

        super().__init__()

    # ------------ CRUD functions ------------ #
    # CREATE
    def create(self, db: Annotated[Session, Depends(get_db)], data: CreateFAQ):
        """Create a new FAQ."""
        faq = FAQ(
            full_name=data.full_name,
            email=data.email,
            message=data.message,
        )
        db.add(faq)
        db.commit()
        db.refresh(faq)
        return faq

    # READ
    def fetch_all(self, db: Session, **query_params: Optional[Any]):
        """Fetch all submisions with option to search using query parameters"""

        query = db.query(FAQ)

        # Enable filter by query parameter
        if query_params:
            for column, value in query_params.items():
                if hasattr(FAQ, column) and value:
                    query = query.filter(getattr(FAQ, column).ilike(f"%{value}%"))

        return query.all()

    def fetch(self, db: Session, id: str):
        """Fetches a faq_inquiry by id"""

        faq = db.query(FAQ).get(id)
        return faq

    def fetch_by_email(self, db: Session, email: str):
        """Fetches a faq_inquiry by email"""

        faq = db.query(FAQ).filter(FAQ.email == email).first()
        return faq
    
    def delete(self, db: Session, id: str):
        """Delete a faq_inquiry by id"""

        faq = db.query(FAQ).get(id)
        db.delete(faq)
        db.commit()
        return faq
    
    def update(self, db: Session, id: str, data: CreateFAQ):
        faq = db.query(FAQ).get(id)
        faq.full_name = data.full_name
        faq.email = data.email
        faq.message = data.message
        db.commit()
        db.refresh(faq)
        return faq


faq_service = FAQService()