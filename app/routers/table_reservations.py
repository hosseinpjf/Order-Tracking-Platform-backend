from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone, time, timedelta
import math
from app.db.session import get_db
from app.services.jwt_bearer import get_payload
from app.middleware.exception_handler import response_handler
from app.models.table_reservation import TableReservation, ReservationStatus, ALLOWED_TRANSITIONS_RESERVATION
from app.models.table import Table, TableStatus
from app.models.user import User
from app.schemas.table_reservation import CreateReservation, OutReservation, UpdateStatus, UpdateReservation
from app.schemas.shared_table import OutFullReservation
from app.utils.get_site_info import get_working_hours, get_site_info
from app.utils.get_site_info import get_settings


router = APIRouter(prefix="/table-reservation", tags=["Table Reservation"])


@router.post("/")
def create_reservation(data: CreateReservation, payload = Depends(get_payload), db: Session = Depends(get_db)):
    try:
        db_settings = get_settings(db, ["allow_table_reservation"])
        if not db_settings["allow_table_reservation"]:
            raise HTTPException(status_code=400, detail="Allow table reservation disabled")

        db_table = db.query(Table).filter(Table.id == data.table_id).with_for_update().first()
        if not db_table:
            raise HTTPException(status_code=404, detail="Table not found")
        
        if db_table.status != TableStatus.free:
            raise HTTPException(status_code=400, detail="Table cannot be reserved")
        
        if data.guests_count > db_table.capacity:
            raise HTTPException(status_code=400, detail="Guests exceed table capacity")
        
        now_time = datetime.now(timezone.utc)
        if data.start_time <= now_time:
            raise HTTPException(status_code=400, detail="Start time must be in the future")
        
        db_site_info = get_site_info(db)
        table_reservation_time = db_site_info.table_reservation_time
        if not table_reservation_time:
            raise HTTPException(status_code=404, detail="Table reservation time not found")
        
        reservation_duration = timedelta(minutes=int(table_reservation_time))
        end_time = data.start_time + reservation_duration

        workday = get_working_hours(db, data.start_time)
        open_time = workday["open_time"]
        close_time = workday["close_time"]
        is_closed = workday["is_closed"]

        if is_closed:
            raise HTTPException(status_code=400, detail="Cafe is closed on the selected day")

        open_dt = datetime.combine(data.start_time.date(), open_time).replace(tzinfo=timezone.utc)
        close_dt = datetime.combine(data.start_time.date(), close_time).replace(tzinfo=timezone.utc)
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
            table_number = db_table.number,
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


@router.get("/")
def get_reservations(
    payload = Depends(get_payload),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1), 
    limit: int = Query(20, ge=1, le=100),
    status: ReservationStatus | None = Query(None),
    user_id: str | None = Query(None),
    q: str | None = Query(None),
    from_date: datetime | None = Query(None),
    to_date: datetime | None = Query(None),
    from_time: time | None = Query(None),
    to_time: time | None = Query(None),
    table_number: int | None = Query(None, gt=0),
):
    try:
        db_reservation = []
        query = db.query(TableReservation).order_by(TableReservation.start_time.desc())

        if payload["role"] != "admin":
            query = query.filter(TableReservation.user_id == payload["sub"])

        if payload["role"] == "admin" and user_id:
            query = query.filter(TableReservation.user_id == user_id)
        if payload["role"] == "admin" and q:
            query = query.filter(TableReservation.user_name.ilike(f"%{q}%"))

        if status:
            query = query.filter(TableReservation.status == status)

        if from_date:
            query = query.filter(TableReservation.start_time >= from_date)
        if to_date:
            query = query.filter(TableReservation.start_time <= to_date)

        if from_time:
            query = query.filter(func.time(TableReservation.start_time) >= from_time)
        if to_time:
            query = query.filter(func.time(TableReservation.start_time) <= to_time)

        if table_number:
            query = query.join(Table).filter(Table.number == table_number)

        db_reservation_total = query.count()
        db_reservation = query.offset((page - 1) * limit).limit(limit).all()

        return response_handler(
            status=True,
            message="Reservations fetched successfully",
            data={
                "reservations": [
                    OutReservation.model_validate(reservation).model_dump()
                    for reservation in db_reservation
                ],
                "page": page,
                "limit": limit,
                "total": db_reservation_total,
                "pages": math.ceil(db_reservation_total / limit)
            },
            status_code=200
        )
    except HTTPException as http_error:
        raise http_error
    except Exception:
        raise HTTPException(status_code=500, detail="Reservation fetch failed")


@router.get("/{reservation_id}")
def get_reservation(reservation_id: str, payload = Depends(get_payload), db: Session = Depends(get_db)):
    try:
        db_reservation = db.query(TableReservation).filter(TableReservation.id == reservation_id).first()
        if not db_reservation:
            raise HTTPException(status_code=404, detail="Reservation not found")

        if payload["role"] != "admin" and payload["sub"] != db_reservation.user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return response_handler(
            status=True,
            message="Reservation found",
            data=OutFullReservation.model_validate(db_reservation).model_dump(),
            status_code=200
        )
    except HTTPException as http_error:
        raise http_error
    except Exception:
        raise HTTPException(status_code=500, detail="Reservation fetch failed")


@router.patch("/{reservation_id}/status")
def update_status(reservation_id: str, data: UpdateStatus, payload = Depends(get_payload), db: Session = Depends(get_db)):
    try:
        db_reservation = db.query(TableReservation).filter(TableReservation.id == reservation_id).first()
        if not db_reservation:
            raise HTTPException(status_code=404, detail="TableReservation not found")
        
        if payload["role"] != "admin":
            if payload["sub"] != db_reservation.user_id:
                raise HTTPException(status_code=403, detail="Access denied")
            if data.status != ReservationStatus.cancelled:
                raise HTTPException(status_code=403, detail="Users can only cancel their own TableReservations")

        allowed = ALLOWED_TRANSITIONS_RESERVATION.get(db_reservation.status, set())
        if data.status not in allowed:
            raise HTTPException(status_code=400, detail="Invalid status transition")

        db_reservation.status = data.status
        db.commit()
        db.refresh(db_reservation)

        return response_handler(
            status=True,
            message="Reservation status updated",
            data=OutReservation.model_validate(db_reservation).model_dump(),
            status_code=200
        )
    except HTTPException as http_error:
        db.rollback()
        raise http_error
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Reservation update failed")


@router.patch("/{reservation_id}")
def update_reservation(reservation_id: str, data: UpdateReservation, payload = Depends(get_payload), db: Session = Depends(get_db)):
    try:
        if data.table_id is None and data.guests_count is None and data.start_time is None:
            raise HTTPException(status_code=400, detail="No fields provided for update")

        db_reservation = db.query(TableReservation).filter(TableReservation.id == reservation_id).first()
        if not db_reservation:
            raise HTTPException(status_code=404, detail="Reservation not found")

        if payload["role"] != "admin" and payload["sub"] != db_reservation.user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        if db_reservation.status not in [ReservationStatus.pending]:
            raise HTTPException(status_code=400, detail="Reservation cannot be modified in this status")
        
        db_site_info = get_site_info(db)
        table_reservation_time = db_site_info.table_reservation_time
        if not table_reservation_time:
            raise HTTPException(status_code=404, detail="Table reservation time not found")
        
        reservation_duration = timedelta(minutes=int(table_reservation_time))
        
        new_table_id = data.table_id if data.table_id is not None else db_reservation.table_id
        new_guests_count = data.guests_count if data.guests_count is not None else db_reservation.guests_count
        new_start_time = data.start_time if data.start_time is not None else db_reservation.start_time
        new_end_time = new_start_time + reservation_duration

        db_table = db.query(Table).filter(Table.id == new_table_id).first()
        if not db_table:
            raise HTTPException(status_code=404, detail="Table not found")
        
        if db_table.status != TableStatus.free:
            raise HTTPException(status_code=400, detail="Table cannot be reserved")

        if db_table.capacity < new_guests_count:
            raise HTTPException(status_code=400, detail="Guests exceed table capacity")

        now_time = datetime.now(timezone.utc)
        if new_start_time <= now_time:
            raise HTTPException(status_code=400, detail="Start time must be in the future")

        workday = get_working_hours(db, new_start_time)
        open_time = workday["open_time"]
        close_time = workday["close_time"]
        is_closed = workday["is_closed"]

        if is_closed:
            raise HTTPException(status_code=400, detail="Cafe is closed on the selected day")

        open_dt = datetime.combine(new_start_time.date(), open_time).replace(tzinfo=timezone.utc)
        close_dt = datetime.combine(new_start_time.date(), close_time).replace(tzinfo=timezone.utc)
        if new_start_time < open_dt or new_end_time > close_dt:
            raise HTTPException(status_code=400, detail="Reservation is outside business hours")

        conflict = db.query(TableReservation).filter(
            TableReservation.table_id == new_table_id,
            TableReservation.id != db_reservation.id,
            TableReservation.status.in_([
                ReservationStatus.pending,
                ReservationStatus.confirmed,
                ReservationStatus.seated
            ]),
            TableReservation.start_time < new_end_time,
            TableReservation.end_time > new_start_time
        ).first()
        if conflict:
            raise HTTPException(status_code=409, detail="Table is not available at this time")
            
        db_reservation.start_time = new_start_time
        db_reservation.end_time = new_end_time
        db_reservation.table_id = new_table_id
        db_reservation.table_number = db_table.number
        db_reservation.guests_count = new_guests_count

        db.commit()
        db.refresh(db_reservation)

        return response_handler(
            status=True,
            message="Reservation update successful",
            data=OutReservation.model_validate(db_reservation).model_dump(),
            status_code=200
        )
    except HTTPException as http_error:
        db.rollback()
        raise http_error
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Reservation update failed")

