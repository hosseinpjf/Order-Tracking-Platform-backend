from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
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

    refresh_token = Column(String, unique=True)
    access_version = Column(Integer, default=1)

    first_login_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    last_login_at = Column(DateTime(timezone=True), nullable=False)
    logout_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="devices")
