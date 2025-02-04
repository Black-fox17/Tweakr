# core/enums/user_type.py

from enum import Enum


class UserType(str, Enum):
    USER = "User"
    ADMIN = "Admin"
    # DAO_MOD = "DAO Moderator"
    SUPERADMIN = "SuperAdmin"
    COMMUNITY_MOD = "Community Moderator"
    # AUTHOR = "Author"
    # REVIEWER = "Reviewer"
