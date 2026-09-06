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
            "reason": (
                f"Smart Cart item is not WATCHING. "
                f"Current status: {item['status']}"
            )
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
                f"is above maximum price Rs. "
                f"{item['maximum_price']}"
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

    # Find one inventory location with enough stock.
    # We do not combine inventory across different branches.
    eligible_inventory = [
        inventory
        for inventory in inventory_response.data
        if inventory["quantity"] >= item["quantity"]
    ]

    if not eligible_inventory:
        best_available = max(
            (
                inventory["quantity"]
                for inventory in inventory_response.data
            ),
            default=0
        )

        return {
            "valid": False,
            "reason": (
                "Insufficient inventory at a single location. "
                f"Required: {item['quantity']}, "
                f"Best available at one location: {best_available}"
            )
        }

    # Choose deterministically:
    # highest stock first, then lowest inventory_id.
    selected_inventory = sorted(
        eligible_inventory,
        key=lambda inventory: (
            -inventory["quantity"],
            inventory["inventory_id"]
        )
    )[0]

    available_inventory = selected_inventory["quantity"]

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
            "inventory_available": available_inventory,
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
        "inventory_available": available_inventory,
        "selected_inventory": selected_inventory,
        "purchase_attempt": (
            attempt_response.data[0]
            if attempt_response.data
            else None
        )
    }


def execute_purchase(smart_cart_item_id: int):
    """
    Execute an authorized Smart Cart purchase through
    one atomic PostgreSQL transaction.

    The database RPC performs the final checks, inventory
    update, order creation, Smart Cart status update,
    and purchase-attempt update.
    """

    if type(smart_cart_item_id) is not int:
        raise ValueError(
            "Smart Cart item ID must be an integer"
        )

    if smart_cart_item_id <= 0:
        raise ValueError(
            "Smart Cart item ID must be greater than 0"
        )

    response = (
        supabase
        .rpc(
            "execute_smart_cart_purchase",
            {
                "p_smart_cart_item_id":
                    smart_cart_item_id
            }
        )
        .execute()
    )

    result = response.data

    # Depending on the Supabase/PostgREST response,
    # normalize a one-item list if necessary.
    if isinstance(result, list):
        result = result[0] if result else None

    if not isinstance(result, dict):
        raise RuntimeError(
            "Purchase transaction returned an invalid result"
        )

    # Preserve the existing service behavior:
    # failed validation/purchase conditions raise an error,
    # while successful purchases return the result.
    if not result.get("success"):
        raise ValueError(
            result.get(
                "reason",
                "Purchase could not be completed"
            )
        )

    return result


def get_purchase_attempts(smart_cart_item_id: int):

    response = (
        supabase
        .table("purchase_attempts")
        .select("*")
        .eq(
            "smart_cart_item_id",
            smart_cart_item_id
        )
        .order(
            "timestamp",
            desc=True
        )
        .execute()
    )

    return response.data