from sqlalchemy import Column, String, text, Boolean, Index, JSON,DECIMAL
from sqlalchemy.orm import relationship
from api.v1.models.base_model import BaseTableModel

class SubscriptionPlans(BaseTableModel):
    __tablename__ = "subscription_plans"
    name = Column(String, nullable=False)
    price_monthly = Column(DECIMAL, nullable=False)
    price_yearly = Column(DECIMAL, nullable=False)
    features = Column(JSON, nullable=True)
    is_active = Column(Boolean, server_default=text("true"))
    
    # Relationships
    subscriptions = relationship("Subscription", back_populates="plan")
    