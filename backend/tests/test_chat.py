from fastapi.testclient import TestClient

from app.main import app
from app.api import chat as chat_api


client = TestClient(app)


def test_chat_endpoint(monkeypatch):
    def fake_run_agent(message, user_id):
        assert message == "Find Nike Air Max"
        assert user_id == 1001

        return {
            "success": True,
            "reply": "I found the Nike Air Max 270.",
            "tool_history": [
                {
                    "tool": "search_products",
                    "arguments": {
                        "query": "Nike Air Max"
                    },
                    "result": {
                        "success": True,
                        "count": 1
                    }
                }
            ]
        }

    monkeypatch.setattr(
        chat_api,
        "run_agent",
        fake_run_agent
    )

    response = client.post(
        "/chat/",
        json={
            "user_id": 1001,
            "message": "Find Nike Air Max"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["reply"] == (
        "I found the Nike Air Max 270."
    )
    assert (
        data["tool_history"][0]["tool"]
        == "search_products"
    )


def test_chat_rejects_blank_message(monkeypatch):
    def fake_run_agent(message, user_id):
        assert user_id == 1001

        raise ValueError(
            "User message cannot be empty"
        )

    monkeypatch.setattr(
        chat_api,
        "run_agent",
        fake_run_agent
    )

    response = client.post(
        "/chat/",
        json={
            "user_id": 1001,
            "message": "   "
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "User message cannot be empty"
    )


def test_chat_requires_message():
    response = client.post(
        "/chat/",
        json={
            "user_id": 1001
        }
    )

    assert response.status_code == 422


def test_chat_requires_user_id():
    response = client.post(
        "/chat/",
        json={
            "message": "Find Nike Air Max"
        }
    )

    assert response.status_code == 422