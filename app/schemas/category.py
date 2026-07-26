from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import List


class CreateImgages(BaseModel):
    url: str = Field(..., pattern=r"^/media/uploads/categories/[A-Za-z0-9_\-./]+\.(jpg|jpeg|png|webp)$")
    position: str = Field(..., min_length=1)

class CreateCategory(BaseModel):
    title: str = Field(..., min_length=1)
    images: List[CreateImgages] = Field(default_factory=list)

class UpdateCategory(BaseModel):
    title: str | None = Field(None, min_length=1)
    images: List[CreateImgages] | None = None

class OutCategory(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    created_at: datetime
    images: list[CreateImgages]