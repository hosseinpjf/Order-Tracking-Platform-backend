from sqlalchemy import Column, String, DateTime, Enum, Integer, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
import enum
from app.db.base import Base

class OrderStatus(enum.Enum):
    pending = "pending"        # سفارش ثبت شده اما هزینه اش پرداخت نشده
    # تایید درگاه پرداختی
    confirmed = "confirmed"    # هزینه پرداخت شده و منتظر تایید
    # تایید ادمین
    preparing = "preparing"    # در حال آماده‌سازی
    # یا سیستم یا ادمین به سیستم اچازه خودکار نمیده تا خودش تایید کنه
    delivering = "delivering"  # در حال ارسال
    # اگر حضوری بود که این وضعیت وجود نداره در غیر این صورت پیک تایید میکنه که سفارش رسونده شده
    completed = "completed"    # نهایی شده
    canceled = "canceled"      # لغو شده

ALLOWED_TRANSITIONS = {
    OrderStatus.pending: {OrderStatus.confirmed, OrderStatus.canceled},
    OrderStatus.confirmed: {OrderStatus.preparing, OrderStatus.canceled},
    OrderStatus.preparing: {OrderStatus.delivering, OrderStatus.completed, OrderStatus.canceled},
    OrderStatus.delivering: {OrderStatus.completed, OrderStatus.canceled},
    OrderStatus.completed: set(),
    OrderStatus.canceled: set(),
}

class OrderType(enum.Enum):
    takeaway = "takeaway"      # کاربر سفارش می‌دهد و خودش می‌آید می‌برد
    delivery = "delivery"      # سفارش باید ارسال شود
    dine_in = "dine_in"        # سفارش برای مصرف داخل مجموعه است

class PaymentType(enum.Enum):
    online = "online"      # پرداخت آنلاین توسط کاربر
    offline = "offline"    # پرداخت حضوری (نقدی یا کارت‌خوان)

class OrderSort(enum.Enum):
    price_desc = "price_desc"                 # گران ترین
    price_asc = "price_asc"                   # ارزان ترین
    items_desc = "items_desc"                 # دارای بیشترین آیتم
    items_asc = "items_asc"                   # دارای کمترین آیتم
    prepare_time_desc = "prepare_time_desc"   # سریع ترین آماده سازی
    prepare_time_asc = "prepare_time_asc"     # کند ترین آماده سازی

class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, index=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    user_name = Column(String, nullable=False)

    status = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.pending)
    order_type = Column(Enum(OrderType), nullable=False)
    payment_type = Column(Enum(PaymentType), nullable=False)
    items_count = Column(Integer, nullable=False, default=0)

    original_total_price = Column(Integer, nullable=False)
    final_total_price = Column(Integer, nullable=False)
    total_prepare_time = Column(Integer, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    status_history = relationship("OrderStatusHistory", back_populates="order", order_by="OrderStatusHistory.start_at", cascade="all, delete-orphan")