from sqlalchemy import Column, String, DateTime, JSON, Integer
from datetime import datetime, timezone
from sqlalchemy.ext.mutable import MutableList, MutableDict
import enum
from app.db.base import Base


class SiteInfoSettings(enum.Enum):
    # Order Settings
    accept_order = "accept_order"                                   # آیا سیستم سفارش را قبول کند یا نه
    allow_online_payment = "allow_online_payment"                   # فعال/غیرفعال کردن پرداخت آنلاین
    allow_offline_payment = "allow_offline_payment"                 # فعال/غیرفعال کردن پرداخت حضوری
    auto_complete_preparing = "auto_complete_preparing"             # آیا سفارش‌های preparing خودکار تغییر وضعیت دهند
    show_today_suggestions = "show_today_suggestions"               # نمایش/عدم نمایش پیشنهادهای امروز
    # Table Reservation Settings
    allow_table_reservation = "allow_table_reservation"             # فعال/غیرفعال کردن رزرو میز
    auto_expire_reservations = "auto_expire_reservations"           # expire خودکار رزروها
    auto_complete_reservations = "auto_complete_reservations"       # complete خودکار رزروهای seated
    show_reservation_section = "show_reservation_section"           # نمایش/عدم نمایش بخش رزرو در سایت
    # Content & UI Settings
    show_statistics = "show_statistics"                             # نمایش/عدم نمایش آمار
    show_gallery = "show_gallery"                                   # نمایش/عدم نمایش گالری
    show_announcements = "show_announcements"                       # نمایش اطلاعیه‌ها
    show_banners = "show_banners"                                   # نمایش بنرها
    show_features = "show_features"                                 # نمایش ویژگی‌ها
    show_facilities = "show_facilities"                             # نمایش امکانات
    show_services = "show_services"                                 # نمایش خدمات
    show_team_members = "show_team_members"                         # نمایش اعضای تیم
    show_faqs = "show_faqs"                                         # نمایش سوالات متداول
    # General Settings
    site_open = "site_open"                                         # آیا سایت باز است یا بسته
    show_contact_info = "show_contact_info"                         # نمایش/عدم نمایش اطلاعات تماس
    show_working_hours = "show_working_hours"                       # نمایش ساعات کاری
    maintenance_mode = "maintenance_mode"                           # حالت تعمیرات

class DaysWeek(enum.Enum):
    saturday = "saturday"
    sunday = "sunday"
    monday = "monday"
    tuesday = "tuesday"
    wednesday = "wednesday"
    thursday = "thursday"
    friday = "friday"

class SiteInfo(Base):
    __tablename__ = "site_info"

    id = Column(String, primary_key=True, default="1")

    name = Column(String(50), nullable=True)
    slogans = Column(MutableList.as_mutable(JSON), default=list)
    logo = Column(String, nullable=True)
    
    address = Column(String, nullable=True)
    location = Column(MutableDict.as_mutable(JSON), default=dict)

    phones = Column(MutableList.as_mutable(JSON), default=list)
    links = Column(MutableList.as_mutable(JSON), default=list)

    working_hours = Column(MutableList.as_mutable(JSON), default=list)

    today_suggestions = Column(MutableList.as_mutable(JSON), default=list)

    settings = Column(MutableList.as_mutable(JSON), default=list)

    table_reservation_time = Column(Integer, default=30)

    hero = Column(MutableDict.as_mutable(JSON), default=dict)
    footer = Column(MutableDict.as_mutable(JSON), default=dict)
    about_us = Column(MutableDict.as_mutable(JSON), default=dict)
    contact_us = Column(MutableDict.as_mutable(JSON), default=dict)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))