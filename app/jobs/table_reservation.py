from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.table_reservation import TableReservation, ReservationStatus


def auto_update_reservations(db: Session, db_settings):
    try:
        now = datetime.now(timezone.utc)

        updated = False

        # expire
        if db_settings["auto_expire_reservations"]:
            expired_reservations = db.query(TableReservation).with_for_update(skip_locked=True).filter(
                TableReservation.status.in_([ReservationStatus.pending, ReservationStatus.confirmed]),
                TableReservation.end_time < now
            ).all()

            for r in expired_reservations:
                r.status = ReservationStatus.expired
                updated = True

        # complete
        if db_settings["auto_complete_reservations"]:
            completed_reservations = db.query(TableReservation).with_for_update(skip_locked=True).filter(
                TableReservation.status == ReservationStatus.seated,
                TableReservation.end_time < now
            ).all()

            for r in completed_reservations:
                r.status = ReservationStatus.completed
                updated = True

        if updated:
            db.commit()

    except Exception:
        db.rollback()
        raise
