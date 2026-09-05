from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.services.inventory_service import get_inventory as get_inventory_service


router = APIRouter(
    prefix="/inventory",
    tags=["Inventory"]
)


@router.get("/")
def get_inventory(
    product_id: Optional[int] = Query(
        None,
        description="Product ID"
    ),
    variant: Optional[str] = Query(
        None,
        description="Product variant, e.g. Size 9 or Medium"
    ),
    color: Optional[str] = Query(
        None,
        description="Product color"
    ),
    branch: Optional[str] = Query(
        None,
        description="Store branch"
    )
):
    try:
        inventory = get_inventory_service(
            product_id=product_id,
            variant=variant,
            color=color,
            branch=branch
        )

        return {
            "success": True,
            "inventory": inventory
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )