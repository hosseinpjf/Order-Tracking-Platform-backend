from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from datetime import datetime
from app.db.session import get_db
from app.services.jwt_bearer import get_payload
from app.middleware.exception_handler import response_handler
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.order_status_history import OrderStatusHistory

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/order/kpi")
def get_order_kpi(
    payload = Depends(get_payload),
    db: Session = Depends(get_db),
    from_date: datetime | None = Query(None),
    to_date: datetime | None = Query(None)
):
    try:
        if payload["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        orders_query = db.query(Order)

        if from_date:
            orders_query = orders_query.filter(Order.created_at >= from_date)
        if to_date:
            orders_query = orders_query.filter(Order.created_at <= to_date)

        orders_subquery = orders_query.subquery()

        order_summary = (
            db.query(
                func.count(orders_subquery.c.id).label("total_orders"),
                func.coalesce(
                    func.sum(
                        case(
                            (orders_subquery.c.status == OrderStatus.completed, orders_subquery.c.final_total_price),
                            else_=0
                        )
                    ), 0
                ).label("total_sales"),
                func.coalesce(
                    func.avg(
                        case(
                            (orders_subquery.c.status == OrderStatus.completed, orders_subquery.c.final_total_price),
                            else_=None
                        )
                    ), 0
                ).label("average_order_price"),
                func.coalesce(
                    func.max(
                        case(
                            (orders_subquery.c.status == OrderStatus.completed, orders_subquery.c.final_total_price),
                            else_=None
                        )
                    ), 0
                ).label("max_order_price"),
                func.coalesce(
                    func.min(
                        case(
                            (orders_subquery.c.status == OrderStatus.completed, orders_subquery.c.final_total_price),
                            else_=None
                        )
                    ), 0
                ).label("min_order_price"),
                func.coalesce(
                    func.avg(orders_subquery.c.items_count), 0
                ).label("average_items"),
                func.sum(
                    case(
                        (orders_subquery.c.status == OrderStatus.completed, 1),
                        else_=0
                    )
                ).label("completed_orders"),
                func.sum(
                    case(
                        (orders_subquery.c.status == OrderStatus.canceled, 1),
                        else_=0
                    )
                ).label("canceled_orders"),
            )
            .first()
        )

        cancel_percentage = 0
        if order_summary.total_orders:
            cancel_percentage = round(
                (order_summary.canceled_orders / order_summary.total_orders) * 100, 2
            )

        sold_products_query = (
            db.query(func.coalesce(func.sum(OrderItem.quantity), 0))
            .join(Order, Order.id == OrderItem.order_id)
            .filter(Order.status == OrderStatus.completed)
        )
        if from_date:
            sold_products_query = sold_products_query.filter(Order.created_at >= from_date)
        if to_date:
            sold_products_query = sold_products_query.filter(Order.created_at <= to_date)
        sold_products = sold_products_query.scalar()

        preparing_query = (
            db.query(
                func.coalesce(
                    func.avg(OrderStatusHistory.duration_seconds), 0
                )
            )
            .join(Order, Order.id == OrderStatusHistory.order_id)
            .filter(Order.status == OrderStatus.completed)
            .filter(OrderStatusHistory.status == OrderStatus.preparing)
            .filter(OrderStatusHistory.duration_seconds > 0)
        )
        if from_date:
            preparing_query = preparing_query.filter(Order.created_at >= from_date)
        if to_date:
            preparing_query = preparing_query.filter(Order.created_at <= to_date)
        average_prepare_time = preparing_query.scalar()

        return response_handler(
            status=True,
            message="Get order KPI report successful",
            data={
                "total_orders": order_summary.total_orders,                             # تعداد سفارش‌ها
                "total_sales": order_summary.total_sales,                               # مبلغ کل فروش
                "average_order_price": round(order_summary.average_order_price, 2),     # میانگین مبلغ سفارش
                "max_order_price": order_summary.max_order_price,                       # بیشترین مبلغ سفارش
                "min_order_price": order_summary.min_order_price,                       # کمترین مبلغ سفارش
                "average_items_per_order": round(order_summary.average_items or 0),     # میانگین آیتم هر سفارش
                "sold_products": sold_products,                                         # مجموع محصولات فروخته شده
                "cancel_percentage": cancel_percentage,                                 # درصد لغو سفارش
                "average_prepare_time_seconds": round(average_prepare_time, 2),         # میانگین زمان آماده سازی
                "completed_orders": order_summary.completed_orders,                     # تعداد سفارش تکمیل شده
                "canceled_orders": order_summary.canceled_orders,                       # تعداد سفارش لغو شده
            },
            status_code=200,
        )
    except HTTPException as http_error:
        raise http_error
    except Exception:
        raise HTTPException(status_code=500, detail="Get order KPI report failed")

