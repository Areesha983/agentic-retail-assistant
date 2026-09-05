from app.services import purchase_service


def validate_purchase(smart_cart_item_id: int):
    """
    Controlled agent tool for validating whether a Smart Cart item
    is eligible for automatic purchase.
    """

    if type(smart_cart_item_id) is not int:
        raise ValueError("Smart Cart item ID must be an integer")

    if smart_cart_item_id <= 0:
        raise ValueError("Smart Cart item ID must be greater than 0")

    result = purchase_service.validate_purchase(
        smart_cart_item_id
    )

    return {
        "success": True,
        "validation": result
    }


def execute_purchase(smart_cart_item_id: int):
    """
    Controlled agent tool for executing an authorized mock purchase.

    Authorization, price, inventory and duplicate-purchase checks
    remain inside purchase_service.
    """

    if type(smart_cart_item_id) is not int:
        raise ValueError("Smart Cart item ID must be an integer")

    if smart_cart_item_id <= 0:
        raise ValueError("Smart Cart item ID must be greater than 0")

    result = purchase_service.execute_purchase(
        smart_cart_item_id
    )

    return {
        "success": True,
        "purchase": result
    }