from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from app.db.base import Base


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(String, primary_key=True, index=True, default=lambda: uuid.uuid4().hex)
    order_id = Column(String, ForeignKey("orders.id"), nullable=False)
    product_id = Column(String, ForeignKey("products.id"), nullable=False)

    quantity = Column(Integer, nullable=False, default=1)
    price_at_time = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")