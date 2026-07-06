from sqlalchemy import Column, String, DateTime, Enum, Integer, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
import enum
from app.db.base import Base

class OrderStatus(enum.Enum):
    pending = "pending"        # سفارش ثبت شده
    confirmed = "confirmed"    # سفارش تأیید شده
    preparing = "preparing"    # در حال آماده‌سازی
    ready = "ready"            # آماده برای ارسال
    delivering = "delivering"  # در حال ارسال
    delivered = "delivered"    # تحویل داده شده
    completed = "completed"    # نهایی شده
    canceled = "canceled"      # لغو شده

class OrderType(enum.Enum):
    takeaway = "takeaway"      # کاربر سفارش می‌دهد و خودش می‌آید می‌برد
    delivery = "delivery"      # سفارش باید ارسال شود
    dine_in = "dine_in"        # سفارش برای مصرف داخل مجموعه است

class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, index=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    status = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.pending)
    order_type = Column(Enum(OrderType), nullable=False)

    original_total_price = Column(Integer, nullable=False)
    final_total_price = Column(Integer, nullable=False)
    total_prepare_time = Column(Integer, nullable=False)
    
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    # status_history = relationship("OrderStatusHistory", back_populates="order", cascade="all, delete-orphan")