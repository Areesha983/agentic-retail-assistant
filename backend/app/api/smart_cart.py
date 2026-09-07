from fastapi import APIRouter, HTTPException

from app.schemas.smart_cart import (
    CreateSmartCartRequest,
    AddSmartCartItemRequest
)

from app.services.smart_cart_service import (
    create_smart_cart,
    add_item_to_smart_cart,
    get_smart_cart,
    cancel_smart_cart_item,
    get_smart_carts_by_user
)


router = APIRouter(
    prefix="/smart-cart",
    tags=["Smart Cart"]
)


@router.post("/")
def create_cart(request: CreateSmartCartRequest):
    try:
        cart = create_smart_cart(request.user_id)

        return {
            "success": True,
            "cart": cart
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.post("/items/")
def add_item(request: AddSmartCartItemRequest):
    try:
        item = add_item_to_smart_cart(
            cart_id=request.cart_id,
            product_id=request.product_id,
            variant=request.variant,
            color=request.color,
            quantity=request.quantity,
            maximum_price=request.maximum_price,
            auto_buy_enabled=request.auto_buy_enabled
        )

        return {
            "success": True,
            "item": item
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

@router.get("/{cart_id}")
def get_cart(cart_id: int):
    try:
        result = get_smart_cart(cart_id)

        return {
            "success": True,
            "cart": result["cart"],
            "items": result["items"]
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

@router.patch("/items/{item_id}/cancel")
def cancel_item(item_id: int):

    try:

        item = cancel_smart_cart_item(item_id)

        return {
            "success": True,
            "message": "Smart Cart item cancelled successfully",
            "item": item
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

@router.get("/user/{user_id}")
def get_user_smart_carts(user_id: int):
    """
    Get all Smart Carts belonging to a customer.
    """

    try:
        carts = get_smart_carts_by_user(
            user_id
        )

        return {
            "success": True,
            "count": len(carts),
            "carts": carts
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