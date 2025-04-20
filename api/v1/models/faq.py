from sqlalchemy import Column, String, Text
from api.v1.models.base_model import BaseTableModel


class FAQ(BaseTableModel):
    __tablename__ = "faq"

    email = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    message = Column(Text, nullable=False)
