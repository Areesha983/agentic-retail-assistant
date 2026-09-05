from app.database.supabase import supabase


def create_support_request(
    user_id: str,
    message: str,
    reason: str | None,
    priority: str
):
    allowed_priorities = ["LOW", "MEDIUM", "HIGH", "URGENT"]

    if priority not in allowed_priorities:
        raise ValueError("Invalid priority")

    response = (
        supabase
        .table("support_requests")
        .insert({
            "user_id": user_id,
            "message": message,
            "reason": reason,
            "priority": priority,
            "status": "OPEN"
        })
        .execute()
    )

    if not response.data:
        raise ValueError("Failed to create support request")

    return response.data[0]


def get_support_requests(user_id: str):
    response = (
        supabase
        .table("support_requests")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )

    return response.data


def update_support_request(
    request_id: int,
    status: str,
    resolution: str | None
):
    allowed_statuses = [
        "OPEN",
        "IN_PROGRESS",
        "RESOLVED",
        "CANCELLED"
    ]

    if status not in allowed_statuses:
        raise ValueError("Invalid support status")

    response = (
        supabase
        .table("support_requests")
        .update({
            "status": status,
            "resolution": resolution
        })
        .eq("request_id", request_id)
        .execute()
    )

    if not response.data:
        raise ValueError("Support request not found")

    return response.data[0]