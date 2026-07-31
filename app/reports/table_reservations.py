from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, time
from sqlalchemy import func, case
from app.db.session import get_db
from app.services.jwt_bearer import get_payload
from app.middleware.exception_handler import response_handler
from app.models.table_reservation import TableReservation, ReservationStatus
from app.utils.chart_helper import normalize_datetime


router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/table-reservation/kpi")
def get_table_reservation_summary(
    payload = Depends(get_payload),
    db: Session = Depends(get_db),
    from_date: datetime = Query(...),
    to_date: datetime = Query(...),
):
    try:
        if payload["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        from_date = normalize_datetime(from_date)
        to_date = normalize_datetime(to_date)
        end_of_to_date = datetime.combine(to_date.date(), time.max)

        summary = (
            db.query(
                func.count(TableReservation.id).label("total_reservations"),
                func.sum(
                    case(
                        (TableReservation.status == ReservationStatus.completed, 1),
                        else_=0,
                    )
                ).label("completed_reservations"),
                func.sum(
                    case(
                        (TableReservation.status == ReservationStatus.cancelled, 1),
                        else_=0,
                    )
                ).label("cancelled_reservations"),
                func.sum(
                    case(
                        (TableReservation.status == ReservationStatus.expired, 1),
                        else_=0,
                    )
                ).label("expired_reservations"),
                func.sum(
                    case(
                        (TableReservation.status == ReservationStatus.rejected, 1),
                        else_=0,
                    )
                ).label("rejected_reservations"),
                func.avg(TableReservation.guests_count).label("average_guests"),
            )
            .filter(
                TableReservation.created_at >= from_date,
                TableReservation.created_at <= end_of_to_date,
            )
            .first()
        )

        total = summary.total_reservations or 0
        completed = summary.completed_reservations or 0
        cancelled = summary.cancelled_reservations or 0

        completed_percentage = (
            round((completed / total) * 100)
            if total
            else 0
        )

        cancelled_percentage = (
            round((cancelled / total) * 100)
            if total
            else 0
        )

        largest_reservation = (
            db.query(TableReservation)
            .filter(
                TableReservation.created_at >= from_date,
                TableReservation.created_at <= end_of_to_date,
            )
            .order_by(
                TableReservation.guests_count.desc(),
                TableReservation.created_at.asc(),
            )
            .first()
        )

        smallest_reservation = (
            db.query(TableReservation)
            .filter(
                TableReservation.created_at >= from_date,
                TableReservation.created_at <= end_of_to_date,
            )
            .order_by(
                TableReservation.guests_count.asc(),
                TableReservation.created_at.asc(),
            )
            .first()
        )

        return response_handler(
            status=True,
            message="Get table reservation KPI report successful",
            data={
                "total_reservations": total,

                "completed_reservations": completed,
                "cancelled_reservations": cancelled,
                "expired_reservations": summary.expired_reservations or 0,
                "rejected_reservations": summary.rejected_reservations or 0,

                "completed_percentage": completed_percentage,
                "cancelled_percentage": cancelled_percentage,

                "average_guests": round(summary.average_guests or 0),

                "largest_reservation": (
                    {
                        "id": largest_reservation.id,
                        "table_number": largest_reservation.table_number,
                        "user_name": largest_reservation.user_name,
                        "guests_count": largest_reservation.guests_count,
                    }
                    if largest_reservation
                    else None
                ),

                "smallest_reservation": (
                    {
                        "id": smallest_reservation.id,
                        "table_number": smallest_reservation.table_number,
                        "user_name": smallest_reservation.user_name,
                        "guests_count": smallest_reservation.guests_count,
                    }
                    if smallest_reservation
                    else None
                ),
            },
            status_code=200,
        )
    except HTTPException as http_error:
        raise http_error
    except Exception:
        raise HTTPException(status_code=500, detail="Get table reservation KPI report failed")

