from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import math
from app.db.session import get_db
from app.services.jwt_bearer import get_payload
from app.schemas.product import CreateProduct
from app.models.product import Product
from app.middleware.exception_handler import response_handler

router = APIRouter(prefix="/product", tags=["Product"])

@router.post("/create")
def create_product(data: CreateProduct, payload = Depends(get_payload), db: Session = Depends(get_db)):
    try:
        new_product = Product(
            title = data.title,
            description = data.description,
            price = data.price,
            discount_percent = data.discount_percent,
            category_id = data.category_id,
            images = [img.dict() for img in data.images],
            is_available = data.is_available,
            tags = [tag.value for tag in data.tags],
            prepare_time = data.prepare_time
        )

        db.add(new_product)
        db.commit()
        db.refresh(new_product)

        return response_handler(
            status=True,
            message="Product created successfully",
            data={
                "id": new_product.id,
                "title": new_product.title,
                "description": new_product.description,
                "price": new_product.price,
                "discount_percent": new_product.discount_percent,
                "category_id": new_product.category_id,
                "images": new_product.images,
                "is_available": new_product.is_available,
                "likes": new_product.likes,
                "tags": new_product.tags,
                "prepare_time": new_product.prepare_time,
                "created_at": new_product.created_at,
                "updated_at": new_product.updated_at
            },
            status_code=201
        )
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Registration failed")

@router.get("/get")
def get_products(db: Session = Depends(get_db), page: int = 1, limit: int = 20):
    try:
        db_products = db.query(Product).offset((page - 1) * limit).limit(limit).all()
        db_products_total = db.query(Product).count()

        if not db_products or not db_products_total:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return response_handler(
            status=True,
            message="All products fetched",
            data={
                "products": [
                    {
                        "id": product.id,
                        "title": product.title,
                        "description": product.description,
                        "price": product.price,
                        "discount_percent": product.discount_percent,
                        "category_id": product.category_id,
                        "images": product.images,
                        "is_available": product.is_available,
                        "likes": product.likes,
                        "tags": product.tags,
                        "prepare_time": product.prepare_time,
                        "created_at": product.created_at,
                        "updated_at": product.updated_at
                    }
                for product in db_products
                ],
                "page": page,
                "limit": limit,
                "total": db_products_total,
                "pages": math.ceil(db_products_total / limit)
            },
            status_code=200
        )


    except HTTPException as http_error:
        db.rollback()
        raise http_error
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Registration failed")

