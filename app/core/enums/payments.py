from enum import Enum


class PaymentPlanType(Enum):
    BASIC = "basic"
    STANDARD = "standard"
    ENTERPRISE = "enterprise"
    PAY_AS_YOU_GO = "pay_as_you_go"


class PaymentStatus(Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
