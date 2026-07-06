from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.jwt_bearer import get_payload
from app.schemas.order import CreateOrder, OutOrder
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.product import Product
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
        
        # Order
        new_order = Order(
            user_id = payload["sub"],
            order_type = data.order_type,
            status = OrderStatus.pending,
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
