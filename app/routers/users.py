from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.user import CreateUser
from app.db.session import get_db
from app.models.user import User
from app.services.tokens import create_access_token, create_refresh_token

router = APIRouter(prefix="/user", tags=["Users"])

@router.post("/register")
def create_user(data: CreateUser, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.phone == data.phone).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Phone already exists")
    
    new_user = User(name = data.name, phone = data.phone, password = data.password)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token = create_access_token(new_user)
    refresh_token = create_refresh_token(new_user)

    return {
        "status": True,
        "access_token": access_token,
        "refresh_token": refresh_token
    }
