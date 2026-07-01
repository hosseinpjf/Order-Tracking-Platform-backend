from fastapi import FastAPI, HTTPException
from .db.database import engine
from .db.base import Base
from .middleware.exception_handler import http_exception_handler, general_exception_handler

from .models.user import User
from .routers.users import router as router_users

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(router_users)

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)