from sqlalchemy import Column, String, text, Boolean, Index, ForeignKey,DateTime,func, DECIMAL
from sqlalchemy.orm import relationship
from api.v1.models.base_model import BaseTableModel

class Payments(BaseTableModel):
    __tablename__ = "payments"

    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable = False)
    subscription_id = Column(String, ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable = False)
    amount = Column(DECIMAL, nullable=True)
    currency = Column(String, nullable = False)
    payment_date = Column(DateTime(timezone=True), server_default=func.now())
    payment_method = Column(String, nullable = True)
    status = Column(String, nullable = True)
    
    # Relationships
    user = relationship("User", back_populates="payments")
    subscription = relationship("Subscription", back_populates="payments")
 
