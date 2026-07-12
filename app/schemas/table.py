from pydantic import BaseModel, Field, ConfigDict
from typing import List
from app.models.table import TableTags, TableStatus


class CreateTable(BaseModel):
    number: int = Field(..., gt=0)
    image: str = Field(..., pattern=r"^/media/uploads/[A-Za-z0-9_\-./]+\.(jpg|jpeg|png|webp)$")
    capacity: int = Field(..., gt=0)
    location: str = Field(..., min_length=1)
    status: TableStatus = TableStatus.free
    tags: List[TableTags] = Field(default_factory=list)

class UpdateTable(BaseModel):
    number: int | None = Field(None, gt=0)
    image: str | None = Field(None, pattern=r"^/media/uploads/[A-Za-z0-9_\-./]+\.(jpg|jpeg|png|webp)$")
    capacity: int | None = Field(None, gt=0)
    location: str | None = Field(None, min_length=1)
    status: TableStatus | None = None
    tags: List[TableTags] | None = None


class OutTable(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    number: int
    image: str
    capacity: int
    location: str
    status: TableStatus
    tags: List[TableTags]