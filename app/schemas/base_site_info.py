from pydantic import BaseModel, Field
from datetime import time
from typing import List
from app.models.site_info import DaysWeek, SiteInfoSettings

class BaseImages(BaseModel):
    url: str = Field(..., pattern=r"^/media/uploads/[A-Za-z0-9_\-./]+\.(jpg|jpeg|png|webp)$")
    position: str | None = Field(None, gt=0)

class BaseButton(BaseModel):
    text: str = Field(..., gt=0)
    url: str = Field(..., gt=0)

class BaseLocation(BaseModel):
    latitude: float = Field(...)
    longitude: float = Field(...)

class BasePhone(BaseModel):
    id: str = Field(..., gt=0)
    title: str = Field(..., gt=0)
    phone: str = Field(..., pattern=r"^09\d{9}$")
    order: int = Field(..., gt=0)
    is_visible: bool = True

class BaseLink(BaseModel):
    id: str = Field(..., gt=0)
    title: str = Field(..., gt=0)
    url: str = Field(..., gt=0)
    icon: str = Field(..., gt=0)
    order: int = Field(..., gt=0)
    is_visible: bool = True

class BaseWorkingHours(BaseModel):
    id: str = Field(..., gt=0)
    day: DaysWeek
    open_time: time
    close_time: time
    is_closed: bool = None

class BaseSetting(BaseModel):
    capability: SiteInfoSettings
    enabled: bool = True

class BaseSection(BaseModel):
    title: str = Field(..., gt=0)
    subtitle: str | None = Field(None, gt=0)
    content: str = Field(..., gt=0)
    images: List[BaseImages] = Field(default_factory=list)
    buttons: List[BaseButton] = Field(default_factory=list)

class BaseHero(BaseSection): pass

class BaseFooter(BaseSection): pass

class BaseAboutUs(BaseSection): pass

class BaseContactUs(BaseSection): pass
