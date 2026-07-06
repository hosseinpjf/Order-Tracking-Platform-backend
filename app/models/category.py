from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from app.db.base import Base

class Category(Base):
    __tablename__ = "categories"

    id = Column(String, primary_key=True, index=True, default=lambda: uuid.uuid4().hex)
    title = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    products = relationship("Product", back_populates="category", cascade="all, delete-orphan")