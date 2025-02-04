# app/schemas/user.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.core.enums.user_type import UserType


class UserBase(BaseModel):
    email: str
    user_type: Optional[UserType] = UserType.USER


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    email: Optional[str] = None
    is_active: Optional[bool] = None
    user_type: Optional[UserType] = None


class UserInDBBase(UserBase):
    id: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class User(UserInDBBase):
    pass


class UserInDB(UserInDBBase):
    pass


class UserProfileBase(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    phone_number: Optional[str]
    address: Optional[str]


class UserProfileCreate(UserProfileBase):
    pass


class UserProfileUpdate(UserProfileBase):
    pass


class UserProfile(UserProfileBase):
    id: str
    user_id: str
    created_at: datetime
