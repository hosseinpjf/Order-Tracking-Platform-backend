from pydantic import BaseModel
from datetime import datetime

class CreateDevice(BaseModel):
    device_name: str
    ip_address: str
    refresh_token_hash: str

class UpdateDevice(BaseModel):
    device_name: str
    ip_address: str
    refresh_token_hash: str
    last_login_at: datetime
