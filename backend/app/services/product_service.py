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

    # First try the normal database search.
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

    products = response.data or []

    if products:
        return products

    # Fallback for natural-language queries such as:
    # "Nike Air Max 270 size 9 black"
    query_words = {
        word.lower()
        for word in query.split()
        if word.strip()
    }

    all_response = (
        supabase
        .table("products")
        .select("*")
        .execute()
    )

    all_products = all_response.data or []

    scored_products = []

    for product in all_products:
        searchable_text = " ".join([
            str(product.get("name") or ""),
            str(product.get("brand") or ""),
            str(product.get("product_type") or ""),
            str(product.get("description") or ""),
        ]).lower()

        score = sum(
            1
            for word in query_words
            if word in searchable_text
        )

        if score >= 2:
            scored_products.append(
                (score, product)
            )

    if not scored_products:
        return []

    scored_products.sort(
        key=lambda item: item[0],
        reverse=True
    )

    best_score = scored_products[0][0]

    return [
        product
        for score, product in scored_products
        if score == best_score
    ]


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