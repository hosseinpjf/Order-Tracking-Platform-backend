from sqlalchemy import Column, String, DateTime, Enum, Integer, Boolean, JSON
from datetime import datetime, timezone
from sqlalchemy.ext.mutable import MutableList, MutableDict
import uuid
import enum
from app.db.base import Base


class SiteContentType(enum.Enum):
    statistics = "statistics"
    announcements = "announcements"
    banners = "banners"
    gallery = "gallery"
    facilities = "facilities"
    services = "services"
    features = "features"
    faqs = "faqs"
    team_members = "team_members"

class SiteContentSort(enum.Enum):
    created_at_desc = "created_at_desc"
    created_at_asc = "created_at_asc"
    updated_at_desc = "updated_at_desc"
    updated_at_asc = "updated_at_asc"
    order_desc = "order_desc"
    order_asc = "order_asc"


class SiteContent(Base):
    __tablename__ = "site_contents"

    id = Column(String, primary_key=True, index=True, default=lambda: uuid.uuid4().hex)
    
    type = Column(Enum(SiteContentType), nullable=False, index=True)

    title = Column(String, nullable=True)
    subtitle = Column(String, nullable=True)
    content = Column(MutableDict.as_mutable(JSON), nullable=True, default=dict)

    images = Column(MutableList.as_mutable(JSON), nullable=True, default=list)
    icons = Column(MutableList.as_mutable(JSON), nullable=True, default=list)
    buttons = Column(MutableList.as_mutable(JSON), nullable=True, default=list)

    order = Column(Integer, nullable=False)
    position = Column(String, nullable=True)
    is_visible = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    