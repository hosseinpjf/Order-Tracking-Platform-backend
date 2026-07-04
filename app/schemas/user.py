from pydantic import BaseModel
from app.models.user import UserRole

class RegisterUser(BaseModel):
    name: str
    phone: str
    password: str

class LoginUser(BaseModel):
    phone: str
    password: str

class ChangeRole(BaseModel):
    user_id: str
    role: UserRole

class RefreshToken(BaseModel):
    refresh_token: str