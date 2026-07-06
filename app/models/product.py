from sqlalchemy import Column, String, DateTime, Enum, Integer, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from sqlalchemy.ext.mutable import MutableList
import uuid
import enum
from app.db.base import Base

class ProductTags(enum.Enum):
    #  محصول تازه اضافه شده یا جدید در فروشگاه
    new = "new" 
    #  محصول پرطرفدار و پرفروش
    popular = "popular" 
    #  محصول دارای تخفیف فعال
    discounted = "discounted" 
    #  محصول محدود یا موجودی کم
    limited = "limited" 
    #  محصول مناسب برای گیاه‌خواران
    vegan = "vegan" 
    #  محصول بدون گلوتن
    gluten_free = "gluten_free" 
    #  محصول تند
    spicy = "spicy" 
    #  محصول داغ یا تازه آماده شده
    hot = "hot" 
    #  محصولی که بیشترین فروش را داشته
    best_seller = "best_seller" 
    #  محصول فصلی (مثلاً مخصوص تابستان یا زمستان)
    seasonal = "seasonal" 
    #  محصول پیشنهادی یا ویژه توسط ادمین
    recommended = "recommended" 
    #  محصول ویژهٔ سرآشپز یا اختصاصی
    chef_special = "chef_special" 
    #  محصول ارگانیک و طبیعی
    organic = "organic" 
    #  محصول لوکس یا باکیفیت بالا
    premium = "premium" 

class ProductSort(enum.Enum):
    newest = "newest"
    popular = "popular"
    price_desc = "price_desc"
    price_asc = "price_asc"
    discount_desc = "discount_desc"
    prepare_time_asc = "prepare_time_asc"

class Product(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True, index=True, default=lambda: uuid.uuid4().hex)
    
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)

    price = Column(Integer, nullable=False)
    discount_percent = Column(Integer, nullable=False, default=0)

    category_id = Column(String, ForeignKey("categories.id"), nullable=False)
    # category_id = Column(String, nullable=False)

    images = Column(JSON, default=list)
    is_available = Column(Boolean, nullable=False, default=True)

    likes = Column(MutableList.as_mutable(JSON), default=list)
    tags = Column(JSON, default=list)

    prepare_time = Column(Integer, nullable=False)

    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    

    category = relationship("Category", back_populates="products")
    # order_items = relationship("OrderItem", back_populates="product")