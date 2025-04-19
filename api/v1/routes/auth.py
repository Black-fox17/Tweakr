import logging
from datetime import timedelta
from fastapi.responses import JSONResponse
from jose import ExpiredSignatureError, JWTError
from slowapi import Limiter
from slowapi.util import get_remote_address

from fastapi import (
    BackgroundTasks,
    Depends,
    status,
    APIRouter,
    Response,
    Request,
    HTTPException,
)
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from typing import Annotated

from api.core.dependencies.email_sender import send_email
from api.utils.success_response import auth_response, success_response
from api.v1.models import User
from api.v1.schemas.user import Token, UserEmailSender
from api.v1.schemas.user import (
    LoginRequest,
    UserCreate,
)
# from api.v1.services.login_notification import send_login_notification
from api.db.database import get_db
from api.v1.services.user import user_service
from api.utils.settings import settings

auth = APIRouter(prefix="/auth", tags=["Authentication"])



  
@auth.post("/register", status_code=status.HTTP_201_CREATED, response_model=auth_response)
def register(
    request: Request,
    background_tasks: BackgroundTasks,
    response: Response,
    user_schema: UserCreate,
    db: Session = Depends(get_db),
):
    """Endpoint for a user to register their account"""

    base_url = str(request.base_url).strip("/")
    # Create user account
    user = user_service.create(db=db, schema=user_schema)


    verification_token = user_service.create_verification_token(user.id)

    access_token = user_service.create_access_token(user_id=user.id)
    refresh_token = user_service.create_refresh_token(user_id=user.id)

    # create an organization for the user
    # Create access and refresh tokens
    access_token = user_service.create_access_token(user_id=user.id)
    refresh_token = user_service.create_refresh_token(user_id=user.id)

    response = auth_response(
        status_code=201,
        message="User created successfully",
        access_token=access_token,
        data={
            "user": jsonable_encoder(
                user, exclude=["password", "is_deleted", "is_verified", "updated_at"]
            )
        },
    )

    # Add refresh token to cookies
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        expires=timedelta(days=60),
        httponly=True,
        secure=True,
        samesite="none",
    )
    return response




@auth.post("/login", status_code=status.HTTP_200_OK, response_model=auth_response)
def login(request: Request, login_request: LoginRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):

    """Endpoint to log in a user"""

    # Authenticate the user
    user = user_service.authenticate_user(
        db=db, email=login_request.email, password=login_request.password
    )
    # Generate access and refresh tokens
    access_token = user_service.create_access_token(user_id=user.id)
    refresh_token = user_service.create_refresh_token(user_id=user.id)

    response = auth_response(
        status_code=200,
        message="Login successful",
        access_token=access_token,
        data={
            "user": jsonable_encoder(
                user, exclude=["password", "is_deleted", "is_verified", "updated_at"]
            )
        },
    )

    # Add refresh token to cookies
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        expires=timedelta(days=30),
        httponly=True,
        secure=True,
        samesite="none",
    )

    return response


@auth.post("/logout", status_code=status.HTTP_200_OK)
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(user_service.get_current_user),
):
    """Endpoint to log a user out of their account"""

    response = success_response(status_code=200, message="User logged put successfully")

    # Delete refresh token from cookies
    response.delete_cookie(key="refresh_token")

    return response


