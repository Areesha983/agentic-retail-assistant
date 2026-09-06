from app.database.supabase import supabase


def save_message(
    user_id: int,
    role: str,
    content: str
):
    if type(user_id) is not int or user_id <= 0:
        raise ValueError("User ID must be a positive integer")

    if role not in ["user", "assistant"]:
        raise ValueError("Invalid conversation role")

    content = content.strip()

    if not content:
        raise ValueError("Message content cannot be empty")

    response = (
        supabase
        .table("conversation_messages")
        .insert({
            "user_id": user_id,
            "role": role,
            "content": content
        })
        .execute()
    )

    if not response.data:
        raise ValueError(
            "Failed to save conversation message"
        )

    return response.data[0]


def get_recent_messages(
    user_id: int,
    limit: int = 10
):
    if type(user_id) is not int or user_id <= 0:
        raise ValueError("User ID must be a positive integer")

    if limit <= 0:
        raise ValueError(
            "Message limit must be greater than zero"
        )

    response = (
        supabase
        .table("conversation_messages")
        .select("role, content, created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )

    messages = response.data or []

    # Database returns newest first.
    # The LLM needs chronological order.
    messages.reverse()

    return messages