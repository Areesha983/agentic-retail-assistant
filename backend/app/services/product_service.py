from app.database.supabase import supabase


def list_products():
    response = (
        supabase
        .table("products")
        .select("*")
        .execute()
    )

    return response.data or []


def search_products(query: str):
    query = query.strip()

    if not query:
        raise ValueError("Product search query cannot be empty")

    response = (
        supabase
        .table("products")
        .select("*")
        .or_(
            f"name.ilike.%{query}%,"
            f"brand.ilike.%{query}%,"
            f"product_type.ilike.%{query}%"
        )
        .execute()
    )

    return response.data or []


def get_product_details(product_id: int):
    response = (
        supabase
        .table("products")
        .select("*")
        .eq("product_id", product_id)
        .execute()
    )

    if not response.data:
        raise ValueError("Product not found")

    return response.data[0]