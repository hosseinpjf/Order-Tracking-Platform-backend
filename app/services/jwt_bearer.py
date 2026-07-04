from fastapi.security import HTTPBearer
from fastapi import Request, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.device_tracking import DeviceTracking
from app.db.session import get_db
from app.services.tokens import verify_token

class JWTBearer(HTTPBearer):
    async def __call__(self, request: Request):
        auth = await super().__call__(request)
        token = auth.credentials

        payload = verify_token(token)
        if payload is None:
            raise HTTPException(status_code=403, detail="Invalid or expired token")
        
        return payload


def get_payload(payload = Depends(JWTBearer()), db: Session = Depends(get_db)):
    
        db_device = db.query(DeviceTracking).filter(
            DeviceTracking.device_id == payload["device_id"]
        ).first()

        if not db_device or db_device.access_version != payload["access_version"]:
            raise HTTPException(status_code=403, detail="Invalid or expired token")
        
        return payload