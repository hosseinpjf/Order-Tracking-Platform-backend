from pydantic import BaseModel, Field
from datetime import time
from typing import List

# ---------------------------------------<< Create >>---------------------------------------
class CreateImages(BaseModel):
    url: str = Field(..., pattern=r"^/media/uploads/site_info/[A-Za-z0-9_\-./]+\.(jpg|jpeg|png|webp)$")
    position: str = Field(..., min_length=1)

class CreateButton(BaseModel):
    text: str = Field(..., min_length=1)
    url: str = Field(..., min_length=1)
    order: int = Field(..., gt=0)
    is_visible: bool = True

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
    icon: str = Field(..., pattern=r"^/media/uploads/site_info/[A-Za-z0-9_\-./]+\.(jpg|jpeg|png|webp)$")
    order: int = Field(..., gt=0)
    is_visible: bool = True

class CreateTodaySuggestions(BaseModel):
    product_id: str = Field(..., min_length=1)
    order: int = Field(..., gt=0)
    is_visible: bool = True

class CreateSection(BaseModel):
    title: str | None = Field(None, min_length=1)
    subtitle: str | None = Field(None, min_length=1)
    content: str | None = Field(None, min_length=1)
    images: List[CreateImages] | None = None
    buttons: List[CreateButton] | None = None

class CreateHero(CreateSection): pass

class CreateFooter(CreateSection): pass

class CreateAboutUs(CreateSection): pass

class CreateContactUs(CreateSection): pass

# ---------------------------------------<< Update >>---------------------------------------
class UpdateImages(BaseModel):
    id: str
    url: str | None = Field(None, pattern=r"^/media/uploads/site_info/[A-Za-z0-9_\-./]+\.(jpg|jpeg|png|webp)$")
    position: str | None = Field(None, min_length=1)

class UpdateButton(BaseModel):
    id: str
    text: str | None = Field(None, min_length=1)
    url: str | None = Field(None, min_length=1)
    order: int | None = Field(None, gt=0)
    is_visible: bool | None = None

class UpdateSlogans(BaseModel):
    id: str
    text: str | None = Field(None, min_length=1)
    is_visible: bool | None = None

class UpdateLocation(BaseModel):
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)

class UpdatePhone(BaseModel):
    id: str
    title: str | None = Field(None, min_length=1)
    phone: str | None = Field(None, pattern=r"^09\d{9}$")
    order: int | None = Field(None, gt=0)
    is_visible: bool | None = None

class UpdateLink(BaseModel):
    id: str
    title: str | None = Field(None, min_length=1)
    url: str | None = Field(None, min_length=1)
    icon: str | None = Field(None, pattern=r"^/media/uploads/site_info/[A-Za-z0-9_\-./]+\.(jpg|jpeg|png|webp)$")
    order: int | None = Field(None, gt=0)
    is_visible: bool | None = None

class UpdateTodaySuggestions(BaseModel):
    id: str
    product_id: str | None = Field(None, min_length=1)
    order: int | None = Field(None, gt=0)
    is_visible: bool | None = None

class UpdateWorkingHours(BaseModel):
    id: str
    open_time: time | None = None
    close_time: time | None = None
    is_closed: bool | None = None

class UpdateSetting(BaseModel):
    id: str
    enabled: bool | None = None

class UpdateSection(BaseModel):
    title: str | None = None
    subtitle: str | None = None
    content: str | None = None
    images: List[UpdateImages] | None = None
    buttons: List[UpdateButton] | None = None

class UpdateHero(UpdateSection): pass

class UpdateFooter(UpdateSection): pass

class UpdateAboutUs(UpdateSection): pass

class UpdateContactUs(UpdateSection): pass

# ---------------------------------------<< Delete >>---------------------------------------
class DeleteId(BaseModel):
    id: str

class DeleteImages(DeleteId): pass

class DeleteButton(DeleteId): pass

class DeleteSlogans(DeleteId): pass

class DeletePhone(DeleteId): pass

class DeleteLink(DeleteId): pass

class DeleteTodaySuggestions(DeleteId): pass

class DeleteSection(BaseModel):
    images: List[DeleteImages] | None = None
    buttons: List[DeleteButton] | None = None

class DeleteHero(DeleteSection): pass

class DeleteFooter(DeleteSection): pass

class DeleteAboutUs(DeleteSection): pass

class DeleteContactUs(DeleteSection): pass
