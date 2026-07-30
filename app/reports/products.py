from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from app.db.session import get_db
from app.services.jwt_bearer import get_payload
from app.middleware.exception_handler import response_handler
from app.models.product import Product, ProductChartType
from app.utils.product_charts import get_best_selling_products_chart, get_highest_revenue_products_chart, get_price_distribution_chart, get_tags_distribution_chart


router = APIRouter(prefix="/reports", tags=["Reports"])


PRODUCT_CHART_HANDLERS = {
    ProductChartType.best_selling_products: get_best_selling_products_chart,
    ProductChartType.highest_revenue_products: get_highest_revenue_products_chart,
    ProductChartType.price_distribution: get_price_distribution_chart,
    ProductChartType.tags_distribution: get_tags_distribution_chart,
}


@router.get("/product/kpi")
def get_products_summary(payload = Depends(get_payload), db: Session = Depends(get_db)):
    try:
        if payload["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        summary = (
            db.query(
                func.count(Product.id).label("total_products"),
                func.sum(
                    case(
                        (Product.is_available == True, 1),
                        else_=0,
                    )
                ).label("available_products"),
                func.sum(
                    case(
                        (Product.is_available == False, 1),
                        else_=0,
                    )
                ).label("unavailable_products"),
                func.avg(Product.price).label("average_price"),
                func.avg(Product.prepare_time).label("average_prepare_time"),
                func.avg(Product.discount_percent).label("average_discount_percent"),
                func.sum(
                    case(
                        (Product.discount_percent > 0, 1),
                        else_=0,
                    )
                ).label("discounted_products"),
            )
            .first()
        )

        query = db.query(Product)

        most_expensive_product = (
            query
            .order_by(
                Product.price.desc(),
                Product.created_at.asc(),
            )
            .first()
        )

        cheapest_product = (
            query
            .order_by(
                Product.price.asc(),
                Product.created_at.asc(),
            )
            .first()
        )

        most_discount_percent = (
            query
            .order_by(
                Product.discount_percent.desc(),
                Product.created_at.asc(),
            )
            .first()
        )

        return response_handler(
            status=True,
            message="Get product KPI report successful",
            data={
                "total_products": summary.total_products or 0,
                "available_products": summary.available_products or 0,
                "unavailable_products": summary.unavailable_products or 0,
                "average_price": int(summary.average_price or 0),
                "average_prepare_time": float(summary.average_prepare_time or 0),
                "average_discount_percent": float(summary.average_discount_percent or 0),
                "discounted_products": summary.discounted_products or 0,

                "most_expensive_product": (
                    {
                        "id": most_expensive_product.id,
                        "title": most_expensive_product.title,
                        "price": most_expensive_product.price,
                    }
                    if most_expensive_product
                    else None
                ),

                "cheapest_product": (
                    {
                        "id": cheapest_product.id,
                        "title": cheapest_product.title,
                        "price": cheapest_product.price,
                    }
                    if cheapest_product
                    else None
                ),

                "most_discount_percent": (
                    {
                        "id": most_discount_percent.id,
                        "title": most_discount_percent.title,
                        "discount_percent": most_discount_percent.discount_percent,
                    }
                    if most_discount_percent
                    else None
                ),
            },
            status_code=200,
        )
    except HTTPException as http_error:
        raise http_error
    except Exception:
        raise HTTPException(status_code=500, detail="Get product KPI report failed")


@router.get("/product/charts")
def get_product_chart(
    payload = Depends(get_payload),
    db: Session = Depends(get_db),
    chart_type: ProductChartType = Query(...),
    price_distribution_buckets: int = Query(5, ge=2, le=20),
):
    try:
        if payload["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        chart_handler = PRODUCT_CHART_HANDLERS.get(chart_type)

        if chart_handler is None:
            raise HTTPException(status_code=400, detail="Invalid chart type")

        if chart_type == ProductChartType.price_distribution:
            data = chart_handler(db, price_distribution_buckets)
        else:
            data = chart_handler(db)

        return response_handler(
            status=True,
            message="Get product chart report successful",
            data=data,
            status_code=200,
        )
    except HTTPException as http_error:
        raise http_error
    except Exception:
        raise HTTPException(status_code=500, detail="Get product chart report failed")

