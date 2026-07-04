from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.db.session import get_db
from app.models.device_tracking import DeviceTracking
from app.middleware.exception_handler import response_handler
from app.services.jwt_bearer import get_payload

router = APIRouter(prefix="/device", tags=["Device"])

@router.delete("/revoke/{id}")
def revoke_device(id: str, payload = Depends(get_payload), db: Session = Depends(get_db)):

    db_device = db.query(DeviceTracking).filter(DeviceTracking.id == id).first()

    if not db_device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    if payload["role"] != "admin" and payload["sub"] != db_device.user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    db_device.refresh_token = None
    db_device.access_version += 1
    db_device.logout_at = datetime.now(timezone.utc)
    db.commit()
    
    return response_handler(
        status=True,
        message="Device revoked successfully",
        data=None,
        status_code=200
    )