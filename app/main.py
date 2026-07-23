from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import asyncio
import logging

from .db.database import engine
from .db.base import Base
from .db.session import SessionLocal
from .config.settings import settings
from .middleware.exception_handler import http_exception_handler, general_exception_handler, validation_exception_handler
from .middleware.cors import setup_cors
from .utils.get_site_info import get_settings
from .config import logging_config

from .routers.users import router as router_users
from .routers.devices_tracking import router as router_devices_tracking
from .routers.products import router as router_products
from .routers.uploads import router as router_uploads
from .routers.categories import router as router_categories
from .routers.orders import router as router_orders
from .routers.tables import router as router_tables
from .routers.table_reservations import router as router_table_reservations
from .routers.site_info import router as router_site_info
from .routers.site_contents import router as router_site_contents
from .routers.message_ws import router as router_message_ws

from .core.init_site_info import init_settings, init_working_hours
from .jobs.table_reservation import auto_update_reservations
from .jobs.order_status_history import auto_update_order_status

logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

async def reservation_scheduler():
    while True:
        db = SessionLocal()
        try:
            db_settings = get_settings(db, ["auto_expire_reservations", "auto_complete_reservations", "auto_complete_preparing"])

            if db_settings["auto_expire_reservations"] or db_settings["auto_complete_reservations"]:
                auto_update_reservations(db, db_settings)
            if db_settings["auto_complete_preparing"]:
                auto_update_order_status(db)

        except Exception:
            logger.exception("Scheduler error")
        finally:
            db.close()

        await asyncio.sleep(settings.JOB_INTERVAL_SECONDS)

@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()
    try:
        init_settings(db)
        init_working_hours(db)
    finally:
        db.close()

    task = asyncio.create_task(reservation_scheduler())

    yield

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

app = FastAPI(lifespan=lifespan)

setup_cors(app)

app.include_router(router_users)
app.include_router(router_devices_tracking)
app.include_router(router_products)
app.include_router(router_uploads)
app.include_router(router_categories)
app.include_router(router_orders)
app.include_router(router_tables)
app.include_router(router_table_reservations)
app.include_router(router_site_info)
app.include_router(router_site_contents)
app.include_router(router_message_ws)

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

app.mount("/media", StaticFiles(directory="media"), name="media")

