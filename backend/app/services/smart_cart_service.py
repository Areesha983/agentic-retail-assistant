from datetime import datetime, timezone

from app.database.supabase import supabase


def create_smart_cart(user_id: int):
    response = (
        supabase
        .table("smart_carts")
        .insert({
            "user_id": user_id,
            "status": "ACTIVE"
        })
        .execute()
    )

    if not response.data:
        raise ValueError("Failed to create Smart Cart")

    return response.data[0]


def add_item_to_smart_cart(
    cart_id: int,
    product_id: int,
    variant: str | None,
    color: str | None,
    quantity: int,
    maximum_price: float | None,
    auto_buy_enabled: bool
):
    cart_response = (
        supabase
        .table("smart_carts")
        .select("cart_id")
        .eq("cart_id", cart_id)
        .execute()
    )

    if not cart_response.data:
        raise ValueError("Smart Cart not found")

    product_response = (
        supabase
        .table("products")
        .select("product_id")
        .eq("product_id", product_id)
        .execute()
    )

    if not product_response.data:
        raise ValueError("Product not found")

    purchase_authorized_at = (
        datetime.now(timezone.utc).isoformat()
        if auto_buy_enabled
        else None
    )

    item_response = (
        supabase
        .table("smart_cart_items")
        .insert({
            "cart_id": cart_id,
            "product_id": product_id,
            "variant": variant,
            "color": color,
            "quantity": quantity,
            "maximum_price": maximum_price,
            "auto_buy_enabled": auto_buy_enabled,
            "purchase_authorized_at": purchase_authorized_at,
            "status": "WATCHING"
        })
        .execute()
    )

    if not item_response.data:
        raise ValueError("Failed to add item to Smart Cart")

    return item_response.data[0]


def get_smart_cart(cart_id: int):
    # Get the Smart Cart
    cart_response = (
        supabase
        .table("smart_carts")
        .select("*")
        .eq("cart_id", cart_id)
        .execute()
    )

    if not cart_response.data:
        raise ValueError("Smart Cart not found")

    cart = cart_response.data[0]

    # Get all items in the Smart Cart
    items_response = (
        supabase
        .table("smart_cart_items")
        .select("*")
        .eq("cart_id", cart_id)
        .execute()
    )

    return {
        "cart": cart,
        "items": items_response.data
    }


def cancel_smart_cart_item(item_id: int):
    # Get the item
    item_response = (
        supabase
        .table("smart_cart_items")
        .select("*")
        .eq("item_id", item_id)
        .execute()
    )

    if not item_response.data:
        raise ValueError("Smart Cart item not found")

    item = item_response.data[0]

    # Only active/watching items can be cancelled
    if item["status"] not in ["WATCHING", "FAILED"]:
        raise ValueError(
            f"Smart Cart item cannot be cancelled because "
            f"its status is {item['status']}"
        )

    # Cancel item
    update_response = (
        supabase
        .table("smart_cart_items")
        .update({
            "status": "CANCELLED"
        })
        .eq("item_id", item_id)
        .execute()
    )

    if not update_response.data:
        raise ValueError(
            "Failed to cancel Smart Cart item"
        )

    return update_response.data[0]