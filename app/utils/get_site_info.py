from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import time, datetime, timezone
from app.models.site_info import SiteInfo

def get_site_info(db: Session) -> SiteInfo | None:
    try:
        db_site_info = db.query(SiteInfo).first()
        if not db_site_info:
            raise HTTPException(status_code=404, detail="Site info not found")
        
        return db_site_info

    except HTTPException as http_error:
        raise http_error
    except Exception:
        raise HTTPException(status_code=500, detail="Reservation fetch failed")


def get_working_hours(db: Session):
    try:
        db_site_info = get_site_info(db)

        working_hours = db_site_info.working_hours
        if not working_hours: 
            raise HTTPException(status_code=404, detail="Working hours not found")

        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        today = days[datetime.now(timezone.utc).weekday()]

        workday = next((item for item in working_hours if item.get("day") == today), None)
        if workday is None:
            raise HTTPException(status_code=400, detail="Working hours not configured for today")

        return {
            "open_time": time.fromisoformat(workday.get("open_time")),
            "close_time": time.fromisoformat(workday.get("close_time")),
            "is_closed": workday.get("is_closed", False),
        }
    except HTTPException as http_error:
        raise http_error
    except Exception:
        raise HTTPException(status_code=500, detail="Reservation fetch failed")
