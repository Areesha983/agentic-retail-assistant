from fastapi import APIRouter, HTTPException

from app.schemas.purchase import (
    ValidatePurchaseRequest,
    ExecutePurchaseRequest
)

from app.services.purchase_service import (
    validate_purchase,
    execute_purchase,
    get_purchase_attempts
)


router = APIRouter(
    prefix="/purchase",
    tags=["Purchase"]
)


@router.post("/validate")
def validate_purchase_api(
    request: ValidatePurchaseRequest
):

    try:

        result = validate_purchase(
            smart_cart_item_id=request.smart_cart_item_id
        )

        return {
            "success": True,
            **result
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


@router.post("/execute")
def execute_purchase_api(
    request: ExecutePurchaseRequest
):

    try:

        result = execute_purchase(
            smart_cart_item_id=request.smart_cart_item_id
        )

        return result

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

@router.get("/attempts/{smart_cart_item_id}")
def get_attempts(smart_cart_item_id: int):
    try:
        attempts = get_purchase_attempts(smart_cart_item_id)

        return {
            "success": True,
            "attempts": attempts
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )