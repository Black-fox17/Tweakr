from pydantic import BaseModel, EmailStr, Field

class DocumentCreate(BaseModel):
    user_id: str
    data: str
    