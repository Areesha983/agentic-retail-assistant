from typing import Optional

from app.database.supabase import supabase


def get_inventory(
    product_id: Optional[int] = None,
    variant: Optional[str] = None,
    color: Optional[str] = None,
    branch: Optional[str] = None,
):
    """
    Return inventory records using optional filters.
    """

    query = (
        supabase
        .table("inventory")
        .select("*")
    )

    if product_id is not None:
        query = query.eq("product_id", product_id)

    if variant:
        query = query.ilike("variant", variant.strip())

    if color:
        query = query.ilike("color", color.strip())

    if branch:
        query = query.ilike("branch", branch.strip())

    response = query.execute()

    return response.data or []