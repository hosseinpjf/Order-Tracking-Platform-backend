from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from app.models.table_reservation import ReservationStatus
from app.schemas.table import OutTable
from app.schemas.user import OutUser



class CreateReservation(BaseModel):
    table_id: str
    start_time: datetime
    guests_count: int = Field(..., gt=0)

class UpdateStatus(BaseModel):
    status: ReservationStatus

class UpdateReservation(BaseModel):
    table_id: str | None = None
    start_time: datetime | None = None
    guests_count: int | None = Field(None, gt=0)


class OutReservation(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    table_id: str
    user_id: str
    start_time: datetime
    end_time: datetime
    guests_count: int
    status: ReservationStatus
    created_at: datetime

class OutFullReservation(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    table_id: str
    user_id: str
    start_time: datetime
    end_time: datetime
    guests_count: int
    status: ReservationStatus
    created_at: datetime
    table: OutTable
    user: OutUser