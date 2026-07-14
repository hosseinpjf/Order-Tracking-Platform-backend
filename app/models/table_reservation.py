from sqlalchemy import Column, String, DateTime, Enum, Integer, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
import enum
from app.db.base import Base


class ReservationStatus(enum.Enum):
    pending = "pending"         # درخواست ثبت شده و منتظر تایید
    confirmed = "confirmed"     # رزرو تایید شده
    seated = "seated"           # مشتری روی میز نشسته و استفاده از میز شروع شده
    completed = "completed"     # استفاده از میز به پایان رسیده و رزرو با موفقیت تمام شده
    expired = "expired"         # مشتری تا پایان زمان مجاز مراجعه نکرده و رزرو منقضی شده
    cancelled = "cancelled"     # توسط کاربر یا ادمین لغو شده
    rejected = "rejected"       # توسط ادمین رد شده

class TableReservation(Base):
    __tablename__ = "table_reservations"

    id = Column(String, primary_key=True, index=True, default=lambda: uuid.uuid4().hex)
    table_id = Column(String, ForeignKey("tables.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    user_name = Column(String, nullable=False)

    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)

    guests_count = Column(Integer, nullable=False)
    status = Column(Enum(ReservationStatus), default=ReservationStatus.pending)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    table = relationship("Table", back_populates="reservations")
    user = relationship("User", back_populates="reservations")