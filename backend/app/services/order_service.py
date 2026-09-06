from app.database.supabase import supabase


def get_orders_by_user(user_id: int):
    response = (
        supabase
        .table("orders")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )

    return response.data


def get_order_by_id(order_id: int):
    response = (
        supabase
        .table("orders")
        .select("*")
        .eq("order_id", order_id)
        .execute()
    )

    if not response.data:
        raise ValueError("Order not found")

    return response.data[0]
def update_order_status(order_id: int, status: str):
    allowed_statuses = [
        "CONFIRMED",
        "PROCESSING",
        "COMPLETED",
        "CANCELLED",
        "FAILED"
    ]

    if status not in allowed_statuses:
        raise ValueError("Invalid order status")

    response = (
        supabase
        .table("orders")
        .update({
            "status": status
        })
        .eq("order_id", order_id)
        .execute()
    )

    if not response.data:
        raise ValueError("Order not found")

    return response.data[0]

def cancel_order(order_id: int):
    response = (
        supabase
        .table("orders")
        .select("*")
        .eq("order_id", order_id)
        .execute()
    )

    if not response.data:
        raise ValueError("Order not found")

    order = response.data[0]

    if order["status"] not in ["CONFIRMED", "PROCESSING"]:
        raise ValueError(
            f"Order cannot be cancelled because its status is {order['status']}"
        )

    update_response = (
        supabase
        .table("orders")
        .update({
            "status": "CANCELLED"
        })
        .eq("order_id", order_id)
        .execute()
    )

    if not update_response.data:
        raise ValueError("Failed to cancel order")

    return update_response.data[0]