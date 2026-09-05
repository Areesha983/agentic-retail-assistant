from app.services import product_service


def search_products(query: str):
    if not isinstance(query, str):
        raise ValueError("Query must be a string")

    query = query.strip()

    if not query:
        raise ValueError("Product search query cannot be empty")

    products = product_service.search_products(query)

    return {
        "success": True,
        "query": query,
        "count": len(products),
        "products": products
    }


def get_product_details(product_id: int):
    if not isinstance(product_id, int):
        raise ValueError("Product ID must be an integer")

    if product_id <= 0:
        raise ValueError("Product ID must be greater than 0")

    return {
        "success": True,
        "product": product_service.get_product_details(product_id)
    }