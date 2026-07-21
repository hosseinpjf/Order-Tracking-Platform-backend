from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
import math
from datetime import datetime, timezone
from app.db.session import get_db
from app.services.jwt_bearer import get_payload
from app.schemas.order import CreateOrder, OutOrder, UpdateStatus, OutFullOrder, OrderItemInput, UpdateOrderItem
from app.models.order import Order, OrderStatus, OrderType, OrderSort, ALLOWED_TRANSITIONS, PaymentType
from app.models.order_item import OrderItem
from app.models.order_status_history import OrderStatusHistory, StatusChangedBy
from app.models.product import Product
from app.models.user import User
from app.middleware.exception_handler import response_handler
from app.utils.calculations import calculate_order_totals, calculate_discounted_price
from app.utils.get_site_info import get_working_hours, get_settings


router = APIRouter(prefix="/order", tags=["Order"])


@router.post("/")
def create_order(data: CreateOrder, payload = Depends(get_payload), db: Session = Depends(get_db)):
    try:
        db_settings = get_settings(db, ["accept_order"])
        if not db_settings["accept_order"]:
            raise HTTPException(status_code=400, detail="Accept order disabled")
        
        product_ids = [item.product_id for item in data.items]
        db_products = db.query(Product).filter(Product.id.in_(product_ids)).all()
        values = calculate_order_totals(data.items, product_ids, db_products)

        db_user = db.query(User).filter(User.id == payload["sub"]).first()

        # Working hours
        now_time = datetime.now(timezone.utc)

        workday = get_working_hours(db, now_time)
        open_time = workday["open_time"]
        close_time = workday["close_time"]
        is_closed = workday["is_closed"]

        if is_closed:
            raise HTTPException(status_code=400, detail="Cafe is closed today")

        open_dt = datetime.combine(now_time.date(), open_time).replace(tzinfo=timezone.utc)
        close_dt = datetime.combine(now_time.date(), close_time).replace(tzinfo=timezone.utc)
        if now_time < open_dt or now_time > close_dt:
            raise HTTPException(status_code=400, detail="Order is outside business hours")

        # Order
        new_order = Order(
            user_id = payload["sub"],
            user_name = db_user.name,
            order_type = data.order_type,
            payment_type = data.payment_type,
            status = OrderStatus.pending,
            items_count = len(data.items),
            original_total_price = values["original_total_price"],
            final_total_price = values["final_total_price"],
            total_prepare_time = values["total_prepare_time"]
        )
        db.add(new_order)
        db.flush()
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
        payment_type: PaymentType | None = Query(None),
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
        if payment_type:
            query = query.filter(Order.payment_type == payment_type)

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
        
        if payload["role"] != "admin":
            if payload["sub"] != db_order.user_id:
                raise HTTPException(status_code=403, detail="Access denied")
            if data.status != OrderStatus.canceled:
                raise HTTPException(status_code=403, detail="Users can only cancel their own orders")
            if db_order.status not in [OrderStatus.pending]:
                raise HTTPException(status_code=400, detail="Order cannot be canceled in this status")
            
        db_order_status_history = (db
            .query(OrderStatusHistory)
            .filter(OrderStatusHistory.order_id == order_id)
            .order_by(OrderStatusHistory.start_at.desc())
            .first()
        )
        if not db_order_status_history:
            raise HTTPException(status_code=404, detail="Order status history not found")
        
        if db_order_status_history.status == OrderStatus.preparing:
            expected_status = OrderStatus.delivering if db_order.order_type == OrderType.delivery else OrderStatus.completed
            if data.status != expected_status:
                raise HTTPException(status_code=400, detail="Invalid status transition for this order type")

        allowed = ALLOWED_TRANSITIONS.get(db_order_status_history.status, set())
        if data.status not in allowed:
            raise HTTPException(status_code=400, detail="Invalid status transition")
            
        db_order.status = data.status

        end_at_status = datetime.now(timezone.utc)

        if db_order_status_history.start_at.tzinfo is None:
            db_order_status_history.start_at = db_order_status_history.start_at.replace(tzinfo=timezone.utc)

        db_order_status_history.end_at = end_at_status
        db_order_status_history.duration_seconds = int((end_at_status - db_order_status_history.start_at).total_seconds())
        db_order_status_history.changed_by = StatusChangedBy.system if data.changed_by == StatusChangedBy.system.value else StatusChangedBy[payload["role"]]

        if data.status == OrderStatus.completed or data.status == OrderStatus.canceled:
            new_order_status_history = OrderStatusHistory(
                order_id = order_id,
                status = data.status,
                changed_by = StatusChangedBy.system if data.changed_by == StatusChangedBy.system.value else StatusChangedBy[payload["role"]],
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


@router.post("/{order_id}/items")
def add_item(order_id: str, data: OrderItemInput, payload = Depends(get_payload), db: Session = Depends(get_db)):
    try:
        db_order = db.query(Order).filter(Order.id == order_id).first()
        if not db_order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        if payload["role"] != "admin" and payload["sub"] != db_order.user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        if db_order.status not in [OrderStatus.pending]:
            raise HTTPException(status_code=400, detail="Order cannot be modified in this status")

        db_product = db.query(Product).filter(Product.id == data.product_id, Product.is_available == True).first()
        if not db_product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        product_ids = [item.product_id for item in db_order.items]
        if data.product_id in product_ids:
            raise HTTPException(status_code=409, detail="Product already exists")
        
        price_at_time = calculate_discounted_price(db_product.price, db_product.discount_percent)
        new_order_item = OrderItem(
            order_id = order_id,
            product_id = data.product_id,
            quantity = data.quantity,
            price_at_time = price_at_time
        )
        db.add(new_order_item)
        db.flush()
        db.refresh(db_order)

        product_ids = [item.product_id for item in db_order.items]
        db_products = db.query(Product).filter(Product.id.in_(product_ids)).all()
        values = calculate_order_totals(db_order.items, product_ids, db_products)

        db_order.items_count = len(db_order.items)
        db_order.original_total_price = values["original_total_price"]
        db_order.final_total_price = values["final_total_price"]
        db_order.total_prepare_time = values["total_prepare_time"]

        db.commit()

        return response_handler(
            status=True,
            message="Item successfully added",
            data=OutOrder.model_validate(db_order).model_dump(),
            status_code=200
        )
    except HTTPException as http_error:
        db.rollback()
        raise http_error
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Order add item failed")


@router.delete("/{order_id}/items/{item_id}")
def delete_item(order_id: str, item_id: str, payload = Depends(get_payload), db: Session = Depends(get_db)):
    try:
        db_order = db.query(Order).filter(Order.id == order_id).first()
        if not db_order:
            raise HTTPException(status_code=404, detail="Order not found")

        if payload["role"] != "admin" and payload["sub"] != db_order.user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        if db_order.status not in [OrderStatus.pending]:
            raise HTTPException(status_code=400, detail="Order cannot be modified in this status")

        db_order_item = db.query(OrderItem).filter(OrderItem.id == item_id).first()
        if not db_order_item:
            raise HTTPException(status_code=404, detail="Order item not found")
        
        db.delete(db_order_item)
        db.flush()
        db.refresh(db_order)

        product_ids = [item.product_id for item in db_order.items]
        db_products = db.query(Product).filter(Product.id.in_(product_ids)).all()
        values = calculate_order_totals(db_order.items, product_ids, db_products)

        db_order.items_count = len(db_order.items)
        db_order.original_total_price = values["original_total_price"]
        db_order.final_total_price = values["final_total_price"]
        db_order.total_prepare_time = values["total_prepare_time"]

        db.commit()
        db.refresh(db_order)

        return response_handler(
            status=True,
            message="Item successfully deleted",
            data=OutOrder.model_validate(db_order).model_dump(),
            status_code=200
        )
    except HTTPException as http_error:
        db.rollback()
        raise http_error
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Order add item failed")


@router.patch("/{order_id}/items/{item_id}")
def update_item(order_id: str, item_id: str, data: UpdateOrderItem, payload = Depends(get_payload), db: Session = Depends(get_db)):
    try:
        db_order = db.query(Order).filter(Order.id == order_id).first()
        if not db_order:
            raise HTTPException(status_code=404, detail="Order not found")

        if payload["role"] != "admin" and payload["sub"] != db_order.user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        if db_order.status not in [OrderStatus.pending]:
            raise HTTPException(status_code=400, detail="Order cannot be modified in this status")

        db_order_item = db.query(OrderItem).filter(OrderItem.id == item_id).first()
        if not db_order_item:
            raise HTTPException(status_code=404, detail="Order item not found")
        
        db_order_item.quantity = data.quantity

        db.flush()
        db.refresh(db_order_item)
        db.refresh(db_order)

        product_ids = [item.product_id for item in db_order.items]
        db_products = db.query(Product).filter(Product.id.in_(product_ids)).all()
        values = calculate_order_totals(db_order.items, product_ids, db_products)

        db_order.original_total_price = values["original_total_price"]
        db_order.final_total_price = values["final_total_price"]
        db_order.total_prepare_time = values["total_prepare_time"]

        db.commit()
        db.refresh(db_order)

        return response_handler(
            status=True,
            message="Item successfully updated",
            data=OutOrder.model_validate(db_order).model_dump(),
            status_code=200
        )
    except HTTPException as http_error:
        db.rollback()
        raise http_error
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Order update item failed")


@router.post("/{order_id}/pay")
def pay_order(order_id: str, payload = Depends(get_payload), db: Session = Depends(get_db)):
    # This section is for demonstration purposes only and is incomplete.
    try:
        db_order = db.query(Order).filter(Order.id == order_id).first()
        if not db_order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        if db_order.status != OrderStatus.pending:
            raise HTTPException(status_code=400, detail="Order cannot be paid in this status")
        
        db_order.status = OrderStatus.confirmed

        db_order_status_history = (db
            .query(OrderStatusHistory)
            .filter(OrderStatusHistory.order_id == order_id)
            .order_by(OrderStatusHistory.start_at.desc())
            .first()
        )
        if not db_order_status_history:
            raise HTTPException(status_code=404, detail="Order status history not found")
        
        end_at_status = datetime.now(timezone.utc)

        if db_order_status_history.start_at.tzinfo is None:
            db_order_status_history.start_at = db_order_status_history.start_at.replace(tzinfo=timezone.utc)

        db_order_status_history.end_at = end_at_status
        db_order_status_history.duration_seconds = int((end_at_status - db_order_status_history.start_at).total_seconds())
        db_order_status_history.changed_by = StatusChangedBy.user

        new_order_status_history = OrderStatusHistory(
            order_id = order_id,
            status = OrderStatus.confirmed,
        )
        db.add(new_order_status_history)
        db.flush()
        db.refresh(db_order)

        db_settings = get_settings(db, ["allow_online_payment", "allow_offline_payment"])
        
        if db_order.payment_type == PaymentType.online:
            if payload["sub"] != db_order.user_id:
                raise HTTPException(status_code=403, detail="Only user can pay online")
            
            if not db_settings["allow_online_payment"]:
                raise HTTPException(status_code=400, detail="Allow online payment disabled")
            
            db.commit()
            
            gateway_url = f"https://bank.example.com/pay?order_id={order_id}&amount={db_order.final_total_price}"
            return response_handler(
                status=True,
                message="Redirect to payment gateway",
                data={
                    "payment_url": gateway_url,
                    "order": OutOrder.model_validate(db_order).model_dump()
                },
                status_code=200
            )

        elif db_order.payment_type == PaymentType.offline:
            if payload["role"] != "admin":
                raise HTTPException(status_code=403, detail="Only admin can confirm offline payments")
            
            if not db_settings["allow_offline_payment"]:
                raise HTTPException(status_code=400, detail="Allow offline payment disabled")
            
            db.commit()
            
            return response_handler(
                status=True,
                message="Offline payment confirmed",
                data={
                    "order": OutOrder.model_validate(db_order).model_dump()
                },
                status_code=200
            )
        
        else:
            raise HTTPException(status_code=400, detail="Invalid payment type")
        
    except HTTPException as http_error:
        db.rollback()
        raise http_error
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Order payment failed")

