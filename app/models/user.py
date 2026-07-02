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
    name = Column(String(30), nullable=False)
    phone = Column(String(12), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.user, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    
    devices = relationship("DeviceTracking", back_populates="user", cascade="all, delete-orphan")