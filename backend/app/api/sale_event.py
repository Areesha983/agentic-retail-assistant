from fastapi import APIRouter, HTTPException

from app.orchestrator.purchase_orchestrator import (
    process_sale_event
)
from app.schemas.sale_event import CreateSaleEventRequest
from app.services.sale_event_service import (
    create_sale_event,
    find_matching_smart_carts
)


router = APIRouter(
    prefix="/sale-events",
    tags=["Sale Events"]
)


@router.post("/")
def create_sale(request: CreateSaleEventRequest):
    """
    Create a sale event and immediately process eligible
    Smart Cart items for automatic purchase.
    """

    try:
        # ----------------------------------------------
        # 1. Create the sale event and update product price
        # ----------------------------------------------

        result = create_sale_event(
            product_id=request.product_id,
            new_price=request.new_price
        )

        sale_event = result["sale_event"]
        event_id = sale_event["event_id"]

        # ----------------------------------------------
        # 2. Trigger Phase 21 purchase orchestrator
        # ----------------------------------------------

        orchestration = process_sale_event(
            event_id
        )

        return {
            "success": True,
            "message": (
                "Sale event created and processed successfully"
            ),
            "product": result["product"],
            "sale_event": sale_event,
            "orchestration": orchestration
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except RuntimeError as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.post("/{event_id}/process")
def process_existing_sale_event(event_id: int):
    """
    Manually re-run the purchase orchestrator for an
    existing sale event.

    Duplicate protection in the purchase transaction
    prevents a second order from being created.
    """

    try:
        result = process_sale_event(
            event_id
        )

        return {
            "success": True,
            "orchestration": result
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except RuntimeError as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get("/{event_id}/matches")
def get_sale_matches(event_id: int):
    """
    View Smart Cart items that match an existing
    sale event.
    """

    try:
        result = find_matching_smart_carts(
            event_id
        )

        return {
            "success": True,
            "sale_event": result["sale_event"],
            "matches": result["matches"],
            "match_count": len(
                result["matches"]
            )
        }

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )