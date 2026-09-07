def validate_sale_candidate(
    sale_event: dict,
    smart_cart_item: dict
) -> dict:
    """
    Validate whether a Smart Cart item is eligible to be
    considered for an automatic purchase after a sale event.

    This is an orchestration-level pre-check only.
    The database RPC performs the final authoritative
    validation again before executing the purchase.
    """

    if not isinstance(sale_event, dict):
        raise ValueError("Sale event must be a dictionary")

    if not isinstance(smart_cart_item, dict):
        raise ValueError(
            "Smart Cart item must be a dictionary"
        )

    # --------------------------------------------------
    # 1. Required identifiers
    # --------------------------------------------------

    event_product_id = sale_event.get("product_id")
    item_product_id = smart_cart_item.get("product_id")

    if event_product_id is None:
        return {
            "valid": False,
            "reason": "Sale event has no product ID"
        }

    if item_product_id is None:
        return {
            "valid": False,
            "reason": "Smart Cart item has no product ID"
        }

    # --------------------------------------------------
    # 2. Sale and Smart Cart item must refer
    #    to the same product
    # --------------------------------------------------

    if event_product_id != item_product_id:
        return {
            "valid": False,
            "reason": (
                "Sale event product does not match "
                "Smart Cart item product"
            )
        }

    # --------------------------------------------------
    # 3. Item must still be WATCHING
    # --------------------------------------------------

    if smart_cart_item.get("status") != "WATCHING":
        return {
            "valid": False,
            "reason": (
                "Smart Cart item is not in WATCHING status"
            )
        }

    # --------------------------------------------------
    # 4. Auto-buy must be explicitly enabled
    # --------------------------------------------------

    if smart_cart_item.get("auto_buy_enabled") is not True:
        return {
            "valid": False,
            "reason": "Automatic purchase is not enabled"
        }

    # --------------------------------------------------
    # 5. Explicit purchase authorization must exist
    # --------------------------------------------------

    if not smart_cart_item.get("purchase_authorized_at"):
        return {
            "valid": False,
            "reason": (
                "Automatic purchase has no recorded "
                "authorization timestamp"
            )
        }

    # --------------------------------------------------
    # 6. Maximum price must exist
    # --------------------------------------------------

    maximum_price = smart_cart_item.get("maximum_price")

    if maximum_price is None:
        return {
            "valid": False,
            "reason": "No maximum price has been specified"
        }

    # --------------------------------------------------
    # 7. Sale price must exist
    # --------------------------------------------------

    new_price = sale_event.get("new_price")

    if new_price is None:
        return {
            "valid": False,
            "reason": "Sale event has no new price"
        }

    # Supabase numeric values may arrive as strings,
    # Decimal objects, ints, or floats.
    try:
        new_price_value = float(new_price)
        maximum_price_value = float(maximum_price)
    except (TypeError, ValueError):
        return {
            "valid": False,
            "reason": "Invalid sale or maximum price"
        }

    # --------------------------------------------------
    # 8. Sale price must satisfy customer's limit
    # --------------------------------------------------

    if new_price_value > maximum_price_value:
        return {
            "valid": False,
            "reason": (
                f"Sale price Rs. {new_price_value:.2f} "
                f"is above maximum price "
                f"Rs. {maximum_price_value:.2f}"
            )
        }

    # --------------------------------------------------
    # Candidate passed orchestration-level checks.
    # Final stock, duplicate, price, and status checks
    # still happen inside the atomic database RPC.
    # --------------------------------------------------

    return {
        "valid": True,
        "reason": "Sale candidate is eligible for purchase"
    }