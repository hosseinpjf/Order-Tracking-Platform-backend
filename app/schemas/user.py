from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from app.models.user import UserRole

class RegisterUser(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    phone: str = Field(..., pattern=r"^09\d{9}$")
    password: str = Field(..., min_length=8, max_length=128)
    address: str = Field(..., min_length=5, max_length=500)

class LoginUser(BaseModel):
    phone: str = Field(..., pattern=r"^09\d{9}$")
    password: str = Field(..., min_length=8, max_length=128)

class ChangeRole(BaseModel):
    user_id: str
    role: UserRole

class RefreshToken(BaseModel):
    refresh_token: str = Field(..., pattern=r"^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$") 


class OutDevice(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    ip_address: str
    user_agent: str
    first_login_at: datetime
    last_logout_at: datetime | None

class OutUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    phone: str
    address: str
    role: UserRole
    created_at: datetime
    devices: list[OutDevice]