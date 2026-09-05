import pytest

from app.tools import support_tools


def test_create_support_request(monkeypatch):
    fake_request = {
        "request_id": 1,
        "user_id": "user-123",
        "message": "My order has an issue",
        "reason": "ORDER",
        "priority": "HIGH",
        "status": "OPEN"
    }

    def fake_create(**kwargs):
        assert kwargs["user_id"] == "user-123"
        assert kwargs["message"] == "My order has an issue"
        assert kwargs["priority"] == "HIGH"
        return fake_request

    monkeypatch.setattr(
        support_tools.support_service,
        "create_support_request",
        fake_create
    )

    result = support_tools.create_support_request(
        user_id="user-123",
        message="My order has an issue",
        reason="ORDER",
        priority="high"
    )

    assert result["success"] is True
    assert result["request"] == fake_request


def test_create_support_rejects_empty_message():
    with pytest.raises(
        ValueError,
        match="message cannot be empty"
    ):
        support_tools.create_support_request(
            user_id="user-123",
            message="   "
        )


def test_create_support_rejects_invalid_priority():
    with pytest.raises(
        ValueError,
        match="Invalid priority"
    ):
        support_tools.create_support_request(
            user_id="user-123",
            message="Help",
            priority="SUPER_HIGH"
        )


def test_view_support_requests(monkeypatch):
    fake_requests = [
        {
            "request_id": 1,
            "status": "OPEN"
        },
        {
            "request_id": 2,
            "status": "RESOLVED"
        }
    ]

    monkeypatch.setattr(
        support_tools.support_service,
        "get_support_requests",
        lambda user_id: fake_requests
    )

    result = support_tools.view_support_requests("user-123")

    assert result["success"] is True
    assert result["count"] == 2
    assert result["requests"] == fake_requests


def test_update_support_request(monkeypatch):
    fake_request = {
        "request_id": 1,
        "status": "RESOLVED",
        "resolution": "Refund processed"
    }

    monkeypatch.setattr(
        support_tools.support_service,
        "update_support_request",
        lambda **kwargs: fake_request
    )

    result = support_tools.update_support_request(
        request_id=1,
        status="resolved",
        resolution="Refund processed"
    )

    assert result["success"] is True
    assert result["request"]["status"] == "RESOLVED"


def test_update_support_rejects_invalid_status():
    with pytest.raises(
        ValueError,
        match="Invalid support status"
    ):
        support_tools.update_support_request(
            request_id=1,
            status="UNKNOWN"
        )