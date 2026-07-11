from sqlalchemy import Column, String, DateTime, Enum, Integer, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from sqlalchemy.ext.mutable import MutableList
import uuid
import enum
from app.db.base import Base


class TableStatus(enum.Enum):
    free = "free"           # آزاد
    reserved = "reserved"   # رزرو شده
    occupied = "occupied"   # اشغال
    cleaning = "cleaning"   # در حال نظافت

class TableTags(enum.Enum):
    vip = "vip"                     # میز ویژه یا لوکس
    window_side = "window_side"     # کنار پنجره
    outdoor = "outdoor"             # فضای باز
    smoking = "smoking"             # مخصوص افراد سیگاری
    non_smoking = "non_smoking"     # غیرسیگاری
    family = "family"               # مناسب خانواده
    couple = "couple"               # مناسب دو نفره / رمانتیک
    booth = "booth"                 # میز با صندلی‌های کاناپه‌ای
    quiet = "quiet"                 # محیط آرام
    near_stage = "near_stage"       # نزدیک صحنه یا موزیک زنده
    near_bar = "near_bar"           # نزدیک بار
    accessible = "accessible"       # مناسب افراد دارای معلولیت
    kids_friendly = "kids_friendly" # مناسب کودکان
    private = "private"             # فضای خصوصی


class Table(Base):
    __tablename__ = "tables"

    id = Column(String, primary_key=True, index=True, default=lambda: uuid.uuid4().hex)
    number = Column(Integer, unique=True, nullable=False)
    image = Column(String, nullable=False)
    capacity = Column(Integer, nullable=False)
    location = Column(String, nullable=False)
    status = Column(Enum(TableStatus), default=TableStatus.free)
    tags = Column(JSON, default=list)