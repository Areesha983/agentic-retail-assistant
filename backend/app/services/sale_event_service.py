from app.database.supabase import supabase


def create_sale_event(product_id: int, new_price: float):

    # Get the current product
    product_response = (
        supabase
        .table("products")
        .select("*")
        .eq("product_id", product_id)
        .execute()
    )

    if not product_response.data:
        raise ValueError("Product not found")

    product = product_response.data[0]

    old_price = product["current_price"]

    # New price must be lower than current price
    if new_price >= old_price:
        raise ValueError(
            "New price must be lower than the current price"
        )

    # Update product price
    update_response = (
        supabase
        .table("products")
        .update({
            "current_price": new_price
        })
        .eq("product_id", product_id)
        .execute()
    )

    if not update_response.data:
        raise ValueError("Failed to update product price")

    # Record the sale event
    event_response = (
        supabase
        .table("sale_events")
        .insert({
            "product_id": product_id,
            "old_price": old_price,
            "new_price": new_price
        })
        .execute()
    )

    if not event_response.data:
        raise ValueError("Failed to create sale event")

    return {
        "product": update_response.data[0],
        "sale_event": event_response.data[0]
    }

def find_matching_smart_carts(event_id: int):

    # Get the sale event
    event_response = (
        supabase
        .table("sale_events")
        .select("*")
        .eq("event_id", event_id)
        .execute()
    )

    if not event_response.data:
        raise ValueError("Sale event not found")

    sale_event = event_response.data[0]

    product_id = sale_event["product_id"]
    new_price = sale_event["new_price"]

    # Find Smart Cart items watching this product
    items_response = (
        supabase
        .table("smart_cart_items")
        .select("*")
        .eq("product_id", product_id)
        .eq("status", "WATCHING")
        .execute()
    )

    matching_items = []

    for item in items_response.data:

        # Auto-buy must be enabled
        if not item["auto_buy_enabled"]:
            continue

        # Maximum price must exist
        if item["maximum_price"] is None:
            continue

        # Sale price must be within customer's limit
        if new_price <= item["maximum_price"]:
            matching_items.append(item)

    return {
        "sale_event": sale_event,
        "matches": matching_items
    }