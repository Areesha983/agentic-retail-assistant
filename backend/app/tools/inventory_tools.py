from typing import Optional

from app.services import inventory_service


def check_inventory(
    product_id: int,
    variant: Optional[str] = None,
    color: Optional[str] = None,
    branch: Optional[str] = None,
):
    """
    Controlled agent tool for checking inventory records.
    """

    if not isinstance(product_id, int):
        raise ValueError("Product ID must be an integer")

    if product_id <= 0:
        raise ValueError("Product ID must be greater than 0")

    inventory = inventory_service.get_inventory(
        product_id=product_id,
        variant=variant,
        color=color,
        branch=branch
    )

    total_quantity = sum(
        item.get("quantity", 0)
        for item in inventory
    )

    return {
        "success": True,
        "product_id": product_id,
        "variant": variant,
        "color": color,
        "branch": branch,
        "total_quantity": total_quantity,
        "inventory": inventory
    }


def check_availability(
    product_id: int,
    variant: Optional[str] = None,
    color: Optional[str] = None,
    branch: Optional[str] = None,
    quantity: int = 1,
):
    """
    Controlled agent tool for checking whether requested stock is available.
    """

    if not isinstance(product_id, int):
        raise ValueError("Product ID must be an integer")

    if product_id <= 0:
        raise ValueError("Product ID must be greater than 0")

    if not isinstance(quantity, int):
        raise ValueError("Quantity must be an integer")

    if quantity <= 0:
        raise ValueError("Quantity must be greater than 0")

    inventory = inventory_service.get_inventory(
        product_id=product_id,
        variant=variant,
        color=color,
        branch=branch
    )

    total_quantity = sum(
        item.get("quantity", 0)
        for item in inventory
    )

    return {
        "success": True,
        "available": total_quantity >= quantity,
        "requested_quantity": quantity,
        "available_quantity": total_quantity,
        "product_id": product_id,
        "variant": variant,
        "color": color,
        "branch": branch,
        "inventory": inventory
    }