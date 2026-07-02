from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from app.db.base import Base

class DeviceTracking(Base):
    __tablename__ = "device_tracking"

    id = Column(String, primary_key=True, index=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    device_id = Column(String(64), nullable=False, index=True, unique=True)
    user_agent = Column(String(2048), nullable=False)
    ip_address = Column(String, nullable=False)
    refresh_token = Column(String, nullable=False, unique=True)
    last_login_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))

    user = relationship("User", back_populates="devices")
