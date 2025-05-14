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


subscription = APIRouter(prefix="/subscription", tags=["Subscription"])


# @bill_plan.get("/{organisation_id}/billing-plans", response_model=GetsubscriptionListResponse)
# async def retrieve_all_subscriptions(
#     organisation_id: str, db: Session = Depends(get_db)
# ):
#     """
#     Endpoint to get all billing plans
#     """

#     plans = subscription_service.fetch_all(db=db, organisation_id=organisation_id)

#     return success_response(
#         status_code=status.HTTP_200_OK,
#         message="Plans fetched successfully",
#         data={
#             "plans": jsonable_encoder(plans),
#         },
#     )

FLW_SECRET_KEY = config("FLW_SECRET_KEY")
@subscription.get("/verify-payment/{transaction_id}")
async def verify_payment(transaction_id: int):
    url = f"https://api.flutterwave.com/v3/transactions/{transaction_id}/verify"
    headers = {
        "Authorization": f"Bearer {FLW_SECRET_KEY}"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to reach Flutterwave")

    result = response.json()

    if result["status"] == "success" and result["data"]["status"] == "successful":
        return {
            "status": "success",
            "message": "Payment verified successfully",
            "data": result["data"]
        }
    else:
        raise HTTPException(status_code=400, detail="Payment not successful")

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

