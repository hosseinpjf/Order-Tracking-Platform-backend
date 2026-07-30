from sqlalchemy import func
from sqlalchemy.orm import Session
from collections import Counter
from math import ceil
from app.models.product import Product, ProductTags
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem


def get_best_selling_products_chart(db: Session) -> list[dict]:

    total_quantity = func.coalesce(
        func.sum(OrderItem.quantity), 0
    )

    products = (
        db.query(
            Product.id,
            Product.title,
            total_quantity.label("total_quantity"),
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.status == OrderStatus.completed)
        .group_by(Product.id, Product.title)
        .order_by(
            total_quantity.desc(),
            Product.title.asc(),
        )
        .all()
    )

    return [
        {
            "id": product.id,
            "key": product.title,
            "value": int(product.total_quantity),
        }
        for product in products
    ]


def get_highest_revenue_products_chart(db: Session) -> list[dict]:

    total_revenue = func.coalesce(
        func.sum(OrderItem.quantity * OrderItem.price_at_time), 0
    )

    products = (
        db.query(
            Product.id,
            Product.title,
            total_revenue.label("total_revenue"),
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.status == OrderStatus.completed)
        .group_by(Product.id, Product.title)
        .order_by(
            total_revenue.desc(),
            Product.title.asc(),
        )
        .all()
    )

    return [
        {
            "id": product.id,
            "key": product.title,
            "value": int(product.total_revenue),
        }
        for product in products
    ]


def get_price_distribution_chart(db: Session, price_distribution_buckets: int = 5) -> list[dict]:

    prices = [
        price
        for (price,) in db.query(Product.price).all()
    ]

    if not prices:
        return []

    min_price = min(prices)
    max_price = max(prices)

    if min_price == max_price:
        return [
            {
                "key": str(min_price),
                "value": len(prices),
            }
        ]

    bucket_count = price_distribution_buckets
    bucket_size = ceil((max_price - min_price + 1) / bucket_count)

    counter = Counter()

    for price in prices:

        index = (price - min_price) // bucket_size

        index = min(index, bucket_count - 1)

        counter[index] += 1

    result = []

    for index in range(bucket_count):

        start = min_price + (index * bucket_size)
        end = start + bucket_size - 1

        result.append({
            "key": f"{start}-{end}",
            "value": counter.get(index, 0),
        })

    return result


def get_tags_distribution_chart(db: Session) -> list[dict]:

    products = db.query(Product.tags).all()

    counter = Counter()

    for product in products:

        if not product.tags:
            continue

        for tag in product.tags:
            counter[tag] += 1

    return [
        {
            "key": tag.value,
            "value": counter.get(tag.value, 0),
        }
        for tag in ProductTags
        if counter[tag.value] > 0
    ]

