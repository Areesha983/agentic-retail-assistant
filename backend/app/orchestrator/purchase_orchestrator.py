from app.orchestrator.validation import validate_sale_candidate
from app.services import purchase_service
from app.services import sale_event_service


def process_sale_event(event_id: int) -> dict:
    """
    Process a sale event and attempt automatic purchases
    for eligible Smart Cart items.

    Flow:
    1. Load sale event and matching Smart Cart items.
    2. Pre-validate each candidate.
    3. Execute eligible purchases through the atomic
       PostgreSQL purchase RPC.
    4. Continue processing other items even if one fails.
    5. Return a summary of all results.
    """

    if type(event_id) is not int:
        raise ValueError(
            "Sale event ID must be an integer"
        )

    if event_id <= 0:
        raise ValueError(
            "Sale event ID must be greater than 0"
        )

    # --------------------------------------------------
    # 1. Load sale event and candidate Smart Cart items
    # --------------------------------------------------

    matching_result = (
        sale_event_service.find_matching_smart_carts(
            event_id
        )
    )

    sale_event = matching_result.get("sale_event")
    matches = matching_result.get("matches") or []

    if not isinstance(sale_event, dict):
        raise RuntimeError(
            "Sale event service returned invalid data"
        )

    results = []

    # --------------------------------------------------
    # 2. Process each Smart Cart candidate independently
    # --------------------------------------------------

    for item in matches:

        item_id = item.get("item_id")

        if type(item_id) is not int or item_id <= 0:
            results.append({
                "item_id": item_id,
                "success": False,
                "stage": "VALIDATION",
                "reason": (
                    "Smart Cart item has an invalid item ID"
                )
            })
            continue

        # ----------------------------------------------
        # Orchestrator pre-validation
        # ----------------------------------------------

        validation = validate_sale_candidate(
            sale_event=sale_event,
            smart_cart_item=item
        )

        if not validation["valid"]:
            results.append({
                "item_id": item_id,
                "success": False,
                "stage": "VALIDATION",
                "reason": validation["reason"]
            })
            continue

        # ----------------------------------------------
        # Atomic purchase
        #
        # The database RPC performs the final
        # authoritative checks again.
        # ----------------------------------------------

        try:
            purchase_result = (
                purchase_service.execute_purchase(
                    item_id
                )
            )

            results.append({
                "item_id": item_id,
                "success": True,
                "stage": "PURCHASE",
                "reason": (
                    "Automatic purchase completed"
                ),
                "purchase": purchase_result
            })

        except (ValueError, RuntimeError) as exc:
            results.append({
                "item_id": item_id,
                "success": False,
                "stage": "PURCHASE",
                "reason": str(exc)
            })

        except Exception as exc:
            # One failed item should not prevent other
            # eligible Smart Cart items from being processed.
            results.append({
                "item_id": item_id,
                "success": False,
                "stage": "PURCHASE",
                "reason": (
                    "Unexpected purchase error: "
                    f"{exc}"
                )
            })

    # --------------------------------------------------
    # 3. Build summary
    # --------------------------------------------------

    successful = sum(
        1
        for result in results
        if result["success"] is True
    )

    failed = len(results) - successful

    return {
        "success": failed == 0,
        "event_id": event_id,
        "product_id": sale_event.get("product_id"),
        "sale_price": sale_event.get("new_price"),
        "candidate_count": len(matches),
        "processed_count": len(results),
        "successful_purchases": successful,
        "failed_purchases": failed,
        "results": results
    }