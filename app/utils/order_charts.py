from datetime import datetime, time
from collections import Counter
from sqlalchemy import func, Integer
from sqlalchemy.orm import Session
from app.models.order import Order, OrderStatus
from app.utils.chart_helper import get_chart_group_type, get_daily_group_expression, merge_daily_rows, fill_missing_periods, normalize_datetime


# ------------
def get_orders_trend(
    db: Session,
    from_date: datetime,
    to_date: datetime,
) -> list[dict]:
    
    from_date = normalize_datetime(from_date)
    to_date = normalize_datetime(to_date)

    group_type = get_chart_group_type(from_date, to_date)
    daily_expression = get_daily_group_expression(db, Order.created_at)
    end_of_to_date = datetime.combine(to_date.date(), time.max)

    rows = (
        db.query(
            daily_expression.label("key"),
            func.count(Order.id).label("orders_count"),
        )
        .filter(
            Order.created_at >= from_date,
            Order.created_at <= end_of_to_date,
        )
        .group_by(daily_expression)
        .order_by(daily_expression)
        .all()
    )

    buckets = merge_daily_rows(rows, group_type, "orders_count")
    result = fill_missing_periods(buckets, from_date, to_date, group_type)

    for item in result:
        item["value"] = int(item["value"])

    return result


# ------------
def get_sales_trend(
    db: Session,
    from_date: datetime,
    to_date: datetime,
) -> list[dict]:

    from_date = normalize_datetime(from_date)
    to_date = normalize_datetime(to_date)

    group_type = get_chart_group_type(from_date, to_date)
    daily_expression = get_daily_group_expression(db, Order.created_at)
    end_of_to_date = datetime.combine(to_date.date(), time.max)

    rows = (
        db.query(
            daily_expression.label("key"),
            func.sum(Order.final_total_price).label("total_sales"),
        )
        .filter(Order.status == OrderStatus.completed)
        .filter(
            Order.created_at >= from_date,
            Order.created_at <= end_of_to_date,
        )
        .group_by(daily_expression)
        .order_by(daily_expression)
        .all()
    )

    buckets = merge_daily_rows(rows, group_type, "total_sales")
    result = fill_missing_periods(buckets, from_date, to_date, group_type)

    for item in result:
        item["value"] = int(item["value"])

    return result


# ------------
def get_order_type_chart(
    db: Session,
    from_date: datetime,
    to_date: datetime,
) -> list[dict]:

    from_date = normalize_datetime(from_date)
    to_date = normalize_datetime(to_date)

    end_of_to_date = datetime.combine(to_date.date(), time.max)

    rows = (
        db.query(Order.order_type, func.count(Order.id))
        .filter(
            Order.created_at >= from_date,
            Order.created_at <= end_of_to_date,
            Order.order_type.isnot(None),
        )
        .group_by(Order.order_type)
        .all()
    )

    counter = {order_type.value: int(count) for order_type, count in rows}

    return [
        {
            "key": order_type,
            "value": counter.get(order_type, 0)
        }
        for order_type in ("delivery", "takeaway", "dine_in")
    ]


# ------------
def get_payment_type_chart(
    db: Session,
    from_date: datetime,
    to_date: datetime,
) -> list[dict]:

    from_date = normalize_datetime(from_date)
    to_date = normalize_datetime(to_date)

    end_of_to_date = datetime.combine(to_date.date(), time.max)

    rows = (
        db.query(Order.payment_type, func.count(Order.id))
        .filter(
            Order.created_at >= from_date,
            Order.created_at <= end_of_to_date,
            Order.payment_type.isnot(None),
        )
        .group_by(Order.payment_type)
        .all()
    )

    counter = {payment_type.value: int(count) for payment_type, count in rows}

    return [
        {
            "key": payment_type,
            "value": counter.get(payment_type, 0)
        }
        for payment_type in ("online", "offline")
    ]


# ------------
def get_hour_expression(db: Session, created_at):

    dialect = db.bind.dialect.name
    if dialect == "postgresql":
        return func.cast(func.extract("hour", created_at), Integer)

    return func.cast(func.strftime("%H", created_at), Integer)

def get_busy_hours_chart(
    db: Session,
    from_date: datetime,
    to_date: datetime,
) -> list[dict]:

    from_date = normalize_datetime(from_date)
    to_date = normalize_datetime(to_date)

    end_of_to_date = datetime.combine(to_date.date(), time.max)
    hour_expression = get_hour_expression(db, Order.created_at)

    rows = (
        db.query(hour_expression.label("hour"), func.count(Order.id))
        .filter(
            Order.created_at >= from_date,
            Order.created_at <= end_of_to_date,
        )
        .group_by(hour_expression)
        .all()
    )

    counter = {int(hour): int(count) for hour, count in rows}

    return [
        {"key": hour, "value": counter.get(hour, 0)}
        for hour in range(24)
    ]


# ------------
def get_weekday_orders_chart(
    db: Session,
    from_date: datetime,
    to_date: datetime,
) -> list[dict]:

    from_date = normalize_datetime(from_date)
    to_date = normalize_datetime(to_date)

    end_of_to_date = datetime.combine(to_date.date(), time.max)

    rows = (
        db.query(Order.created_at)
        .filter(
            Order.created_at >= from_date,
            Order.created_at <= end_of_to_date,
        )
        .all()
    )

    counter = Counter()

    for row in rows:
        counter[row.created_at.weekday()] += 1

    weekday_names = (
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    )

    result = []

    for index, weekday in enumerate(weekday_names):
        result.append({
            "key": weekday,
            "value": counter.get(index, 0)
        })

    return result

