from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import List
from app.models.order import OrderType, OrderStatus
from app.models.order_status_history import StatusChangedBy

class OrderItemInput(BaseModel):
    product_id: str
    quantity: int = Field(..., gt=0)

class CreateOrder(BaseModel):
    order_type: OrderType
    items: List[OrderItemInput]

class UpdateStatus(BaseModel):
    changed_by: StatusChangedBy
    status: OrderStatus


class OutOrder(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: str
    user_name: str
    status: OrderStatus
    order_type: OrderType
    items_count: int
    original_total_price: int
    final_total_price: int
    total_prepare_time: int
    updated_at: datetime
    created_at: datetime

class OutFullOrder(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: str
    user_name: str
    status: OrderStatus
    order_type: OrderType
    items_count: int
    original_total_price: int
    final_total_price: int
    total_prepare_time: int
    updated_at: datetime
    created_at: datetime
    items: List[OutOrderItems]
    status_history: List[OutOrderStatusHistory]

class OutOrderItems(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    order_id: str
    product_id: str
    quantity: int
    price_at_time: int
    created_at: datetime

class OutOrderStatusHistory(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    order_id: str
    status: OrderStatus
    duration_seconds: int | None
    changed_by: StatusChangedBy | None
    start_at: datetime
    end_at: datetime | None