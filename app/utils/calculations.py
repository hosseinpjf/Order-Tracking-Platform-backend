from fastapi import HTTPException
from decimal import Decimal, ROUND_HALF_UP


def calculate_discounted_price(price: int | float, discount_percent: int | float) -> int:
    """
    Calculate the discounted price using financial rounding (ROUND_HALF_UP).
    Args: price: Original product price. & discount_percent: Discount percentage (0-100).
    Returns: Discounted price rounded to the nearest integer.
    """

    price = Decimal(str(price))
    discount_percent = Decimal(str(discount_percent))

    discounted_price = (
        price * (Decimal("100") - discount_percent) / Decimal("100")
    ).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

    return int(discounted_price)


def calculate_order_totals(items, product_ids, db_products):
    
    original_total_price = 0
    final_total_price = 0
    total_prepare_time = 0

    if len(db_products) != len(set(product_ids)):
        raise HTTPException(status_code=404, detail="One or more products not found")

    if len(product_ids) != len(set(product_ids)):
        raise HTTPException(status_code=400, detail="Duplicate product_id in items")

    products_map = {p.id: p for p in db_products}
    for item in items:
        db_product = products_map[item.product_id]

        if not db_product.is_available:
            raise HTTPException(status_code=400, detail="The product is not available")

        discounted_price = calculate_discounted_price(db_product.price, db_product.discount_percent)
        final_total_price += discounted_price * item.quantity
        original_total_price += db_product.price * item.quantity
        total_prepare_time += db_product.prepare_time * item.quantity

    return {
        "final_total_price": final_total_price, 
        "original_total_price": original_total_price, 
        "total_prepare_time": total_prepare_time
    }