from pydantic import BaseModel

class RegisterUser(BaseModel):
    name: str
    phone: str
    password: str

class LoginUser(BaseModel):
    phone: str
    password: str