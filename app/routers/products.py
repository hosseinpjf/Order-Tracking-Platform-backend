from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import math
from app.db.session import get_db
from app.services.jwt_bearer import get_payload
from app.schemas.product import CreateProduct, UpdateProduct
from app.models.product import Product
from app.middleware.exception_handler import response_handler

router = APIRouter(prefix="/product", tags=["Product"])

@router.post("/create")
def create_product(data: CreateProduct, payload = Depends(get_payload), db: Session = Depends(get_db)):
    try:
        if payload["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

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
            data={new_product},
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
            raise HTTPException(status_code=404, detail="Products not found")
        
        return response_handler(
            status=True,
            message="All products fetched",
            data={
                "products": [
                    {product}
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


@router.get("/get/{product_id}")
def get_product(product_id: str, db: Session = Depends(get_db)):
    try:
        db_product = db.query(Product).filter(Product.id == product_id).first()

        if not db_product:
            raise HTTPException(status_code=404, detail="Product not found")
            
        return response_handler(
            status=True,
            message="Product found",
            data={db_product},
            status_code=200
        )
    except HTTPException as http_error:
        db.rollback()
        raise http_error
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Registration failed")


@router.patch("/update/{product_id}")
def update_product(product_id: str, data: UpdateProduct, payload = Depends(get_payload), db: Session = Depends(get_db)):
    try:
        if payload["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        db_product = db.query(Product).filter(Product.id == product_id).first()

        if not db_product:
            raise HTTPException(status_code=404, detail="Product not found")

        update_data = data.model_dump(
            exclude_unset=True,
            exclude_none=True
        )

        for key, value in update_data.items():
            if key == "tags":
                value = [tag.value for tag in value]
            setattr(db_product, key, value)

        db.commit()
        db.refresh(db_product)

        return response_handler(
            status=True,
            message="Data update completed successfully",
            data={db_product},
            status_code=200
        )
    except HTTPException as http_error:
        db.rollback()
        raise http_error
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Registration failed")

@router.delete("/delete/{product_id}")
def delete_product(prdocut_id: str, payload = Depends(get_payload), db: Session = Depends(get_db)):
    try:
        if payload["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        db_product = db.query(Product).filter(Product.id == prdocut_id).first()

        if not db_product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        db.delete(db_product)
        db.commit()

        return response_handler(
            status=True,
            message="Product deleted successfully",
            data=None,
            status_code=200
        )
    except HTTPException as http_error:
        db.rollback()
        raise http_error
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Registration failed")
