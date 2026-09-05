from typing import Optional

from app.services import smart_cart_service


def create_smart_cart(user_id: str):
    """
    Controlled agent tool for creating a Smart Cart.
    """

    if not isinstance(user_id, str):
        raise ValueError("User ID must be a string")

    user_id = user_id.strip()

    if not user_id:
        raise ValueError("User ID cannot be empty")

    cart = smart_cart_service.create_smart_cart(user_id)

    return {
        "success": True,
        "cart": cart
    }


def add_to_smart_cart(
    cart_id: int,
    product_id: int,
    variant: Optional[str] = None,
    color: Optional[str] = None,
    quantity: int = 1,
    maximum_price: Optional[float] = None,
    auto_buy_enabled: bool = False,
):
    """
    Controlled agent tool for adding a product to a Smart Cart.
    """

    if type(cart_id) is not int or cart_id <= 0:
        raise ValueError("Cart ID must be a positive integer")

    if type(product_id) is not int or product_id <= 0:
        raise ValueError("Product ID must be a positive integer")

    if type(quantity) is not int or quantity <= 0:
        raise ValueError("Quantity must be a positive integer")

    if maximum_price is not None:
        if isinstance(maximum_price, bool) or not isinstance(
            maximum_price,
            (int, float)
        ):
            raise ValueError("Maximum price must be a number")

        if maximum_price <= 0:
            raise ValueError("Maximum price must be greater than 0")

    if not isinstance(auto_buy_enabled, bool):
        raise ValueError("auto_buy_enabled must be a boolean")

    if variant is not None:
        variant = variant.strip() or None

    if color is not None:
        color = color.strip() or None

    item = smart_cart_service.add_item_to_smart_cart(
        cart_id=cart_id,
        product_id=product_id,
        variant=variant,
        color=color,
        quantity=quantity,
        maximum_price=maximum_price,
        auto_buy_enabled=auto_buy_enabled
    )

    return {
        "success": True,
        "item": item
    }


def view_smart_cart(cart_id: int):
    """
    Controlled agent tool for viewing a Smart Cart and its items.
    """

    if type(cart_id) is not int or cart_id <= 0:
        raise ValueError("Cart ID must be a positive integer")

    result = smart_cart_service.get_smart_cart(cart_id)

    return {
        "success": True,
        "cart": result["cart"],
        "items": result["items"]
    }


def cancel_smart_cart_item(item_id: int):
    """
    Controlled agent tool for cancelling a Smart Cart item.
    """

    if type(item_id) is not int or item_id <= 0:
        raise ValueError("Item ID must be a positive integer")

    item = smart_cart_service.cancel_smart_cart_item(item_id)

    return {
        "success": True,
        "message": "Smart Cart item cancelled successfully",
        "item": item
    }