""" User data model
"""

from enum import Enum as PyEnum
from sqlalchemy import Column, String, text, DateTime, func, Boolean, Index, Enum as SAEnum
from sqlalchemy.orm import relationship
from api.v1.models.associations import Base


class RoleEnum(PyEnum):
    ADMIN = "ADMIN"
    USER = "USER"


class Organization(Base):
    __tablename__ = "organisation"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    address = Column(Boolean, server_default=text("false"))
    phone = Column(String, nullable= True, unique=True)
    referralLink = Column(String, nullable= True)
    password = Column(String, nullable=False)
    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    updatedAt = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    role = Column(
        SAEnum(RoleEnum, name="role_enum"),
        nullable=False,
        server_default=text("'USER'"),
    )
    profilePictureBase64 = Column(String, nullable=True)
    plan = Column(String, nullable= True)
    emailVerified = Column(Boolean, server_default=text("false"))


    def to_dict(self):
        obj_dict = super().to_dict()
        obj_dict.pop("password", None)
        return obj_dict

    def __str__(self):
        return self.email
