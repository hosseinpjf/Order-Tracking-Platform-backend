from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
import math
import json
from app.db.session import get_db
from app.services.jwt_bearer import get_payload
from app.schemas.product import CreateProduct, UpdateProduct, OutProduct
from app.models.product import Product, ProductTags, ProductSort
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
def get_products(
        db: Session = Depends(get_db), 
        page: int = Query(1, ge=1), 
        limit: int = Query(20, ge=1, le=100),
        q: str | None = Query(None, min_length=1, max_length=100),
        category_id: str | None = Query(None, min_length=32, max_length=32),
        tag: ProductTags | None = None,
        discount: bool | None = None,
        available: bool | None = None,
        sort: ProductSort | None = None,
    ):
    try:
        db_products = []
        query = db.query(Product)

        if q:
            query = query.filter(Product.title.ilike(f"%{q}%"))
        if category_id:
            query = query.filter(Product.category_id == category_id)
        if tag:
            query = query.filter(func.json_extract(Product.tags, '$').like(f'%"{tag.value}"%'))
            # query = query.filter(Product.tags.contains([tag.value]))
        if discount is not None:
            query = query.filter(Product.discount_percent > 0 if discount else Product.discount_percent == 0)
        if available is not None:
            query = query.filter(Product.is_available == available)

        if sort == ProductSort.newest:
            query = query.order_by(Product.created_at.desc())
        elif sort == ProductSort.popular:
            query = query.order_by(Product.likes.desc())
        elif sort == ProductSort.price_desc:
            query = query.order_by(Product.price.desc())
        elif sort == ProductSort.price_asc:
            query = query.order_by(Product.price.asc())
        elif sort == ProductSort.discount_desc:
            query = query.order_by(Product.discount_percent.desc())
        elif sort == ProductSort.prepare_time_asc:
            query = query.order_by(Product.prepare_time.asc())

        db_products = query.offset((page - 1) * limit).limit(limit).all()
        db_products_total = query.count()
        
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


@router.patch('/like/{product_id}')
def update_likes_product(product_id: str, payload = Depends(get_payload), db: Session = Depends(get_db)):
    try:
        db_product = db.query(Product).filter(Product.id == product_id).first()

        if not db_product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        if payload["sub"] in db_product.likes:
            db_product.likes.remove(payload["sub"])
        else:
            db_product.likes.append(payload["sub"])
        
        db.commit()
        db.refresh(db_product)

        return response_handler(
            status=True,
            message="Like successfully recorded",
            data=OutProduct.model_validate(db_product).model_dump(),
            status_code=200
        )
    except HTTPException as http_error:
        db.rollback()
        raise http_error
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Product like failed")