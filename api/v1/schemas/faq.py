from pydantic import BaseModel, EmailStr, Field

class CreateFAQ(BaseModel):
    """Validate the FAQ form data."""

    full_name: str = Field(..., example="John Doe")
    email: EmailStr = Field(..., example="johndoe@gmail.com")
    message: str = Field(..., example="I have a question about the product.")