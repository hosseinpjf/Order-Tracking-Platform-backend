from pydantic import BaseModel, Field
from app.models.user import UserRole

class RegisterUser(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    phone: str = Field(..., pattern=r"^09\d{9}$")
    password: str = Field(..., min_length=8, max_length=128)

class LoginUser(BaseModel):
    phone: str = Field(..., pattern=r"^09\d{9}$")
    password: str = Field(..., min_length=8, max_length=128)

class ChangeRole(BaseModel):
    user_id: str
    role: UserRole

class RefreshToken(BaseModel):
    refresh_token: str = Field(..., pattern=r"^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$") 