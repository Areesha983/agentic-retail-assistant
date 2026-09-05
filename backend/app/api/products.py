from fastapi import APIRouter, HTTPException, Query

from app.services.product_service import (
    list_products,
    search_products as search_products_service,
)


router = APIRouter(
    prefix="/products",
    tags=["Products"]
)


@router.get("/")
def get_products():
    try:
        return {
            "success": True,
            "products": list_products()
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get("/search")
def search_products(
    q: str = Query(..., min_length=1)
):
    try:
        return {
            "success": True,
            "query": q,
            "products": search_products_service(q)
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