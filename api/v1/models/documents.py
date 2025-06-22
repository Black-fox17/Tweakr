from sqlalchemy import Column, String, text, Boolean, Index, ForeignKey,DateTime,func
from sqlalchemy.orm import relationship
# from api.v1.models.associations import user_organisation_association
# from api.v1.models.permissions.user_org_role import user_organisation_roles
from api.v1.models.base_model import BaseTableModel
from datetime import datetime, timedelta

class DocumentModel(BaseTableModel):
    __tablename__ = "documents"
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable = False)
    data = Column(String, nullable = False)
    download_url = Column(String, nullable = False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(hours=24))

    
    user = relationship("User", back_populates="documents")