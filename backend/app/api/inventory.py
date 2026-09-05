from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.database.supabase import supabase


router = APIRouter(
    prefix="/inventory",
    tags=["Inventory"]
)


@router.get("/")
def get_inventory(
    product_id: Optional[str] = Query(
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
        query = (
            supabase
            .table("inventory")
            .select("*")
        )

        if product_id:
            query = query.eq("product_id", product_id)

        if variant:
            query = query.ilike("variant", variant)

        if color:
            query = query.ilike("color", color)

        if branch:
            query = query.ilike("branch", branch)

        response = query.execute()

        return {
            "success": True,
            "inventory": response.data
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )