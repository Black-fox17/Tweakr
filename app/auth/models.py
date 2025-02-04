from sqlalchemy import Column, Integer, String, Enum, Boolean, DateTime, ForeignKey
from datetime import datetime
from sqlalchemy.orm import relationship
import uuid


from app.core.enums.user_type import UserType
from app.core.database import Base
from app.podcasts.models import GeneratedAudio


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    user_type = Column(
        Enum(UserType), default=UserType.USER, nullable=False, index=True
    )
    created_at = Column(DateTime, default=datetime.utcnow)

    contents = relationship("UserContent", back_populates="user")
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    scripts = relationship("Script", back_populates="user")
    research_topics = relationship("ResearchTopic", back_populates="user")
    generated_documents = relationship("GeneratedDocument", back_populates="user")
    generated_audio = relationship(
        GeneratedAudio, back_populates="user", lazy="dynamic"
    )
    episodes = relationship("Episode", back_populates="user", lazy="dynamic")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    address = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="profile")
