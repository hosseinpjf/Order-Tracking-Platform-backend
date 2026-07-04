from pydantic import BaseModel, Field

class DeviceData(BaseModel):
    device_id: str = Field(..., min_length=5, max_length=100)
