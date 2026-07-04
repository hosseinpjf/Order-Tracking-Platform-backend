from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from app.config.settings import settings

def create_access_token(data: dict):
    expire = datetime.now(timezone.utc) + timedelta(minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": data["sub"],
        "role": data["role"],
        "access_version": data["access_version"],
        "device_id": data["device_id"],
        "type": "access",
        "exp": expire
    }
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    
def create_refresh_token(data: dict):
    expire = datetime.now(timezone.utc) + timedelta(days = settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "sub": data["sub"],
        "role": data["role"],
        "type": "refresh",
        "exp": expire
    }
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def verify_token(token: str):
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None