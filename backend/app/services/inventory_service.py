from typing import Optional

from app.database.supabase import supabase


def normalize_variant(variant: Optional[str]) -> Optional[str]:
    if variant is None:
        return None

    variant = variant.strip()

    if not variant:
        return None

    # Convert "9" → "Size 9"
    if variant.replace(".", "", 1).isdigit():
        return f"Size {variant}"

    return variant


def get_inventory(
    product_id: Optional[int] = None,
    variant: Optional[str] = None,
    color: Optional[str] = None,
    branch: Optional[str] = None,
):
    query = (
        supabase
        .table("inventory")
        .select("*")
    )

    if product_id is not None:
        query = query.eq("product_id", product_id)

    variant = normalize_variant(variant)

    if variant:
        query = query.ilike("variant", variant)

    if color:
        query = query.ilike("color", color.strip())

    if branch:
        query = query.ilike("branch", branch.strip())

    response = query.execute()

    return response.data or []