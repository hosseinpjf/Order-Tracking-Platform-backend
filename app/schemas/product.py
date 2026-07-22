from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import List
from app.models.product import ProductTags

class ImageSchema(BaseModel):
    url: str = Field(..., pattern=r"^/media/uploads/products/[A-Za-z0-9_\-./]+\.(jpg|jpeg|png|webp)$")
    position: str = Field(..., min_length=1)

class CreateProduct(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    price: int = Field(..., gt=0)
    discount_percent: int = Field(default=0, ge=0, le=100)
    category_id: str
    images: List[ImageSchema] = Field(default_factory=list)
    is_available: bool = True
    tags: List[ProductTags] = Field(default_factory=list)
    prepare_time: int = Field(..., gt=0)


class UpdateProduct(BaseModel):
    title: str | None = Field(None, min_length=1)
    description: str | None = Field(None, min_length=1)
    price: int | None = Field(None, gt=0)
    discount_percent: int | None = Field(None, ge=0, le=100)
    category_id: str | None = None
    images: List[ImageSchema] | None = None
    is_available: bool | None = None
    tags: List[ProductTags] | None = None
    prepare_time: int | None = Field(None, gt=0)

class OutProduct(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    description: str
    price: int
    discount_percent: int
    prepare_time: int
    category_id: str
    likes: list
    is_available: bool
    tags: list[ProductTags]
    images: list[ImageSchema]
    created_at: datetime
    updated_at: datetime
