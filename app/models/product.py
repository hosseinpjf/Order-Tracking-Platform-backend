from sqlalchemy import Column, String, DateTime, Enum, Integer, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from sqlalchemy.ext.mutable import MutableList
import uuid
import enum
from app.db.base import Base


class ProductTags(enum.Enum):
    new = "new"                     #  محصول تازه اضافه شده یا جدید در فروشگاه
    popular = "popular"             #  محصول پرطرفدار و پرفروش
    discounted = "discounted"       #  محصول دارای تخفیف فعال
    limited = "limited"             #  محصول محدود یا موجودی کم
    vegan = "vegan"                 #  محصول مناسب برای گیاه‌خواران
    gluten_free = "gluten_free"     #  محصول بدون گلوتن
    spicy = "spicy"                 #  محصول تند
    hot = "hot"                     # محصول داغ یا تازه آماده شده
    best_seller = "best_seller"     #  محصولی که بیشترین فروش را داشته
    seasonal = "seasonal"           #  محصول فصلی (مثلاً مخصوص تابستان یا زمستان)
    recommended = "recommended"     #  محصول پیشنهادی یا ویژه توسط ادمین
    chef_special = "chef_special"   #  محصول ویژهٔ سرآشپز یا اختصاصی
    organic = "organic"             #  محصول ارگانیک و طبیعی
    premium = "premium"             #  محصول لوکس یا باکیفیت بالا

class ProductSort(enum.Enum):
    newest = "newest"                       # جدید ترین
    popular = "popular"                     # معروف ترین
    price_desc = "price_desc"               # گران ترین
    price_asc = "price_asc"                 # ارزان ترین
    discount_desc = "discount_desc"         # بیشترین تخفیف
    prepare_time_asc = "prepare_time_asc"   # زمان آماده سازی

class ProductChartType(enum.Enum):
    best_selling_products = "best_selling_products"
    highest_revenue_products = "highest_revenue_products"
    price_distribution = "price_distribution"
    tags_distribution = "tags_distribution"


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

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    

    category = relationship("Category", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product")