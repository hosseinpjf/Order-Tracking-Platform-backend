from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timezone
import math
from app.schemas.table import CreateTable, OutTable
from app.schemas.device_tracking import DeviceData
from app.db.session import get_db
from app.models.table import Table
from app.models.device_tracking import DeviceTracking
from app.services.tokens import create_access_token, create_refresh_token, verify_token
from app.utils.hashing import hash_password, verify_password, hash_token
from app.middleware.exception_handler import response_handler
from app.services.jwt_bearer import get_payload

router = APIRouter(prefix="/table", tags=["Table"])

@router.post("/")
def create_table(data: CreateTable, payload = Depends(get_payload), db: Session = Depends(get_db)):
    try:
        if payload["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")
        
        new_table = Table()

        create_data = data.model_dump(
            exclude_none=True
        )
        for key, value in create_data.items():
            if key == "tags":
                value = [tag.value for tag in value]
            setattr(new_table, key, value)

        db.add(new_table)
        db.commit()
        db.refresh(new_table)

        return response_handler(
            status=True,
            message="Table created successfully",
            data=OutTable.model_validate(new_table).model_dump(),
            status_code=201
        )
    except HTTPException as http_error:
        db.rollback()
        raise http_error
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Table create failed")
