from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from .db.database import engine
from .db.base import Base
from .middleware.exception_handler import http_exception_handler, general_exception_handler, validation_exception_handler
from .middleware.cors import setup_cors

from .routers.users import router as router_users
from .routers.devices_tracking import router as router_devices_tracking
from .routers.products import router as router_products
from .routers.uploads import router as router_uploads
from .routers.categories import router as router_categories
from .routers.orders import router as router_orders
from .routers.tables import router as router_tables


app = FastAPI()

Base.metadata.create_all(bind=engine)

setup_cors(app)

app.include_router(router_users)
app.include_router(router_devices_tracking)
app.include_router(router_products)
app.include_router(router_uploads)
app.include_router(router_categories)
app.include_router(router_orders)
app.include_router(router_tables)

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

app.mount("/media", StaticFiles(directory="media"), name="media")
