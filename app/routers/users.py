from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.schemas.user import RegisterUser, LoginUser, ChangeRole
from app.schemas.device_tracking import DeviceData
from app.db.session import get_db
from app.models.user import User
from app.models.device_tracking import DeviceTracking
from app.services.tokens import create_access_token, create_refresh_token
from app.utils.hashing import hash_password, verify_password, hash_token
from app.middleware.exception_handler import response_handler
from app.services.jwt_bearer import JWTBearer

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
            password = hash_password(user_data.password)
        )
        db.add(new_user)
        db.flush()
        db.refresh(new_user)

        access_token = create_access_token(new_user)
        refresh_token = create_refresh_token(new_user)

        # ----- Device Tracking -----
        user_agent = request.headers.get("User-Agent")
        ip_address = request.client.host

        new_device = DeviceTracking(
            user_id = new_user.id, 
            device_id = device_data.device_id,
            user_agent = user_agent,
            ip_address = ip_address,
            refresh_token = hash_token(refresh_token)
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
        
        access_token = create_access_token(db_user)
        refresh_token = create_refresh_token(db_user)

        # ----- Device Tracking -----
        user_agent = request.headers.get("User-Agent")
        ip_address = request.client.host
        
        db_device = db.query(DeviceTracking).filter(
            DeviceTracking.user_id == db_user.id,
            DeviceTracking.device_id == device_data.device_id,
        ).first()

        if db_device:
            db_device.user_agent = user_agent
            db_device.ip_address = ip_address
            db_device.refresh_token = hash_token(refresh_token)
            db_device.last_login_at = datetime.now(timezone.utc)
        else:
            new_device = DeviceTracking(
                user_id = db_user.id,
                device_id = device_data.device_id,
                user_agent = user_agent,
                ip_address = ip_address, 
                refresh_token = hash_token(refresh_token)
            )
            db.add(new_device)

        db.commit()

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


@router.get("/me")
def get_me(payload = Depends(JWTBearer()), db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == payload["sub"]).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return response_handler(
        status=True,
        message="User found",
        data={
            "id": db_user.id,
            "name": db_user.name,
            "phone": db_user.phone,
            "role": db_user.role,
            "created_at": db_user.created_at,
            "devices": [
                {
                    "id": device.id,
                    "device_id": device.device_id,
                    "ip_address": device.ip_address,
                    "user_agent": device.user_agent,
                    "last_login_at": device.last_login_at
                }
                for device in db_user.devices
            ]
        },
        status_code=200
    )


@router.get("/users")
def get_users(payload = Depends(JWTBearer()), db: Session = Depends(get_db)):
    
    if payload["role"] != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    db_users = db.query(User).filter(User.id != payload["sub"]).all()

    return response_handler(
        status=True,
        message="All users fetched",
        data=[
            {
                "id": user.id,
                "name": user.name,
                "phone": user.phone,
                "role": user.role,
                "created_at": user.created_at,
                "devices": [
                    {
                        "id": device.id,
                        "device_id": device.device_id,
                        "ip_address": device.ip_address,
                        "user_agent": device.user_agent,
                        "last_login_at": device.last_login_at
                    }
                    for device in user.devices
                ]
            }
            for user in db_users
        ],
        status_code=200
    )


@router.patch("/change-role")
def change_role(data: ChangeRole, payload = Depends(JWTBearer()), db: Session = Depends(get_db)):
    
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

    db.commit()
    db.refresh(db_user)

    return response_handler(
        status=True,
        message=f"User role updated to {data.role.value}",
        data={
            "id": db_user.id,
            "name": db_user.name,
            "phone": db_user.phone,
            "role": db_user.role,
            "created_at": db_user.created_at
        },
        status_code=200
    )


@router.delete("/delete/{user_id}")
def delete_user(user_id: str, payload = Depends(JWTBearer()), db: Session = Depends(get_db)):

    if payload["role"] != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    db_user = db.query(User).filter(User.id == user_id).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(db_user)
    db.commit()

    return response_handler(
        status=True,
        message="User deleted successfully",
        data=None,
        status_code=200
    )


@router.delete("/logout/{device_id}")
def refresh_token(device_id: str, payload = Depends(JWTBearer()), db: Session = Depends(get_db)):
    
    db_device = db.query(DeviceTracking).filter(DeviceTracking.device_id == device_id).first()

    if not db_device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    if payload["role"] != "admin" and payload["sub"] != db_device.user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    db.delete(db_device)
    db.commit()

    return response_handler(
        status=True,
        message="Logged out successfully",
        data=None,
        status_code=200
    )

