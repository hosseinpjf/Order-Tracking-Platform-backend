from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
import math
from datetime import datetime, timezone
from app.db.session import get_db
from app.services.jwt_bearer import get_payload
from app.schemas.order import CreateOrder, OutOrder, UpdateStatus, OutFullOrder
from app.models.order import Order, OrderStatus, OrderType, OrderSort, ALLOWED_TRANSITIONS
from app.models.order_item import OrderItem
from app.models.order_status_history import OrderStatusHistory
from app.models.product import Product
from app.models.user import User
from app.middleware.exception_handler import response_handler
from app.utils.calculations import calculate_order_totals, calculate_discounted_price


router = APIRouter(prefix="/order", tags=["Order"])


@router.post("/")
def create_order(data: CreateOrder, payload = Depends(get_payload), db: Session = Depends(get_db)):
    try:
        if payload["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")
        
        product_ids = [item.product_id for item in data.items]
        db_products = db.query(Product).filter(Product.id.in_(product_ids)).all()
        values = calculate_order_totals(data, product_ids, db_products)

        db_user = db.query(User).filter(User.id == payload["sub"]).first()
        
        # Order
        new_order = Order(
            user_id = payload["sub"],
            user_name = db_user.name,
            order_type = data.order_type,
            status = OrderStatus.pending,
            items_count = len(data.items),
            original_total_price = values["original_total_price"],
            final_total_price = values["final_total_price"],
            total_prepare_time = values["total_prepare_time"]
        )
        db.add(new_order)
        db.commit()
        db.refresh(new_order)

        # OrderItems
        products_map = {p.id: p for p in db_products}
        for item in data.items:
            product = products_map[item.product_id]
            price_at_time = calculate_discounted_price(product.price, product.discount_percent)

            new_order_item = OrderItem(
                order_id = new_order.id,
                product_id = item.product_id,
                quantity = item.quantity,
                price_at_time = price_at_time
            )
            db.add(new_order_item)

        # OrderStatusHistory
        new_order_status_history = OrderStatusHistory(
            order_id = new_order.id,
            status = OrderStatus.pending,
        )
        db.add(new_order_status_history)

        db.commit()

        return response_handler(
            status=True,
            message="Order created successfully",
            data=OutOrder.model_validate(new_order).model_dump(),
            status_code=201
        )
    except HTTPException as http_error:
        db.rollback()
        raise http_error
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Order create failed")


@router.get("/")
def get_orders(
        payload = Depends(get_payload), 
        db: Session = Depends(get_db),
        page: int = Query(1, ge=1), 
        limit: int = Query(20, ge=1, le=100),
        status: OrderStatus | None = Query(None),
        order_type: OrderType | None = Query(None),
        user_id: str | None = Query(None),
        q: str | None = Query(None),
        sort: OrderSort | None = Query(None),
        from_date: datetime | None = Query(None),
        to_date: datetime | None = Query(None)
    ):
    try:
        db_orders = []
        query = db.query(Order).order_by(Order.created_at.desc())

        if payload["role"] != "admin":
            query = query.filter(Order.user_id == payload["sub"])

        if payload["role"] == "admin" and user_id:
            query = query.filter(Order.user_id == user_id)
        if payload["role"] == "admin" and q:
            query = query.filter(Order.user_name.ilike(f"%{q}%"))

        if status:
            query = query.filter(Order.status == status)
        if order_type:
            query = query.filter(Order.order_type == order_type)

        if from_date:
            query = query.filter(Order.created_at >= from_date)
        if to_date:
            query = query.filter(Order.created_at <= to_date)

        db_orders_total = query.count()

        if sort == OrderSort.price_desc:
            query = query.order_by(Order.final_total_price.desc(), Order.created_at.desc())
        if sort == OrderSort.price_asc:
            query = query.order_by(Order.final_total_price.asc(), Order.created_at.desc())
        if sort == OrderSort.items_desc:
            query = query.outerjoin(OrderItem).group_by(Order.id).order_by(func.count(OrderItem.id).desc(), Order.created_at.desc())
        if sort == OrderSort.items_asc:
            query = query.outerjoin(OrderItem).group_by(Order.id).order_by(func.count(OrderItem.id).asc(), Order.created_at.desc())
        if sort == OrderSort.prepare_time_desc:
            query = query.order_by(Order.total_prepare_time.desc(), Order.created_at.desc())
        if sort == OrderSort.prepare_time_asc:
            query = query.order_by(Order.total_prepare_time.asc(), Order.created_at.desc())

        db_orders = query.offset((page - 1) * limit).limit(limit).all()

        return response_handler(
            status=True,
            message="All orders fetched",
            data={
                "orders": [
                    OutOrder.model_validate(order).model_dump()
                    for order in db_orders
                ],
                "page": page,
                "limit": limit,
                "total": db_orders_total,
                "pages": math.ceil(db_orders_total / limit)
            },
            status_code=200
        )

    except HTTPException as http_error:
        raise http_error
    except Exception:
        raise HTTPException(status_code=500, detail="Orders get failed")


@router.get("/{order_id}")
def get_order(order_id: str, payload = Depends(get_payload), db: Session = Depends(get_db)):
    try:
        db_order = db.query(Order).filter(Order.id == order_id).first()
        if not db_order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        if payload["role"] != "admin" and payload["sub"] != db_order.user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return response_handler(
            status=True,
            message="Order found",
            data=OutFullOrder.model_validate(db_order).model_dump(),
            status_code=200
        )
    except HTTPException as http_error:
        raise http_error
    except Exception:
        raise HTTPException(status_code=500, detail="Order get failed")


@router.patch("/{order_id}/status")
def update_status(
        order_id: str, 
        data: UpdateStatus, 
        payload = Depends(get_payload), 
        db: Session = Depends(get_db)
    ):
    try:
        db_order = db.query(Order).filter(Order.id == order_id).first()
        if not db_order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        db_order_status_history = (
            db.query(OrderStatusHistory)
            .filter(OrderStatusHistory.order_id == order_id)
            .order_by(OrderStatusHistory.start_at.desc())
            .first()
        )
        if not db_order_status_history:
            raise HTTPException(status_code=404, detail="Order status history not found")
        
        if db_order_status_history.status == OrderStatus.completed or db_order_status_history.status == OrderStatus.canceled:
            raise HTTPException(status_code=404, detail="The order is in the final status")
        
        allowed = ALLOWED_TRANSITIONS.get(db_order_status_history.status, set())
        if data.status not in allowed:
            raise HTTPException(status_code=400, detail="Invalid status transition")
            
        db_order.status = data.status

        end_at_status = datetime.now(timezone.utc)

        if db_order_status_history.start_at.tzinfo is None:
            db_order_status_history.start_at = db_order_status_history.start_at.replace(tzinfo=timezone.utc)

        db_order_status_history.changed_by = data.changed_by
        db_order_status_history.end_at = end_at_status
        db_order_status_history.duration_seconds = int(
            (end_at_status - db_order_status_history.start_at).total_seconds()
        )

        if data.status == OrderStatus.completed or data.status == OrderStatus.canceled:
            new_order_status_history = OrderStatusHistory(
                order_id = order_id,
                status = data.status,
                changed_by = data.changed_by,
                duration_seconds = 0,
                end_at = datetime.now(timezone.utc)
            )
            db.add(new_order_status_history)
        else:
            new_order_status_history = OrderStatusHistory(
                order_id = order_id,
                status = data.status,
            )
            db.add(new_order_status_history)
        
        db.commit()
        db.refresh(db_order)

        return response_handler(
            status=True,
            message="Status updated",
            data=OutOrder.model_validate(db_order).model_dump(),
            status_code=200
        )
    except HTTPException as http_error:
        db.rollback()
        raise http_error
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Order update status failed")

