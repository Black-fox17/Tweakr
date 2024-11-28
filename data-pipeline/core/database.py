from sqlalchemy import create_engine, Column, Integer, String, Date, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, unique=True, nullable=False)
    content = Column(Text)
    category = Column(String, nullable=False)
    pub_date = Column(Date, nullable=False)
    keywords = Column(JSON, nullable=False)

# Initialize database tables
Base.metadata.create_all(bind=engine)
