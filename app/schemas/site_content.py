from pydantic import BaseModel, Field
from typing import List, Any


class CreateImages(BaseModel):
    url: str = Field(..., pattern=r"^/media/uploads/site_contents/[A-Za-z0-9_\-./]+\.(jpg|jpeg|png|webp)$")
    position: str = Field(..., min_length=1)

class CreateButton(BaseModel):
    text: str = Field(..., min_length=1)
    url: str = Field(..., min_length=1)
    order: int = Field(..., gt=0)
    is_visible: bool = True

class CreateSiteContent(BaseModel):
    title: str = Field(..., min_length=1)
    subtitle: str | None = Field(None, min_length=1)
    content: dict[str, Any] | list[Any] | None = None

    images: List[CreateImages] | None = None
    icons: List[CreateImages] | None = None
    buttons: List[CreateButton] | None = None

    order: int = Field(..., gt=0)
    position: str = Field(..., min_length=1)
    is_visible: bool = True
