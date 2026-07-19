from pydantic import BaseModel, Field
from typing import List
from app.schemas.base_site_info import CreateSlogans, CreateLocation, CreatePhone, CreateLink, CreateTodaySuggestions, CreateHero, CreateFooter, CreateAboutUs, CreateContactUs, UpdateSlogans, UpdateLocation, UpdatePhone, UpdateLink, UpdateTodaySuggestions, UpdateWorkingHours, UpdateSetting, UpdateHero, UpdateFooter, UpdateAboutUs, UpdateContactUs

class CreateSiteInfo(BaseModel):
    name: str | None = Field(None, min_length=1)
    slogans: List[CreateSlogans] | None = None
    logo: str | None = Field(None, pattern=r"^/media/uploads/site_info/[A-Za-z0-9_\-./]+\.(jpg|jpeg|png|webp)$")

    address: str | None = Field(None, min_length=1)
    location: CreateLocation | None = None

    phones: List[CreatePhone] | None = None

    links: List[CreateLink] | None = None

    today_suggestions: List[CreateTodaySuggestions] | None = None

    table_reservation_time: int | None = Field(None, gt=0)
    
    hero: CreateHero | None = None
    footer: CreateFooter | None = None
    about_us: CreateAboutUs | None = None
    contact_us: CreateContactUs | None = None



class UpdateSiteInfo(BaseModel):
    name: str | None = Field(None, min_length=1)
    slogans: List[UpdateSlogans] | None = None
    logo: str | None = Field(None, pattern=r"^/media/uploads/site_info/[A-Za-z0-9_\-./]+\.(jpg|jpeg|png|webp)$")

    address: str | None = Field(None, min_length=1)
    location: UpdateLocation | None = None

    phones: List[UpdatePhone] | None = None

    links: List[UpdateLink] | None = None

    working_hours: List[UpdateWorkingHours] | None = None

    today_suggestions: List[UpdateTodaySuggestions] | None = None

    settings: List[UpdateSetting] | None = None

    table_reservation_time: int | None = Field(None, gt=0)
    
    hero: UpdateHero | None = None
    footer: UpdateFooter | None = None
    about_us: UpdateAboutUs | None = None
    contact_us: UpdateContactUs | None = None