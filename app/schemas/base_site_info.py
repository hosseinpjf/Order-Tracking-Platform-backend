from pydantic import BaseModel, Field
from datetime import time
from typing import List
from app.models.site_info import DaysWeek, SiteInfoSettings

class CreateImages(BaseModel):
    url: str = Field(..., pattern=r"^/media/uploads/[A-Za-z0-9_\-./]+\.(jpg|jpeg|png|webp)$")
    position: str = Field(..., min_length=1)

class CreateButton(BaseModel):
    text: str = Field(..., min_length=1)
    url: str = Field(..., min_length=1)

class CreateSlogans(BaseModel):
    text: str = Field(..., min_length=1)
    is_visible: bool = True

class CreateLocation(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)

class CreatePhone(BaseModel):
    title: str = Field(..., min_length=1)
    phone: str = Field(..., pattern=r"^09\d{9}$")
    order: int = Field(..., gt=0)
    is_visible: bool = True

class CreateLink(BaseModel):
    title: str = Field(..., min_length=1)
    url: str = Field(..., min_length=1)
    icon: str = Field(..., min_length=1)
    order: int = Field(..., gt=0)
    is_visible: bool = True

# class CreateWorkingHours(BaseModel):
#     day: DaysWeek
#     open_time: time
#     close_time: time
#     is_closed: bool = False

# class CreateSetting(BaseModel):
#     capability: SiteInfoSettings
#     enabled: bool

class CreateSection(BaseModel):
    title: str | None = Field(None, min_length=1)
    subtitle: str | None = Field(None, min_length=1)
    content: str = Field(..., min_length=1)
    images: List[CreateImages] | None = None
    buttons: List[CreateButton] | None = None

class CreateHero(CreateSection): pass

class CreateFooter(CreateSection): pass

class CreateAboutUs(CreateSection): pass

class CreateContactUs(CreateSection): pass

