from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from app.models.table_reservation import ReservationStatus

class CreateReservation(BaseModel):
    table_id: str
    start_time: datetime
    guests_count: int = Field(..., gt=0)

class UpdateStatus(BaseModel):
    status: ReservationStatus

class OutReservation(BaseModel):
    id: str
    table_id: str
    user_id: str
    start_time: datetime
    end_time: datetime
    guests_count: int
    status: ReservationStatus
    created_at: datetime