from app.database.supabase import supabase


def validate_purchase(smart_cart_item_id: int):

    # --------------------------------------------------
    # 1. Get Smart Cart Item
    # --------------------------------------------------

    item_response = (
        supabase
        .table("smart_cart_items")
        .select("*")
        .eq("item_id", smart_cart_item_id)
        .execute()
    )

    if not item_response.data:
        raise ValueError("Smart Cart item not found")

    item = item_response.data[0]

    # --------------------------------------------------
    # 2. Check item status
    # --------------------------------------------------

    if item["status"] != "WATCHING":
        return {
            "valid": False,
            "reason": f"Smart Cart item is not WATCHING. Current status: {item['status']}"
        }

    # --------------------------------------------------
    # 3. Check Auto-Buy authorization
    # --------------------------------------------------

    if not item["auto_buy_enabled"]:
        return {
            "valid": False,
            "reason": "Automatic purchase is not enabled"
        }

    # --------------------------------------------------
    # 4. Get current product price
    # --------------------------------------------------

    product_response = (
        supabase
        .table("products")
        .select("*")
        .eq("product_id", item["product_id"])
        .execute()
    )

    if not product_response.data:
        raise ValueError("Product not found")

    product = product_response.data[0]

    current_price = product["current_price"]

    # --------------------------------------------------
    # 5. Check maximum price
    # --------------------------------------------------

    if item["maximum_price"] is None:
        return {
            "valid": False,
            "reason": "No maximum price has been specified"
        }

    if current_price > item["maximum_price"]:
        return {
            "valid": False,
            "reason": (
                f"Current price Rs. {current_price} "
                f"is above maximum price Rs. {item['maximum_price']}"
            )
        }

    # --------------------------------------------------
    # 6. Check inventory
    # --------------------------------------------------

    inventory_query = (
        supabase
        .table("inventory")
        .select("*")
        .eq("product_id", item["product_id"])
    )

    if item["variant"] is not None:
        inventory_query = inventory_query.eq(
            "variant",
            item["variant"]
        )

    if item["color"] is not None:
        inventory_query = inventory_query.eq(
            "color",
            item["color"]
        )

    inventory_response = inventory_query.execute()

    if not inventory_response.data:
        return {
            "valid": False,
            "reason": "Required product variant/color is not available"
        }

    # Calculate total available quantity
    total_inventory = sum(
        inventory["quantity"]
        for inventory in inventory_response.data
    )

    if total_inventory < item["quantity"]:
        return {
            "valid": False,
            "reason": (
                f"Insufficient inventory. "
                f"Required: {item['quantity']}, "
                f"Available: {total_inventory}"
            )
        }

    # --------------------------------------------------
    # 7. Check duplicate purchase
    # --------------------------------------------------

    order_response = (
        supabase
        .table("orders")
        .select("order_id")
        .eq(
            "smart_cart_item_id",
            smart_cart_item_id
        )
        .execute()
    )

    if order_response.data:
        return {
            "valid": False,
            "reason": "This Smart Cart item has already been purchased"
        }

    # --------------------------------------------------
    # 8. Record successful validation attempt
    # --------------------------------------------------

    attempt_response = (
        supabase
        .table("purchase_attempts")
        .insert({
            "smart_cart_item_id": smart_cart_item_id,
            "price": current_price,
            "inventory_available": total_inventory,
            "status": "VALIDATED",
            "reason": "All purchase validation checks passed"
        })
        .execute()
    )

    return {
        "valid": True,
        "reason": "Purchase validation successful",
        "smart_cart_item": item,
        "product": product,
        "current_price": current_price,
        "inventory_available": total_inventory,
        "purchase_attempt": (
            attempt_response.data[0]
            if attempt_response.data
            else None
        )
    }
def execute_purchase(smart_cart_item_id: int):

    # --------------------------------------------------
    # 1. Get Smart Cart Item
    # --------------------------------------------------

    item_response = (
        supabase
        .table("smart_cart_items")
        .select("*")
        .eq("item_id", smart_cart_item_id)
        .execute()
    )

    if not item_response.data:
        raise ValueError("Smart Cart item not found")

    item = item_response.data[0]

    # --------------------------------------------------
    # 2. Make sure item is WATCHING
    # --------------------------------------------------

    if item["status"] != "WATCHING":
        raise ValueError(
            f"Smart Cart item cannot be purchased. "
            f"Current status: {item['status']}"
        )

    # --------------------------------------------------
    # 3. Make sure auto-buy is enabled
    # --------------------------------------------------

    if not item["auto_buy_enabled"]:
        raise ValueError(
            "Automatic purchase is not enabled"
        )

    # --------------------------------------------------
    # 4. Get current product
    # --------------------------------------------------

    product_response = (
        supabase
        .table("products")
        .select("*")
        .eq("product_id", item["product_id"])
        .execute()
    )

    if not product_response.data:
        raise ValueError("Product not found")

    product = product_response.data[0]

    current_price = product["current_price"]

    # --------------------------------------------------
    # 5. Re-check maximum price
    # --------------------------------------------------

    if item["maximum_price"] is None:
        raise ValueError(
            "No maximum price specified"
        )

    if current_price > item["maximum_price"]:
        raise ValueError(
            f"Current price Rs. {current_price} "
            f"exceeds maximum price Rs. "
            f"{item['maximum_price']}"
        )

    # --------------------------------------------------
    # 6. Find matching inventory
    # --------------------------------------------------

    inventory_query = (
        supabase
        .table("inventory")
        .select("*")
        .eq("product_id", item["product_id"])
    )

    if item["variant"] is not None:
        inventory_query = inventory_query.eq(
            "variant",
            item["variant"]
        )

    if item["color"] is not None:
        inventory_query = inventory_query.eq(
            "color",
            item["color"]
        )

    inventory_response = inventory_query.execute()

    if not inventory_response.data:
        raise ValueError(
            "Required product variant/color is unavailable"
        )

    # Find an inventory location with enough stock
    selected_inventory = None

    for inventory in inventory_response.data:
        if inventory["quantity"] >= item["quantity"]:
            selected_inventory = inventory
            break

    if selected_inventory is None:
        raise ValueError(
            "Insufficient inventory"
        )

    # --------------------------------------------------
    # 7. Prevent duplicate purchase
    # --------------------------------------------------

    existing_order = (
        supabase
        .table("orders")
        .select("order_id")
        .eq(
            "smart_cart_item_id",
            smart_cart_item_id
        )
        .execute()
    )

    if existing_order.data:
        raise ValueError(
            "This Smart Cart item has already been purchased"
        )

    # --------------------------------------------------
    # 8. Mark item as PROCESSING
    # --------------------------------------------------

    supabase \
        .table("smart_cart_items") \
        .update({
            "status": "PROCESSING"
        }) \
        .eq(
            "item_id",
            smart_cart_item_id
        ) \
        .execute()

    try:

        # --------------------------------------------------
        # 9. Reduce inventory
        # --------------------------------------------------

        old_quantity = selected_inventory["quantity"]

        new_quantity = (
            old_quantity - item["quantity"]
        )

        inventory_update = (
            supabase
            .table("inventory")
            .update({
                "quantity": new_quantity
            })
            .eq(
                "inventory_id",
                selected_inventory["inventory_id"]
            )
            .execute()
        )

        if not inventory_update.data:
            raise ValueError(
                "Failed to update inventory"
            )

        # --------------------------------------------------
        # 10. Create mock order
        # --------------------------------------------------

        order_response = (
            supabase
            .table("orders")
            .insert({
                "user_id": item["cart_id"],
                "product_id": item["product_id"],
                "smart_cart_item_id": smart_cart_item_id,
                "variant": item["variant"],
                "color": item["color"],
                "quantity": item["quantity"],
                "price": current_price,
                "status": "CONFIRMED"
            })
            .execute()
        )

        if not order_response.data:
            raise ValueError(
                "Failed to create order"
            )

        order = order_response.data[0]

        # --------------------------------------------------
        # 11. Mark Smart Cart item as PURCHASED
        # --------------------------------------------------

        supabase \
            .table("smart_cart_items") \
            .update({
                "status": "PURCHASED"
            }) \
            .eq(
                "item_id",
                smart_cart_item_id
            ) \
            .execute()

        # --------------------------------------------------
        # 12. Update purchase attempt
        # --------------------------------------------------

        attempt_response = (
            supabase
            .table("purchase_attempts")
            .select("attempt_id")
            .eq(
                "smart_cart_item_id",
                smart_cart_item_id
            )
            .order(
                "timestamp",
                desc=True
            )
            .limit(1)
            .execute()
        )

        if attempt_response.data:

            supabase \
                .table("purchase_attempts") \
                .update({
                    "status": "SUCCESS",
                    "reason": "Mock purchase completed successfully"
                }) \
                .eq(
                    "attempt_id",
                    attempt_response.data[0]["attempt_id"]
                ) \
                .execute()

        # --------------------------------------------------
        # 13. Return result
        # --------------------------------------------------

        return {
            "success": True,
            "message": "Mock purchase completed successfully",
            "order": order,
            "inventory_before": old_quantity,
            "inventory_after": new_quantity
        }

    except Exception as e:

        # If something fails, restore item status
        supabase \
            .table("smart_cart_items") \
            .update({
                "status": "WATCHING"
            }) \
            .eq(
                "item_id",
                smart_cart_item_id
            ) \
            .execute()

        raise e

def get_purchase_attempts(smart_cart_item_id: int):
    response = (
        supabase
        .table("purchase_attempts")
        .select("*")
        .eq("smart_cart_item_id", smart_cart_item_id)
        .order("timestamp", desc=True)
        .execute()
    )

    return response.data