from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.db.session import get_db
from app.services.jwt_bearer import get_payload
from app.schemas.category import CreateCategory, OutCategory, UpdateCategory
from app.models.category import Category
from app.middleware.exception_handler import response_handler
from app.utils.delete_file import delete_files


router = APIRouter(prefix="/category", tags=["Category"])

@router.post("/")
def create_category(data: CreateCategory, payload = Depends(get_payload), db: Session = Depends(get_db)):
    try:
        if payload["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        new_category = Category()

        create_data = data.model_dump(
            exclude_unset=True,
            exclude_none=True
        )
        for key, value in create_data.items():
            setattr(new_category, key, value)

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
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Category title already exists")
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


@router.patch("/{category_id}")
def update_category(category_id: str, data: UpdateCategory, payload = Depends(get_payload), db: Session = Depends(get_db)):
    try:
        if payload["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        db_category = db.query(Category).filter(Category.id == category_id).first()
        if not db_category:
            raise HTTPException(status_code=404, detail="Category not found")

        old_images = []
        new_images = []

        update_data = data.model_dump(
            exclude_unset=True,
            exclude_none=True
        )

        if "images" in update_data:
            new_images = [img.url for img in data.images]
            old_images = [img["url"] for img in (db_category.images or [])]

        for key, value in update_data.items():
            setattr(db_category, key, value)

        db.commit()
        db.refresh(db_category)

        delete_images = set(old_images) - set(new_images)
        if delete_images:
            delete_files(delete_images)

        return response_handler(
            status=True,
            message="Category updated successfully",
            data=OutCategory.model_validate(db_category).model_dump(),
            status_code=200
        )
    except HTTPException as http_error:
        db.rollback()
        raise http_error
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Category title already exists")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Category update failed")


@router.delete("/{category_id}")
def delete_category(category_id: str, payload = Depends(get_payload), db: Session = Depends(get_db)):
    try:
        if payload["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        db_category = db.query(Category).filter(Category.id == category_id).first()
        if not db_category:
            raise HTTPException(status_code=404, detail="Category not found")
        
        images = [img["url"] for img in (db_category.images or [])]

        db.delete(db_category)
        db.commit()

        if images:
            delete_files(images)

        return response_handler(
            status=True,
            message="Category deleted successfully",
            data=None,
            status_code=200
        )
    except HTTPException as http_error:
        db.rollback()
        raise http_error
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Category delete failed")

