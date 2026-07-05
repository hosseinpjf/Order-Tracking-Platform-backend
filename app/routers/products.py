from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import math
from app.db.session import get_db
from app.services.jwt_bearer import get_payload
from app.schemas.product import CreateProduct, UpdateProduct, OutProduct
from app.models.product import Product
from app.middleware.exception_handler import response_handler

router = APIRouter(prefix="/product", tags=["Product"])

@router.post("/")
def create_product(data: CreateProduct, payload = Depends(get_payload), db: Session = Depends(get_db)):
    try:
        if payload["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        new_product = Product()

        create_data = data.model_dump(
            exclude_none=True
        )
        for key, value in create_data.items():
            if key == "tags":
                value = [tag.value for tag in value]
            setattr(new_product, key, value)

        db.add(new_product)
        db.commit()
        db.refresh(new_product)

        return response_handler(
            status=True,
            message="Product created successfully",
            data=OutProduct.model_validate(new_product).model_dump(),
            status_code=201
        )
    except HTTPException as http_error:
        db.rollback()
        raise http_error
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Product create failed")


@router.get("/")
def get_products(db: Session = Depends(get_db), page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100)):
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
                    OutProduct.model_validate(product).model_dump()
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
        raise http_error
    except Exception:
        raise HTTPException(status_code=500, detail="Products get failed")


@router.get("/{product_id}")
def get_product(product_id: str, db: Session = Depends(get_db)):
    try:
        db_product = db.query(Product).filter(Product.id == product_id).first()

        if not db_product:
            raise HTTPException(status_code=404, detail="Product not found")
            
        return response_handler(
            status=True,
            message="Product found",
            data=OutProduct.model_validate(db_product).model_dump(),
            status_code=200
        )
    except HTTPException as http_error:
        raise http_error
    except Exception:
        raise HTTPException(status_code=500, detail="Product get failed")


@router.patch("/{product_id}")
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
            data=OutProduct.model_validate(db_product).model_dump(),
            status_code=200
        )
    except HTTPException as http_error:
        db.rollback()
        raise http_error
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Product update failed")


@router.delete("/{product_id}")
def delete_product(product_id: str, payload = Depends(get_payload), db: Session = Depends(get_db)):
    try:
        if payload["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        db_product = db.query(Product).filter(Product.id == product_id).first()

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
        raise HTTPException(status_code=500, detail="Product delete failed")

