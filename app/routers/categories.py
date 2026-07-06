from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.jwt_bearer import get_payload
from app.schemas.category import CreateCategory, OutCategory
from app.models.category import Category
from app.middleware.exception_handler import response_handler


router = APIRouter(prefix="/category", tags=["Category"])

@router.post("/")
def create_category(data: CreateCategory, payload = Depends(get_payload), db: Session = Depends(get_db)):
    try:
        if payload["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")
        
        exists = db.query(Category).filter(Category.title == data.title).first()
        if exists:
            raise HTTPException(status_code=400, detail="Category already exists")

        new_category = Category(
            title = data.title
        )

        db.add(new_category)
        db.commit()
        db.refresh(new_category)

        return response_handler(
            status=True,
            message="Category successfully created",
            data=OutCategory.model_validate(new_category).model_dump(),
            status_code=201
        )
    except HTTPException as http_error:
        db.rollback()
        raise http_error
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Category create failed")


@router.get("/")
def get_categories(db: Session = Depends(get_db)):
    try:
        db_categories = db.query(Category).order_by(Category.created_at.desc()).all()
        
        return response_handler(
            status=True,
            message="All category fetched",
            data={
                "categories": [
                    OutCategory.model_validate(category).model_dump()
                    for category in db_categories
                ]
            },
            status_code=200
        )
    except HTTPException as http_error:
        raise http_error
    except Exception:
        raise HTTPException(status_code=500, detail="Category get failed")


@router.put("/{category_id}")
def update_category(category_id: str, data: CreateCategory, payload = Depends(get_payload), db: Session = Depends(get_db)):
    try:
        if payload["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        db_category = db.query(Category).filter(Category.id == category_id).first()

        if not db_category:
            raise HTTPException(status_code=404, detail="Category not found")

        db_category.title = data.title

        db.commit()
        db.refresh(db_category)

        return response_handler(
            status=True,
            message="Category updated successfully",
            data=OutCategory.model_validate(db_category).model_dump(),
            status_code=200
        )
    except HTTPException as http_error:
        db.rollback()
        raise http_error
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Category update failed")
    

