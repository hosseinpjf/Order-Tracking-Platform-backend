from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.user import RegisterUser, LoginUser
from app.db.session import get_db
from app.models.user import User
from app.services.tokens import create_access_token, create_refresh_token
from app.utils.hashing import hash_password, verify_password
from app.middleware.exception_handler import response_handler
from app.services.jwt_bearer import JWTBearer

router = APIRouter(prefix="/user", tags=["Users"])

@router.post("/register")
def register_user(data: RegisterUser, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.phone == data.phone).first()
    if db_user:
        raise HTTPException(status_code=409, detail="Phone already exists")
    
    new_user = User(name = data.name, phone = data.phone, password = hash_password(data.password))

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token = create_access_token(new_user)
    refresh_token = create_refresh_token(new_user)

    return response_handler(
        status=True,
        message="Register successful",
        data={
            "access_token": access_token,
            "refresh_token": refresh_token
        },
        status_code=201
    )


@router.post("/login")
def login_user(data: LoginUser, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.phone == data.phone).first()

    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid phone or password")
    
    if not verify_password(data.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid phone or password")
    
    access_token = create_access_token(db_user)
    refresh_token = create_refresh_token(db_user)

    return response_handler(
        status=True,
        message="Login successful",
        data={
            "access_token": access_token,
            "refresh_token": refresh_token
        },
        status_code=200
    )


@router.get("/me")
def get_user(payload = Depends(JWTBearer()), db: Session = Depends(get_db)):
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
            "created_at": db_user.created_at
        },
        status_code=200
    )
