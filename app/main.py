from fastapi import FastAPI
from .db.database import engine
from .db.base import Base

from app.models.user import User

app = FastAPI()

Base.metadata.create_all(bind=engine)