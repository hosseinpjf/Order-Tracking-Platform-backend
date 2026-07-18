from pydantic import BaseModel, Field
from typing import List
from app.schemas.base_site_info import CreateSlogans, CreateLocation, CreatePhone, CreateLink, CreateHero, CreateFooter, CreateAboutUs, CreateContactUs

class CreateSiteInfo(BaseModel):
    name: str | None = Field(None, min_length=1)
    slogans: List[CreateSlogans] | None = None
    logo: str | None = Field(None, pattern=r"^/media/uploads/[A-Za-z0-9_\-./]+\.(jpg|jpeg|png|webp)$")

    address: str | None = Field(None, min_length=1)
    location: CreateLocation | None = None

    phones: List[CreatePhone] | None = None

    links: List[CreateLink] | None = None

    # working_hours: List[CreateWorkingHours] | None = None

    today_suggestions: List[str] | None = None

    # settings: List[CreateSetting] | None = None

    table_reservation_time: int | None = Field(None, gt=0)
    
    hero: CreateHero | None = None
    footer: CreateFooter | None = None
    about_us: CreateAboutUs | None = None
    contact_us: CreateContactUs | None = None