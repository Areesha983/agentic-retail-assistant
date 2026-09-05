from fastapi import APIRouter, HTTPException

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

    try:
        result = create_sale_event(
            product_id=request.product_id,
            new_price=request.new_price
        )

        return {
            "success": True,
            "message": "Sale event created successfully",
            "product": result["product"],
            "sale_event": result["sale_event"]
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get("/{event_id}/matches")
def get_sale_matches(event_id: int):

    try:
        result = find_matching_smart_carts(event_id)

        return {
            "success": True,
            "sale_event": result["sale_event"],
            "matches": result["matches"],
            "match_count": len(result["matches"])
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