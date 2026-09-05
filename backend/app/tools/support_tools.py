from typing import Optional

from app.services import support_service


ALLOWED_PRIORITIES = ["LOW", "MEDIUM", "HIGH", "URGENT"]

ALLOWED_STATUSES = [
    "OPEN",
    "IN_PROGRESS",
    "RESOLVED",
    "CANCELLED"
]


def create_support_request(
    user_id: str,
    message: str,
    reason: Optional[str] = None,
    priority: str = "MEDIUM",
):
    """
    Controlled agent tool for creating a customer support request.
    """

    if not isinstance(user_id, str) or not user_id.strip():
        raise ValueError("User ID cannot be empty")

    if not isinstance(message, str) or not message.strip():
        raise ValueError("Support message cannot be empty")

    if not isinstance(priority, str):
        raise ValueError("Priority must be a string")

    priority = priority.strip().upper()

    if priority not in ALLOWED_PRIORITIES:
        raise ValueError("Invalid priority")

    if reason is not None:
        if not isinstance(reason, str):
            raise ValueError("Reason must be a string")
        reason = reason.strip() or None

    request = support_service.create_support_request(
        user_id=user_id.strip(),
        message=message.strip(),
        reason=reason,
        priority=priority
    )

    return {
        "success": True,
        "request": request
    }


def view_support_requests(user_id: str):
    """
    Controlled agent tool for viewing a user's support requests.
    """

    if not isinstance(user_id, str) or not user_id.strip():
        raise ValueError("User ID cannot be empty")

    requests = support_service.get_support_requests(
        user_id.strip()
    )

    return {
        "success": True,
        "count": len(requests or []),
        "requests": requests or []
    }


def update_support_request(
    request_id: int,
    status: str,
    resolution: Optional[str] = None,
):
    """
    Controlled agent tool for updating a support request.
    """

    if type(request_id) is not int or request_id <= 0:
        raise ValueError("Request ID must be a positive integer")

    if not isinstance(status, str):
        raise ValueError("Status must be a string")

    status = status.strip().upper()

    if status not in ALLOWED_STATUSES:
        raise ValueError("Invalid support status")

    if resolution is not None:
        if not isinstance(resolution, str):
            raise ValueError("Resolution must be a string")
        resolution = resolution.strip() or None

    request = support_service.update_support_request(
        request_id=request_id,
        status=status,
        resolution=resolution
    )

    return {
        "success": True,
        "request": request
    }