""" Associations
"""
from sqlalchemy import (
        Column,
        ForeignKey,
        String,
        Table,
        Enum
    )
from api.db.database import Base


user_organisation_association = Table(
    "user_organisation",
    Base.metadata,
    Column(
        "user_id", String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    ),
)
