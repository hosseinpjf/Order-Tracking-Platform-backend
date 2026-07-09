from sqlalchemy import Column, String, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
import enum
from app.db.base import Base

class UserRole(enum.Enum):
    admin = "admin"
    user = "user"

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True, default=lambda: uuid.uuid4().hex)
    name = Column(String(50), nullable=False)
    phone = Column(String(11), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    address = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.user, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    devices = relationship("DeviceTracking", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user")
    