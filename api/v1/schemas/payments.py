from pydantic import BaseModel, validator
from typing import List, Optional
from datetime import datetime
from api.v1.schemas.base_schema import ResponseBase


class CreatePaymentSchema(BaseModel):
    amount: float
    currency: str
    payment_method: str
