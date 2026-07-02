from pydantic import BaseModel

class DeviceData(BaseModel):
    device_id: str
