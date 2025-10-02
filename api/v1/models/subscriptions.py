from sqlalchemy import Column, String, text, Boolean, Index, ForeignKey,DateTime,func
from sqlalchemy.orm import relationship
# from api.v1.models.associations import user_organisation_association
# from api.v1.models.permissions.user_org_role import user_organisation_roles
from api.v1.models.base_model import BaseTableModel

class Subscription(BaseTableModel):
    __tablename__ = "subscriptions"
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable = False)
    plan_id = Column(String, ForeignKey("subscription_plans.id", ondelete="CASCADE"), nullable = False)
    start_date = Column(DateTime(timezone=True), server_default=func.now())
    end_date = Column(DateTime(timezone=True), nullable=True)
    auto_renew = Column(Boolean, server_default=text("true"))
    trial_used = Column(Boolean, server_default=text("false"))
    
    # Relationships
    user = relationship("User", back_populates="subscriptions")
    plan = relationship("SubscriptionPlans", back_populates="subscriptions")
    