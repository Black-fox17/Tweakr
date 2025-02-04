from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Response,
    BackgroundTasks,
    Query,
)
from fastapi.responses import JSONResponse
from datetime import timedelta, datetime
from sqlalchemy.orm import Session
from typing import List

# from aioredis import Redis
from redis.asyncio import Redis


from app.auth.models import User, UserType, UserProfile
from app.auth.schemas import UserProfileCreate, UserProfileUpdate
from app.auth.services import UserProfileService
from app.core.constants import EXPIRATION
from app.core.utils import generate_otp_code
from app.core.database import get_session
from app.core.redis import get_redis_connection
from app.auth.helpers import get_current_active_user, create_jwt_token
from app.core.mail import EmailService

router = APIRouter()


@router.post("/send-code")
async def register_user_send_code(
    email: str,
    db=Depends(get_session),
    background_tasks: BackgroundTasks = None,
    redis: Redis = Depends(get_redis_connection),
):
    try:
        # Check if email is already registered or create a new user
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(email=email)
            db.add(user)
            db.commit()

        # Generate OTP
        code = generate_otp_code()

        # Save OTP to Redis
        await redis.setex(f"otp:{email}", EXPIRATION, code)

        # Send OTP via email
        email_service = EmailService(otp_expiration=EXPIRATION)
        background_tasks.add_task(email_service.send_otp_email, email, code)

        return {"message": "OTP sent successfully"}
    except Exception as e:
        print("Error:", e)
        raise HTTPException(
            status_code=500,
            detail="Failed to register user or send OTP. Please try again.",
        )


@router.post("/verify-code")
async def verify_code(
    email: str, code: int, redis: Redis = Depends(get_redis_connection)
):
    try:
        # Retrieve OTP from Redis
        stored_code = await redis.get(f"otp:{email}")
        if not stored_code or int(stored_code) != code:
            raise HTTPException(status_code=400, detail="Invalid or expired OTP")

        # OTP is valid, delete it from Redis
        await redis.delete(f"otp:{email}")

        # Generate a JWT token
        jwt_token = create_jwt_token(email)

        # return {"message": "OTP verified successfully", "token": jwt_token}
        response = JSONResponse(
            content={"message": "OTP verified successfully", "token": jwt_token}
        )
        response.set_cookie(key="access_token", value=jwt_token, httponly=True)
        return response
    except Exception as e:
        print("Error:", e)
        raise HTTPException(
            status_code=500, detail="Failed to verify OTP. Please try again."
        )


@router.post("/resend-code")
async def resend_code(
    email: str,
    db=Depends(get_session),
    redis: Redis = Depends(get_redis_connection),
    background_tasks: BackgroundTasks = None,
):
    try:
        # Check if email is registered
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="Email not found")

        # Generate a new OTP
        code = generate_otp_code()

        # Save new OTP to Redis
        await redis.setex(f"otp:{email}", EXPIRATION, code)

        # Send OTP via email
        email_service = EmailService(otp_expiration=EXPIRATION)
        background_tasks.add_task(email_service.send_otp_email, email, code)
        return {"message": "New OTP sent successfully"}
    except Exception as e:
        print("Error:", e)
        raise HTTPException(
            status_code=500, detail="Failed to resend OTP. Please try again."
        )


@router.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return {"email": current_user.email, "created_at": current_user.created_at}


"""User Profile endpoints"""


@router.post("/users/{user_id}/profile")
def create_user_profile(
    user_id: str, profile_data: UserProfileCreate, db: Session = Depends(get_session)
):
    return UserProfileService.create_user_profile(user_id, profile_data, db)


@router.get("/users/{user_id}/profile")
def get_user_profile(user_id: str, db: Session = Depends(get_session)):
    return UserProfileService.get_user_profile(user_id, db)


@router.put("/users/{user_id}/profile")
def update_user_profile(
    user_id: str, profile_data: UserProfileUpdate, db: Session = Depends(get_session)
):
    return UserProfileService.update_user_profile(user_id, profile_data, db)


@router.delete("/users/{user_id}/profile")
def delete_user_profile(user_id: str, db: Session = Depends(get_session)):
    return UserProfileService.delete_user_profile(user_id, db)


# @router.get("/users", response_model=List[User])
# def get_users(
#     db: Session = Depends(get_session),
#     skip: int = Query(0, ge=0),
#     limit: int = Query(100, ge=1),
#     user_type: Optional[str] = None,
#     current_user: User = Depends(get_current_active_user),
# ):
#     """Get list of users with optional filtering"""
#     if not current_user.user_type == UserType.ADMIN:
#         raise HTTPException(status_code=403, detail="Not enough permissions")
#     users = user_service.get_users(db, skip=skip, limit=limit, user_type=user_type)
#     return users


# @router.get("/users/{user_id}", response_model=User)
# def get_user(
#     user_id: str,
#     db: Session = Depends(get_session),
#     current_user: User = Depends(get_current_active_user),
# ):
#     """Get user by ID"""
#     user = user_service.get_user(db, user_id=user_id)
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#     if not current_user.user_type == UserType.ADMIN and current_user.id != user_id:
#         raise HTTPException(status_code=403, detail="Not enough permissions")
#     return user

# @router.put("/users/{user_id}", response_model=User)
# def update_user(
#     *,
#     db: Session = Depends(get_session),
#     user_id: str,
#     user_in: UserUpdate,
#     current_user: User = Depends(get_current_active_user),
# ):
#     """Update user"""
#     user = user_service.get_user(db, user_id=user_id)
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#     if not current_user.user_type == UserType.ADMIN and current_user.id != user_id:
#         raise HTTPException(status_code=403, detail="Not enough permissions")
#     user = user_service.update_user(db, db_obj=user, obj_in=user_in)
#     return user

# @router.delete("/users/{user_id}")
# def delete_user(
#     *,
#     db: Session = Depends(get_session),
#     user_id: str,
#     current_user: User = Depends(get_current_active_user),
# ):
#     """Delete user"""
#     if not current_user.user_type == UserType.ADMIN:
#         raise HTTPException(status_code=403, detail="Not enough permissions")
#     user = user_service.get_user(db, user_id=user_id)
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#     user = user_service.delete_user(db, user_id=user_id)
#     return {"message": "User deleted successfully"}
