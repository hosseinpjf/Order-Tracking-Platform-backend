from fastapi import FastAPI
from .db.database import engine
from .db.base import Base

app = FastAPI()

Base.metadata.create_all(bind = engine)