from fastapi import (
    APIRouter,
    Depends,
    status,
    HTTPException
)
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from api.utils.success_response import success_response
from api.v1.models.user import User
from api.v1.services.subscription import subscription_service
from api.db.database import get_db
from api.v1.services.user import user_service
from api.v1.schemas.subscription import CreateSubscriptionSchema, CreateSubscriptionResponse
import httpx
from decouple import config
import requests


subscription = APIRouter(prefix="/subscription", tags=["Subscription"])


FLW_SECRET_KEY = config("FLW_SECRET_KEY")

@subscription.get("/user_subscribed/{user_id}")
async def user_subscribed(user_id: str, db: Session = Depends(get_db)):
    user_subscribed = user_service.fetch_subscription(db,user_id)
    if user_subscribed:
        return success_response(
            status_code=status.HTTP_200_OK,
            message="User subscription fetched successfully",
            data=jsonable_encoder(user_subscribed)
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User subscription not found"
        )

@subscription.get("/verify-payment-sync/{transaction_id}")
async def verify_payment_sync(transaction_id: str):  # Changed from int to str
    """
    Synchronous endpoint to verify payment using requests library.
    """

    url = f"https://api.flutterwave.com/v3/transactions/{transaction_id}/verify"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {FLW_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    try:
        # Add timeout to prevent hanging
        response = requests.get(url, headers=headers, timeout=30)
        

        result = response.json()

        if result["status"] == "success" and result["data"]["status"] == "successful":
            return {
                "status": "success",
                "message": "Payment verified successfully",
                "data": result["data"]
            }
        else:
            return {
                "status": "failed",
                "message": "Payment verification failed",
                "data": result
            }
            
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=500, detail="Request to Flutterwave timed out")
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=500, detail="Could not connect to Flutterwave")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Request error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@subscription.post("/subscriptions", response_model=CreateSubscriptionResponse)
async def create_new_subscription(
    request: CreateSubscriptionSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(user_service.get_current_user)
):
    """
    Endpoint to create new billing plan
    """

    plan = subscription_service.create(db=db, user_id=current_user.id, request=request)

    return success_response(
        status_code=status.HTTP_200_OK,
        message="Plans created successfully",
        data=jsonable_encoder(plan),
    )


@subscription.patch("/subscriptions/{supscription_id}", response_model=CreateSubscriptionResponse)
async def update_a_subscription(
    subscription_id: str,
    request: CreateSubscriptionSchema,
    db: Session = Depends(get_db),
):
    """
    Endpoint to update a billing plan by ID
    """

    plan = subscription_service.update(db=db, id=subscription_id, schema=request)

    return success_response(
        status_code=status.HTTP_200_OK,
        message="Plan updated successfully",
        data=jsonable_encoder(plan),
    )


# @subscription.delete("/billing-plans/{subscription_id}", response_model=success_response)
# async def delete_a_subscription(
#     subscription_id: str,
#     db: Session = Depends(get_db),
# ):
#     """
#     Endpoint to delete a billing plan by ID
#     """

#     subscription_service.delete(db=db, id=subscription_id)

#     return success_response(
#         status_code=status.HTTP_200_OK,
#         message="Plan deleted successfully",
#     )


@subscription.get('/subscriptions/{subscription_id}', response_model=CreateSubscriptionResponse)
async def retrieve_single_subscriptions(
    subscription_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(user_service.get_current_user)
):
    """
    Endpoint to get single billing plan by id
    """

    subscription = subscription_service.fetch(db, subscription_id)

    return success_response(
        status_code=status.HTTP_200_OK,
        message="Plan fetched successfully",
        data=jsonable_encoder(subscription)
    )

@subscription.get('/subscriptions/user', response_model=CreateSubscriptionResponse)
async def retrieve_all_subscriptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(user_service.get_current_user)
):
    """
    Endpoint to get all billing plans
    """

    subscriptions = subscription_service.fetch_user_subscription(db, current_user.id)

    return success_response(
        status_code=status.HTTP_200_OK,
        message="Subscriptions fetched successfully",
        data=jsonable_encoder(subscriptions)
    )

