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
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "address": self.address,
            "phone": self.phone,
            "referralLink": self.referralLink,
            "createdAt": self.createdAt,
            "updatedAt": self.updatedAt,
            "role": self.role.value if self.role else None,
            "profilePictureBase64": self.profilePictureBase64,
            "plan": self.plan,
            "emailVerified": self.emailVerified
        }


    def __str__(self):
        return f"Organization(id={self.id}, email={self.email}, plan={self.plan})"

