from pydantic import BaseModel

class CreateDevice(BaseModel):
    device_id: str

class UpdateDevice(BaseModel):
    device_id: str
