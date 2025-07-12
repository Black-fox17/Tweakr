from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from api.v1.models.subscriptions_plan import SubscriptionPlans
from api.v1.models.subscriptions import Subscription
from typing import Any, Optional
from api.core.base.services import Service
from api.v1.schemas.subscription import CreateSubscriptionSchema
from api.utils.db_validators import check_model_existence
from api.db.database import get_db
from fastapi import Depends, HTTPException, status
from typing import Annotated
from datetime import datetime, timedelta


class SubscriptionService(Service):
    """Product service functionality"""

    def create(self, db: Session, user_id: str, request: CreateSubscriptionSchema):
        """
        Create and return a new billing plan, ensuring a plan name can only exist 
        once for each 'monthly' and 'yearly' duration, and cannot be created 
        if it already exists for both durations.
        """
        if request.duration == "monthly":
            price_monthly = request.price
            price_yearly = request.price * 12 
            duration = 30
        else:
            price_monthly = request.price / 12
            price_yearly = request.price
            duration = 365

        # Check if the plan already exists for both durations
        existing_plan = db.query(SubscriptionPlans).filter(
            SubscriptionPlans.name == request.name,
        ).first()


        if not existing_plan:
            plan = SubscriptionPlans(
                name=request.name,
                price_monthly=price_monthly,
                price_yearly=price_yearly,
                features=request.features,
            )
            db.add(plan)
            db.commit()
            db.refresh(plan)

            user_subscription = Subscription(
                user_id=user_id,
                plan_id=plan.id,
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=duration),
            )
            db.add(user_subscription)
            db.commit()
            db.refresh(user_subscription)
            return plan
        else:
            user_subscription = Subscription(
                user_id=user_id,
                plan_id=existing_plan.id,
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=duration),
            )
            db.add(user_subscription)
            db.commit()
            db.refresh(user_subscription)
            return existing_plan

    def delete(self, db: Session, id: str):
        """
        delete a subscription plan by id
        """
        plan = db.query(SubscriptionPlans).filter(SubscriptionPlans.id == id).first()
        
        if not plan:
            raise HTTPException(
                status_code=404, detail="Subscription plan not found."
            )

        db.delete(plan)
        db.commit()

    def fetch(self, db: Session, subscription_id: str):
        subscription = db.query(SubscriptionPlans).filter(
            SubscriptionPlans.id == subscription_id
        ).first()

        if subscription is None:
            raise HTTPException(
                status_code=404, detail="Subscription plan not found."
            )

        return subscription
    def fetch_user_subscription(self, db: Session, user_id: str):
        user_subscription = db.query(Subscription).filter(
            Subscription.user_id == user_id
        ).all()

        return user_subscription

    def update(self, db: Session, id: str, schema):
        """
        fetch and update a subscription plan
        """
        plan = db.query(SubscriptionPlans).filter(SubscriptionPlans.id == id).first()
        
        if not plan:
            raise HTTPException(
                status_code=404, detail="Subscription plan not found."
            )

        if schema.duration == "monthly":
            price_monthly = schema.price_monthly 
            price_yearly = schema.price_monthly * 12
        else:
            price_monthly = schema.price_yearly / 12
            price_yearly = schema.price_yearly

        plan.name = schema.name
        plan.price_monthly = price_monthly
        plan.price_yearly = price_yearly
        plan.features = schema.features

        db.commit()
        db.refresh(plan)

        return plan

    def fetch_all(self, db: Session, **query_params: Optional[Any]):
        """Fetch all subscription plans with option to search using query parameters"""

        query = db.query(SubscriptionPlans)

        # Enable filter by query parameter
        if query_params:
            for column, value in query_params.items():
                if hasattr(SubscriptionPlans, column) and value:
                    query = query.filter(
                        getattr(SubscriptionPlans, column).ilike(f"%{value}%")
                    )

        return query.all()
    def cleanup_expired_subs(self, db: Annotated[Session, Depends(get_db)]):
        expired_subs = db.query(Subscription).filter(
            Subscription.end_date <= datetime.utcnow()
        ).all()
        
        for doc in expired_subs:
            db.delete(doc)
        db.commit()
        return len(expired_subs)


subscription_service = SubscriptionService()
