from sqlalchemy import func, case
from sqlalchemy.orm import Session
from app.models.category import Category
from app.models.product import Product
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem


def get_products_count_chart(db: Session) -> list[dict]:
    
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

    return [
        {
            "id": category.id,
            "title": category.title,
            "value": int(category.products_count)
        }
        for category in categories
    ]


def get_category_sales_chart(db: Session) -> list[dict]:
    
    total_sales = func.coalesce(
        func.sum(
            case(
                (
                    Order.status == OrderStatus.completed,
                    OrderItem.quantity * OrderItem.price_at_time,
                ), else_=0,
            )
        ), 0,
    )

    categories = (
        db.query(
            Category.id,
            Category.title,
            total_sales.label("total_sales"),
        )
        .outerjoin(Product, Product.category_id == Category.id)
        .outerjoin(OrderItem, OrderItem.product_id == Product.id)
        .outerjoin(Order, Order.id == OrderItem.order_id)
        .group_by(Category.id, Category.title)
        .order_by(
            total_sales.desc(),
            Category.title.asc(),
        )
        .all()
    )

    return [
        {
            "id": category.id,
            "title": category.title,
            "value": int(category.total_sales),
        }
        for category in categories
    ]

