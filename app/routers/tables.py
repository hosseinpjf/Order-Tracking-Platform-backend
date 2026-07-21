from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from app.db.session import get_db
from app.services.jwt_bearer import get_payload, get_optional_payload
from app.middleware.exception_handler import response_handler
from app.utils.delete_file import delete_file
from app.models.table import Table, TableStatus, TableTags
from app.schemas.table import CreateTable, OutTable, UpdateTable
from app.schemas.shared_table import OutFullTable
from app.utils.get_site_info import get_settings


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
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Table number already exists")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Table create failed")


@router.get("/")
def get_tables(
        db: Session = Depends(get_db),
        payload = Depends(get_optional_payload),
        tag: TableTags | None = Query(None),
        status: TableStatus | None = Query(None)
    ):
    try:
        is_admin = bool(payload) and payload.get("role") == "admin"

        db_settings = get_settings(db, ["show_table_reservation"])
        if not db_settings["show_table_reservation"] and not is_admin:
            raise HTTPException(status_code=400, detail="Show table disabled")

        db_tables = []
        query = db.query(Table)
        
        if tag:
            query = query.filter(func.json_extract(Table.tags, '$').like(f'%"{tag.value}"%'))
        if status:
            query = query.filter(Table.status == status)
        
        db_tables_total = query.count()
        db_tables = query.all()

        return response_handler(
            status=True,
            message="Tables get successfully",
            data={
                "tables": [
                    OutTable.model_validate(table).model_dump()
                    for table in db_tables
                ], 
                "total": db_tables_total,
            },
            status_code=200
        )
    except HTTPException as http_error:
        raise http_error
    except Exception:
        raise HTTPException(status_code=500, detail="Table get failed")


@router.get("/{table_id}")
def get_reservation(table_id: str, payload = Depends(get_optional_payload), db: Session = Depends(get_db)):
    try:
        is_admin = bool(payload) and payload.get("role") == "admin"

        db_settings = get_settings(db, ["show_table_reservation"])
        if not db_settings["show_table_reservation"] and not is_admin:
            raise HTTPException(status_code=400, detail="Show table disabled")
        
        db_table = db.query(Table).filter(Table.id == table_id).first()
        if not db_table:
            raise HTTPException(status_code=404, detail="Table not found")

        return response_handler(
            status=True,
            message="Table found",
            data=OutFullTable.model_validate(db_table).model_dump(),
            status_code=200
        )
    except HTTPException as http_error:
        raise http_error
    except Exception:
        raise HTTPException(status_code=500, detail="Table fetch failed")


@router.patch("/{table_id}")
def update_table(table_id: str, data: UpdateTable, payload = Depends(get_payload), db: Session = Depends(get_db)):
    try:
        if payload["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        db_table = db.query(Table).filter(Table.id == table_id).first()
        if not db_table:
            raise HTTPException(status_code=404, detail="table not found")
        
        old_image = None

        update_data = data.model_dump(
            exclude_unset=True,
            exclude_none=True
        )

        if "image" in update_data and db_table.image and db_table.image != update_data["image"]:
            old_image = db_table.image

        for key, value in update_data.items():
            if key == "tags":
                value = [tag.value for tag in value]
            setattr(db_table, key, value)

        db.commit()
        db.refresh(db_table)
        
        if old_image:
            delete_file(old_image)

        return response_handler(
            status=True,
            message="Data update completed successfully",
            data=OutTable.model_validate(db_table).model_dump(),
            status_code=200
        )
    except HTTPException as http_error:
        db.rollback()
        raise http_error
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="table update failed")


@router.delete("/{table_id}")
def delete_table(table_id: str, payload = Depends(get_payload), db: Session = Depends(get_db)):
    try:
        if payload["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        db_table = db.query(Table).filter(Table.id == table_id).first()
        if not db_table:
            raise HTTPException(status_code=404, detail="table not found")
        
        image = db_table.image
        
        db.delete(db_table)
        db.commit()

        if image:
            delete_file(image)

        return response_handler(
            status=True,
            message="Table deleted successfully",
            data=None,
            status_code=200
        )
    except HTTPException as http_error:
        db.rollback()
        raise http_error
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="table delete failed")

