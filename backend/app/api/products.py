from fastapi import APIRouter, HTTPException, Query

from app.database.supabase import supabase


router = APIRouter(
    prefix="/products",
    tags=["Products"]
)


@router.get("/")
def get_products():
    try:
        response = (
            supabase
            .table("products")
            .select("*")
            .execute()
        )

        return {
            "success": True,
            "products": response.data
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get("/search")
def search_products(
    q: str = Query(..., min_length=1, description="Product search query")
):
    try:
        response = (
            supabase
            .table("products")
            .select("*")
            .or_(
                f"name.ilike.%{q}%,"
                f"brand.ilike.%{q}%,"
                f"product_type.ilike.%{q}%"
            )
            .execute()
        )

        return {
            "success": True,
            "query": q,
            "products": response.data
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )