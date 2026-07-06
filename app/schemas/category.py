from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class CreateCategory(BaseModel):
    title: str = Field(..., min_length=1)

class OutCategory(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    created_at: datetime