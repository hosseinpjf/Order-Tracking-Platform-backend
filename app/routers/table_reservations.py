from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone, timedelta
from app.db.session import get_db
from app.services.jwt_bearer import get_payload
from app.middleware.exception_handler import response_handler
from app.models.table_reservation import TableReservation, ReservationStatus
from app.models.table import Table
from app.models.user import User
from app.schemas.table_reservation import CreateReservation, OutReservation
from app.config.settings import settings



router = APIRouter(prefix="/table-reservation", tags=["Table Reservation"])


@router.post("/")
def create_reservation(data: CreateReservation, payload = Depends(get_payload), db: Session = Depends(get_db)):
    try:
        db_table = db.query(Table).filter(Table.id == data.table_id).with_for_update().first()
        if not db_table:
            raise HTTPException(status_code=404, detail="Table not found")
        
        if data.guests_count > db_table.capacity:
            raise HTTPException(status_code=400, detail="Guests exceed table capacity")
        
        now_time = datetime.now(timezone.utc)
        if data.start_time <= now_time:
            raise HTTPException(status_code=400, detail="Start time must be in the future")

        end_time = data.start_time + settings.RESERVATION_DURATION

        open_dt = datetime.combine(data.start_time.date(), settings.OPEN_TIME, tzinfo=timezone.utc)
        close_dt = datetime.combine(data.start_time.date(), settings.CLOSE_TIME, tzinfo=timezone.utc)
        if data.start_time < open_dt or end_time > close_dt:
            raise HTTPException(status_code=400, detail="Reservation is outside business hours")

        conflict = db.query(TableReservation).filter(
            TableReservation.table_id == data.table_id,
            TableReservation.status.in_([
                ReservationStatus.pending,
                ReservationStatus.confirmed,
                ReservationStatus.seated
            ]),
            TableReservation.start_time < end_time,
            TableReservation.end_time > data.start_time
        ).first()

        if conflict:
            raise HTTPException(status_code=409, detail="Table is not available at this time")
        
        db_user = db.query(User).filter(User.id == payload["sub"]).first()
        
        new_reservation = TableReservation(
            table_id = data.table_id,
            user_id = payload["sub"],
            user_name = db_user.name,
            start_time = data.start_time,
            end_time = end_time,
            guests_count = data.guests_count,
            status = ReservationStatus.pending,
        )
        db.add(new_reservation)
        db.commit()
        db.refresh(new_reservation)

        return response_handler(
            status=True,
            message="Reservation created successfully",
            data=OutReservation.model_validate(new_reservation).model_dump(),
            status_code=201
        )
    except HTTPException as http_error:
        db.rollback()
        raise http_error
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Reservation creation failed")

