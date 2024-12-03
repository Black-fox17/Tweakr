from sqlalchemy import create_engine, Column, Integer, String, Date, JSON, Text, Boolean

from datapipeline.core.database import Base


class Papers(Base):
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, unique=True, nullable=False, index=True)
    category = Column(String, nullable=False, index=True)
    pub_date = Column(Date, nullable=False)
    keywords = Column(JSON, nullable=True, index=True)
    is_processed = Column(Boolean, index=True, default=False)
