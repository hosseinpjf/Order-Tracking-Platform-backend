from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, case
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.jwt_bearer import get_payload
from app.middleware.exception_handler import response_handler
from app.models.category import Category
from app.models.product import Product


router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/category/kpi")
def get_categories_summary(payload=Depends(get_payload), db: Session = Depends(get_db)):
    try:
        if payload["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        category_stats = (
            db.query(Category.id, func.count(Product.id).label("products_count"))
            .outerjoin(Product, Product.category_id == Category.id)
            .group_by(Category.id)
            .subquery()
        )

        summary = (
            db.query(
                func.count(category_stats.c.id).label("total_categories"),
                func.sum(
                    case(
                        (category_stats.c.products_count > 0, 1),
                        else_=0
                    )
                ).label("categories_with_products"),
                func.sum(
                    case(
                        (category_stats.c.products_count == 0, 1),
                        else_=0
                    )
                ).label("empty_categories"),
                func.avg(category_stats.c.products_count).label("average_products"),
                func.max(category_stats.c.products_count).label("max_products"),
                func.min(category_stats.c.products_count).label("min_products"),
            )
            .first()
        )

        newest_category = db.query(Category).order_by(Category.created_at.desc()).first()
        oldest_category = db.query(Category).order_by(Category.created_at.asc()).first()

        return response_handler(
            status=True,
            message="Get category KPI report successful",
            data={
                "total_categories": summary.total_categories or 0,
                "categories_with_products": summary.categories_with_products or 0,
                "empty_categories": summary.empty_categories or 0,
                "average_products": round(summary.average_products or 0, 2),
                "max_products": summary.max_products or 0,
                "min_products": summary.min_products or 0,

                "newest_category": (
                    {
                        "id": newest_category.id,
                        "title": newest_category.title,
                        "created_at": newest_category.created_at
                    }
                    if newest_category
                    else None
                ),

                "oldest_category": (
                    {
                        "id": oldest_category.id,
                        "title": oldest_category.title,
                        "created_at": oldest_category.created_at
                    }
                    if oldest_category
                    else None
                )
            },
            status_code=200,
        )
    except HTTPException as http_error:
        raise http_error
    except Exception:
        raise HTTPException(status_code=500, detail="Get category KPI report failed")


@router.get("/category/charts")
def get_category_chart(payload=Depends(get_payload), db: Session = Depends(get_db)):
    try:
        if payload["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        categories = (
            db.query(
                Category.id,
                Category.title,
                func.count(Product.id).label("products_count")
            )
            .outerjoin(Product, Product.category_id == Category.id)
            .group_by(Category.id, Category.title)
            .order_by(func.count(Product.id).desc(), Category.title.asc())
            .all()
        )

        return response_handler(
            status=True,
            message="Get category chart report successful",
            data=[
                {
                    "id": category.id,
                    "title": category.title,
                    "products_count": category.products_count
                }
                for category in categories
            ],
            status_code=200,
        )
    except HTTPException as http_error:
        raise http_error
    except Exception:
        raise HTTPException(status_code=500, detail="Get category chart report failed")

