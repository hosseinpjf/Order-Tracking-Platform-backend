from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timezone
import math
from app.schemas.user import RegisterUser, LoginUser, ChangeRole, RefreshToken, OutUser, OutFullUser
from app.schemas.device_tracking import DeviceData
from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.device_tracking import DeviceTracking
from app.services.tokens import create_access_token, create_refresh_token, verify_token
from app.utils.hashing import hash_password, verify_password, hash_token
from app.middleware.exception_handler import response_handler
from app.services.jwt_bearer import get_payload

router = APIRouter(prefix="/user", tags=["Users"])

@router.post("/register")
def register_user(request: Request, user_data: RegisterUser, device_data: DeviceData, db: Session = Depends(get_db)):
    try:
        db_user = db.query(User).filter(User.phone == user_data.phone).first()
        if db_user:
            raise HTTPException(status_code=409, detail="Phone already exists")
        
        new_user = User(
            name = user_data.name, 
            phone = user_data.phone, 
            password = hash_password(user_data.password),
            address = user_data.address
        )
        db.add(new_user)
        db.flush()
        db.refresh(new_user)

        access_token = create_access_token({
            "sub": new_user.id,
            "role": new_user.role.value,
            "access_version": 1,
            "device_id": device_data.device_id
        })
        refresh_token = create_refresh_token({
            "sub": new_user.id,
            "role": new_user.role.value
        })

        # ----- Device Tracking -----
        user_agent = request.headers.get("User-Agent")
        ip_address = request.client.host

        login_time = datetime.now(timezone.utc)

        new_device = DeviceTracking(
            user_id = new_user.id, 

            device_id = device_data.device_id,
            user_agent = user_agent,
            ip_address = ip_address,

            refresh_token = hash_token(refresh_token),
            access_version = 1,

            first_login_at = login_time,
            last_login_at = login_time
        )
        db.add(new_device)

        db.commit()

        return response_handler(
            status=True,
            message="Register successful",
            data={
                "access_token": access_token,
                "refresh_token": refresh_token
            },
            status_code=201
        )
    except HTTPException as http_error:
        db.rollback()
        raise http_error
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Registration failed")


@router.post("/login")
def login_user(request: Request, user_data: LoginUser, device_data: DeviceData, db: Session = Depends(get_db)):
    try:
        db_user = db.query(User).filter(User.phone == user_data.phone).first()

        if not db_user:
            raise HTTPException(status_code=401, detail="Invalid phone or password")
        
        if not verify_password(user_data.password, db_user.password):
            raise HTTPException(status_code=401, detail="Invalid phone or password")

        refresh_token = create_refresh_token({
            "sub": db_user.id, 
            "role": db_user.role.value
        })

        # ----- Device Tracking -----
        user_agent = request.headers.get("User-Agent")
        ip_address = request.client.host
        
        db_device = db.query(DeviceTracking).filter(
            DeviceTracking.user_id == db_user.id,
            DeviceTracking.device_id == device_data.device_id,
        ).first()

        access_version = None
        login_time = datetime.now(timezone.utc)

        if db_device:
            # Prev Device
            db_device.user_agent = user_agent
            db_device.ip_address = ip_address

            db_device.access_version += 1
            db_device.refresh_token = hash_token(refresh_token)

            db_device.last_login_at = login_time

            access_version = db_device.access_version
        else:
            # New Device
            access_version = 1

            new_device = DeviceTracking(
                user_id = db_user.id,

                device_id = device_data.device_id,
                user_agent = user_agent,
                ip_address = ip_address,

                refresh_token = hash_token(refresh_token),
                access_version = 1,

                first_login_at = login_time,
                last_login_at = login_time
            )
            db.add(new_device)

        db.commit()

        access_token = create_access_token({
            "sub": db_user.id, 
            "role": db_user.role.value, 
            "access_version": access_version, 
            "device_id": device_data.device_id
        })

        return response_handler(
            status=True,
            message="Login successful",
            data={
                "access_token": access_token,
                "refresh_token": refresh_token
            },
            status_code=200
        )
    except HTTPException as http_error:
        db.rollback()
        raise http_error
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Login failed")


@router.post("/refresh")
def refresh_token(data: RefreshToken, db: Session = Depends(get_db)):
    try:
        payload = verify_token(data.refresh_token)

        if payload is None or payload["type"] != "refresh":
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

        db_device = db.query(DeviceTracking).filter(
            DeviceTracking.user_id == payload["sub"],
            DeviceTracking.refresh_token == hash_token(data.refresh_token)
        ).first()

        if not db_device:
            raise HTTPException(status_code=401, detail="Session not found. Please log in again")
        
        db_device.access_version += 1
        db.commit()

        new_access_token = create_access_token({
            "sub": payload["sub"],
            "role": payload["role"],
            "access_version": db_device.access_version,
            "device_id": db_device.device_id,
        })

        return response_handler(
            status=True,
            message="Access token refreshed",
            data={"access_token": new_access_token},
            status_code=200
        )
    except HTTPException as http_error:
        db.rollback()
        raise http_error
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Refresh failed")


@router.get("/me")
def get_me(payload = Depends(get_payload), db: Session = Depends(get_db)):
    try:
        db_user = db.query(User).filter(User.id == payload["sub"]).first()

        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return response_handler(
            status=True,
            message="User found",
            data=OutFullUser.model_validate(db_user).model_dump(),
            status_code=200
        )
    except HTTPException as http_error:
        raise http_error
    except Exception:
        raise HTTPException(status_code=500, detail="Me get failed")


@router.get("/")
def get_users(
        payload = Depends(get_payload), 
        db: Session = Depends(get_db), 
        page: int = Query(1, ge=1), 
        limit: int = Query(10, ge=1, le=100),
        role: UserRole | None = Query(None),
        q: str | None = Query(None, min_length=1, max_length=100),
    ):
    try:
        if payload["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")
        
        db_users = []
        query = db.query(User).order_by(User.created_at.desc())

        if role:
            query = query.filter(User.role == role)
        if q:
            query = query.filter(or_(User.name.ilike(f"%{q}%"), User.phone.ilike(f"%{q}%")))

        db_users_total = query.count()
        db_users = query.offset((page - 1) * limit).limit(limit).all()

        return response_handler(
            status=True,
            message="All users fetched",
            data={
                "users": [
                    OutUser.model_validate(user).model_dump()
                    for user in db_users
                ],
                "page": page,
                "limit": limit,
                "total": db_users_total,
                "pages": math.ceil(db_users_total / limit)
            },
            status_code=200
        )
    except HTTPException as http_error:
        raise http_error
    except Exception:
        raise HTTPException(status_code=500, detail="Users get failed")


@router.get("/{user_id}")
def get_user(user_id: str, payload = Depends(get_payload), db: Session = Depends(get_db)):
    try:
        if payload["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")
        
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")

        return response_handler(
            status=True,
            message="User found",
            data=OutFullUser.model_validate(db_user).model_dump(),
            status_code=200
        )
    except HTTPException as http_error:
        raise http_error
    except Exception:
        raise HTTPException(status_code=500, detail="Users get failed")


@router.patch("/change-role")
def change_role(data: ChangeRole, payload = Depends(get_payload), db: Session = Depends(get_db)):
    try:
        if payload["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")
        
        if payload["sub"] == data.user_id:
            raise HTTPException(status_code=400, detail="You cannot change your own role")
        
        db_user = db.query(User).filter(User.id == data.user_id).first()

        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")

        if db_user.role.value == data.role.value:
            raise HTTPException(status_code=400, detail="User already has this role")

        db_user.role = data.role

        db.flush()
        db.refresh(db_user)

        db_devices = db.query(DeviceTracking).filter(DeviceTracking.user_id == db_user.id).all()
        for device in db_devices:
            device.refresh_token = None
            device.access_version += 1
            device.last_logout_at = datetime.now(timezone.utc)

        db.commit()

        return response_handler(
            status=True,
            message=f"User role updated to {data.role.value}",
            data=OutUser.model_validate(db_user).model_dump(),
            status_code=200
        )
    except HTTPException as http_error:
        db.rollback()
        raise http_error
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Change Role failed")


@router.delete("/delete/{user_id}")
def delete_user(user_id: str, payload = Depends(get_payload), db: Session = Depends(get_db)):
    try:
        db_user = db.query(User).filter(User.id == user_id).first()

        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if payload["role"] != "admin" and payload["sub"] != db_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        db.delete(db_user)
        db.commit()

        return response_handler(
            status=True,
            message="User deleted successfully",
            data=None,
            status_code=200
        )
    except HTTPException as http_error:
        db.rollback()
        raise http_error
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="User Delete failed")


@router.delete("/logout/{device_id}")
def logout_user(device_id: str, payload = Depends(get_payload), db: Session = Depends(get_db)):
    try:
        db_device = db.query(DeviceTracking).filter(
            DeviceTracking.user_id == payload["sub"],
            DeviceTracking.device_id == device_id
        ).first()

        if not db_device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        if payload["role"] != "admin" and payload["sub"] != db_device.user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        db_device.refresh_token = None
        db_device.access_version += 1
        db_device.last_logout_at = datetime.now(timezone.utc)
        db.commit()

        return response_handler(
            status=True,
            message="Logged out successfully",
            data=None,
            status_code=200
        )
    except HTTPException as http_error:
        db.rollback()
        raise http_error
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Logout failed")

