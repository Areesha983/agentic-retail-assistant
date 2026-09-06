from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

class UpdateOrderStatusRequest(BaseModel):
    status: str

from app.services.order_service import (
    get_orders_by_user,
    get_order_by_id,
    update_order_status,
    cancel_order
)

router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)


@router.get("/{user_id}")
def get_user_orders(user_id: int):
    try:
        orders = get_orders_by_user(user_id)

        return {
            "success": True,
            "orders": orders
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get("/id/{order_id}")
def get_order(order_id: int):
    try:
        order = get_order_by_id(order_id)

        return {
            "success": True,
            "order": order
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

@router.patch("/id/{order_id}/status")
def update_status(
    order_id: int,
    request: UpdateOrderStatusRequest
):
    try:
        order = update_order_status(
            order_id,
            request.status
        )

        return {
            "success": True,
            "order": order
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

@router.patch("/id/{order_id}/cancel")
def cancel_order_api(order_id: int):
    try:
        order = cancel_order(order_id)

        return {
            "success": True,
            "message": "Order cancelled successfully",
            "order": order
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