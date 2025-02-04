# app/services/user_service.py
from sqlalchemy.orm import Session
from typing import List, Optional, Union, Dict, Any
from fastapi.encoders import jsonable_encoder
from fastapi import HTTPException


from app.auth.models import User, UserProfile
from app.auth.schemas import (
    UserCreate,
    UserUpdate,
    UserProfileCreate,
    UserProfileUpdate,
)
from app.core.enums.user_type import UserType


def get_user(db: Session, user_id: str) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def get_users(
    db: Session, skip: int = 0, limit: int = 100, user_type: Optional[str] = None
) -> List[User]:
    query = db.query(User)
    if user_type:
        query = query.filter(User.user_type == UserType[user_type])
    return query.offset(skip).limit(limit).all()


def create_user(db: Session, obj_in: UserCreate) -> User:
    obj_in_data = jsonable_encoder(obj_in)
    db_obj = User(**obj_in_data)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_user(
    db: Session, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]
) -> User:
    obj_data = jsonable_encoder(db_obj)
    if isinstance(obj_in, dict):
        update_data = obj_in
    else:
        update_data = obj_in.dict(exclude_unset=True)
    for field in obj_data:
        if field in update_data:
            setattr(db_obj, field, update_data[field])
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_user(db: Session, user_id: str) -> Optional[User]:
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
    return user


class UserProfileService:
    # TODO: add try and exceptions to catch possible errors in time.
    @staticmethod
    def create_user_profile(
        user_id: str, profile_data: UserProfileCreate, db: Session
    ) -> UserProfile:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        profile = UserProfile(user_id=user_id, **profile_data.dict())
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def get_user_profile(user_id: str, db: Session) -> UserProfile:
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        return profile

    @staticmethod
    def update_user_profile(
        user_id: str, profile_data: UserProfileUpdate, db: Session
    ) -> UserProfile:
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        for key, value in profile_data.dict(exclude_unset=True).items():
            setattr(profile, key, value)

        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def delete_user_profile(user_id: str, db: Session) -> dict:
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        db.delete(profile)
        db.commit()
        return {"message": "Profile deleted successfully"}
