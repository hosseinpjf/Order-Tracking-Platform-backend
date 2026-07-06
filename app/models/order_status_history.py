from sqlalchemy import Column, String, DateTime, Enum, Integer, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
import enum
from app.db.base import Base
from app.models.order import OrderStatus


class StatusChangedBy(enum.Enum):
    user = "user"
    admin = "admin"
    system = "system"


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"

    id = Column(String, primary_key=True, index=True, default=lambda: uuid.uuid4().hex)
    order_id = Column(String, ForeignKey("orders.id"), nullable=False)

    status = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.pending)
    duration_seconds = Column(Integer, default=0)
    changed_by = Column(Enum(StatusChangedBy), nullable=False)

    start_at = Column(DateTime, default=datetime.now(timezone.utc))
    end_at = Column(DateTime)


    order = relationship("Order", back_populates="status_history")

