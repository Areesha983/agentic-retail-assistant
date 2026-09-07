from fastapi.testclient import TestClient

from app.main import app
from app.api import chat as chat_api
from app.agents.agent import run_agent


client = TestClient(app)


# =========================================================
# Fake Ollama response helpers
# =========================================================

class FakeToolFunction:
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments


class FakeToolCall:
    def __init__(self, name, arguments):
        self.function = FakeToolFunction(
            name,
            arguments
        )


class FakeMessage:
    def __init__(self, content="", tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls


class FakeResponse:
    def __init__(self, content="", tool_calls=None):
        self.message = FakeMessage(
            content=content,
            tool_calls=tool_calls
        )


class FakeChat:
    def __init__(self, responses):
        self.responses = responses
        self.index = 0

    def __call__(self, *args, **kwargs):
        if self.index >= len(self.responses):
            raise AssertionError(
                "FakeChat received more calls than expected."
            )

        response = self.responses[self.index]
        self.index += 1

        return response


# =========================================================
# Fake tool executor
# =========================================================

def fake_execute_tool(tool_name, **arguments):
    """
    Mock the agent tool layer so these tests do not access
    Supabase or any real backend service.
    """

    # -----------------------------------------------------
    # Product search
    # -----------------------------------------------------

    if tool_name == "search_products":
        return {
            "success": True,
            "count": 1,
            "products": [
                {
                    "product_id": 1,
                    "name": "Nike Air Max 270",
                    "brand": "Nike",
                    "category": "Shoes",
                    "price": 19000
                }
            ]
        }

    # -----------------------------------------------------
    # Product details
    # -----------------------------------------------------

    if tool_name == "get_product_details":
        return {
            "success": True,
            "product": {
                "product_id": 1,
                "name": "Nike Air Max 270",
                "brand": "Nike",
                "category": "Shoes",
                "price": 19000
            }
        }

    # -----------------------------------------------------
    # Inventory
    # -----------------------------------------------------

    if tool_name == "check_inventory":
        return {
            "success": True,
            "product_id": arguments.get("product_id"),
            "inventory": [
                {
                    "inventory_id": 1,
                    "product_id": 1,
                    "variant": "Size 9",
                    "color": "Black",
                    "branch": "Dolmen",
                    "quantity": 3
                }
            ]
        }

    # -----------------------------------------------------
    # Availability
    # -----------------------------------------------------

    if tool_name == "check_availability":
        return {
            "success": True,
            "product_id": arguments.get("product_id"),
            "available": True,
            "inventory": [
                {
                    "variant": "Size 9",
                    "color": "Black",
                    "branch": "Dolmen",
                    "quantity": 3
                }
            ]
        }

    # -----------------------------------------------------
    # Create Smart Cart
    # -----------------------------------------------------

    if tool_name == "create_smart_cart":
        return {
            "success": True,
            "cart": {
                "cart_id": 1,
                "user_id": arguments.get("user_id"),
                "status": "ACTIVE"
            }
        }

    # -----------------------------------------------------
    # Add to Smart Cart
    # -----------------------------------------------------

    if tool_name == "add_to_smart_cart":
        return {
            "success": True,
            "message": "Product added to Smart Cart.",
            "item": {
                "item_id": 1,
                "cart_id": arguments.get("cart_id"),
                "product_id": arguments.get("product_id"),
                "quantity": arguments.get(
                    "quantity",
                    1
                ),
                "variant": arguments.get("variant"),
                "color": arguments.get("color"),
                "maximum_price": arguments.get(
                    "maximum_price"
                ),
                "auto_buy_enabled": arguments.get(
                    "auto_buy_enabled",
                    False
                ),
                "status": "WATCHING"
            }
        }

    # -----------------------------------------------------
    # View Smart Cart
    # -----------------------------------------------------

    if tool_name == "view_smart_cart":
        return {
            "success": True,
            "cart": {
                "cart_id": arguments.get("cart_id"),
                "status": "ACTIVE"
            },
            "items": []
        }

    # -----------------------------------------------------
    # Cancel Smart Cart item
    # -----------------------------------------------------

    if tool_name == "cancel_smart_cart_item":
        return {
            "success": True,
            "message": "Smart Cart item cancelled.",
            "item": {
                "item_id": arguments.get("item_id"),
                "status": "CANCELLED"
            }
        }

    # -----------------------------------------------------
    # Purchase validation
    # -----------------------------------------------------

    if tool_name == "validate_purchase":
        return {
            "success": True,
            "valid": True,
            "message": "Purchase validated."
        }

    # -----------------------------------------------------
    # Purchase execution
    # -----------------------------------------------------

    if tool_name == "execute_purchase":
        return {
            "success": True,
            "message": "Purchase completed.",
            "order": {
                "order_id": 1,
                "status": "CONFIRMED"
            }
        }

    # -----------------------------------------------------
    # Support request
    # -----------------------------------------------------

    if tool_name == "create_support_request":
        return {
            "success": True,
            "request": {
                "request_id": 1,
                "user_id": arguments.get("user_id"),
                "status": "OPEN"
            }
        }

    # -----------------------------------------------------
    # View support requests
    # -----------------------------------------------------

    if tool_name == "view_support_requests":
        return {
            "success": True,
            "requests": []
        }

    # -----------------------------------------------------
    # Update support request
    # -----------------------------------------------------

    if tool_name == "update_support_request":
        return {
            "success": True,
            "request": {
                "request_id": arguments.get(
                    "request_id"
                ),
                "status": arguments.get(
                    "status",
                    "OPEN"
                )
            }
        }

    raise AssertionError(
        f"Unexpected tool called: {tool_name}"
    )


# =========================================================
# Chat API tests
# =========================================================

def test_chat_endpoint(monkeypatch):

    def fake_get_recent_messages(user_id, limit=10):
        assert user_id == 1001
        assert limit == 10

        return []

    def fake_save_message(user_id, role, content):
        assert user_id == 1001

        if role == "user":
            assert content == "Find Nike Air Max"

        elif role == "assistant":
            assert content == (
                "I found the Nike Air Max 270."
            )

        return {
            "message_id": 1,
            "user_id": user_id,
            "role": role,
            "content": content
        }

    def fake_run_agent(
        message,
        user_id,
        conversation_history=None
    ):
        assert message == "Find Nike Air Max"
        assert user_id == 1001
        assert conversation_history == []

        return {
            "success": True,
            "reply": (
                "I found the Nike Air Max 270."
            ),
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
        "get_recent_messages",
        fake_get_recent_messages
    )

    monkeypatch.setattr(
        chat_api,
        "save_message",
        fake_save_message
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

    def fail_if_called(*args, **kwargs):
        raise AssertionError(
            "This function should not be called "
            "for a blank message"
        )

    monkeypatch.setattr(
        chat_api,
        "get_recent_messages",
        fail_if_called
    )

    monkeypatch.setattr(
        chat_api,
        "save_message",
        fail_if_called
    )

    monkeypatch.setattr(
        chat_api,
        "run_agent",
        fail_if_called
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


# =========================================================
# Conversation context tests
# =========================================================

def test_chat_context_across_messages(monkeypatch):

    responses = [
        # -------------------------------------------------
        # First message -> search
        # -------------------------------------------------

        FakeResponse(
            content="",
            tool_calls=[
                FakeToolCall(
                    "search_products",
                    {
                        "query": "Nike Air Max 270"
                    }
                )
            ]
        ),

        # -------------------------------------------------
        # First message -> final answer
        # -------------------------------------------------

        FakeResponse(
            content=(
                "I found the Nike Air Max 270. "
                "It is currently Rs. 19,000."
            )
        ),

        # -------------------------------------------------
        # Second message -> "What is its price?" now requires
        # verification (widened is_product_search_request).
        # known_product_ids resets per run, so the product must
        # be re-resolved via search_products even though it was
        # already mentioned in conversation_history.
        # -------------------------------------------------

        FakeResponse(
            content="",
            tool_calls=[
                FakeToolCall(
                    "search_products",
                    {
                        "query": "Nike Air Max 270"
                    }
                )
            ]
        ),

        # -------------------------------------------------
        # Second message -> fetch a FRESH price using the
        # newly-verified product_id, rather than reusing the
        # price mentioned in the earlier assistant reply.
        # -------------------------------------------------

        FakeResponse(
            content="",
            tool_calls=[
                FakeToolCall(
                    "get_product_details",
                    {
                        "product_id": 1
                    }
                )
            ]
        ),

        # -------------------------------------------------
        # Second message -> final answer, grounded in the
        # get_product_details result above.
        # -------------------------------------------------

        FakeResponse(
            content=(
                "The Nike Air Max 270 is currently "
                "Rs. 19,000."
            )
        )
    ]

    fake_chat = FakeChat(responses)

    monkeypatch.setattr(
        "app.agents.agent.chat",
        fake_chat
    )

    monkeypatch.setattr(
        "app.agents.agent.execute_tool",
        fake_execute_tool
    )

    history = []

    # -----------------------------------------------------
    # First conversation
    # -----------------------------------------------------

    first = run_agent(
        user_id=1,
        user_message=(
            "Tell me about Nike Air Max 270"
        ),
        conversation_history=history
    )

    assert first["success"] is True

    assert (
        "Nike Air Max 270"
        in first["reply"]
    )

    # -----------------------------------------------------
    # Persist conversation
    # -----------------------------------------------------

    history.append(
        {
            "role": "user",
            "content": (
                "Tell me about Nike Air Max 270"
            )
        }
    )

    history.append(
        {
            "role": "assistant",
            "content": first["reply"]
        }
    )

    # -----------------------------------------------------
    # Second conversation
    # -----------------------------------------------------

    second = run_agent(
        user_id=1,
        user_message="What is its price?",
        conversation_history=history
    )

    assert second["success"] is True

    assert "19,000" in second["reply"]

    # -----------------------------------------------------
    # Verify the price answer was grounded in fresh tool
    # calls, not reused from stale conversation text.
    # -----------------------------------------------------

    tool_names = [
        entry["tool"]
        for entry in second["tool_history"]
    ]

    assert "search_products" in tool_names

    assert "get_product_details" in tool_names

    detail_calls = [
        entry
        for entry in second["tool_history"]
        if entry["tool"] == "get_product_details"
    ]

    assert len(detail_calls) == 1

    assert (
        detail_calls[0]["arguments"]["product_id"]
        == 1
    )

# =========================================================
# Previous product context
# =========================================================

def test_agent_uses_previous_product_context(
    monkeypatch
):

    responses = [
        # -------------------------------------------------
        # First conversation -> search product
        # -------------------------------------------------

        FakeResponse(
            content="",
            tool_calls=[
                FakeToolCall(
                    "search_products",
                    {
                        "query": "Nike Air Max 270"
                    }
                )
            ]
        ),

        # -------------------------------------------------
        # First conversation -> final answer
        # -------------------------------------------------

        FakeResponse(
            content=(
                "The Nike Air Max 270 costs "
                "Rs. 19,000."
            )
        ),

        # -------------------------------------------------
        # Second conversation -> resolve product
        # -------------------------------------------------

        FakeResponse(
            content="",
            tool_calls=[
                FakeToolCall(
                    "search_products",
                    {
                        "query": "Nike Air Max 270"
                    }
                )
            ]
        ),

        # -------------------------------------------------
        # Second conversation -> check inventory
        # -------------------------------------------------

        FakeResponse(
            content="",
            tool_calls=[
                FakeToolCall(
                    "check_inventory",
                    {
                        "product_id": 1
                    }
                )
            ]
        ),

        # -------------------------------------------------
        # Second conversation -> final answer
        # -------------------------------------------------

        FakeResponse(
            content=(
                "The Nike Air Max 270 is available "
                "in size 9."
            )
        )
    ]

    fake_chat = FakeChat(responses)

    monkeypatch.setattr(
        "app.agents.agent.chat",
        fake_chat
    )

    monkeypatch.setattr(
        "app.agents.agent.execute_tool",
        fake_execute_tool
    )

    history = []

    # =====================================================
    # Conversation 1
    # =====================================================

    first = run_agent(
        user_id=1,
        user_message=(
            "Tell me about Nike Air Max 270"
        ),
        conversation_history=history
    )

    assert first["success"] is True

    assert (
        "Nike Air Max 270"
        in first["reply"]
    )

    # -----------------------------------------------------
    # Persist conversation
    # -----------------------------------------------------

    history.extend(
        [
            {
                "role": "user",
                "content": (
                    "Tell me about Nike Air Max 270"
                )
            },
            {
                "role": "assistant",
                "content": first["reply"]
            }
        ]
    )

    # =====================================================
    # Conversation 2
    # =====================================================

    second = run_agent(
        user_id=1,
        user_message=(
            "What size 9 options do you have?"
        ),
        conversation_history=history
    )

    assert second["success"] is True

    assert "size 9" in second["reply"].lower()

    # -----------------------------------------------------
    # Verify product was resolved again
    # -----------------------------------------------------

    tool_names = [
        entry["tool"]
        for entry in second["tool_history"]
    ]

    assert "search_products" in tool_names

    # -----------------------------------------------------
    # Verify inventory was checked
    # -----------------------------------------------------

    assert "check_inventory" in tool_names

    inventory_calls = [
        entry
        for entry in second["tool_history"]
        if entry["tool"] == "check_inventory"
    ]

    assert len(inventory_calls) == 1

    assert (
        inventory_calls[0]["arguments"]["product_id"]
        == 1
    )

    # -----------------------------------------------------
    # Verify product search used previous context
    # -----------------------------------------------------

    search_calls = [
        entry
        for entry in second["tool_history"]
        if entry["tool"] == "search_products"
    ]

    assert len(search_calls) == 1

    assert (
        search_calls[0]["arguments"]["query"]
        == "Nike Air Max 270"
    )


# =========================================================
# Smart Cart + previous product context
# =========================================================

def test_smart_cart_uses_previous_product_context(
    monkeypatch
):

    responses = [
        # -------------------------------------------------
        # Conversation 1:
        # Search product
        # -------------------------------------------------

        FakeResponse(
            content="",
            tool_calls=[
                FakeToolCall(
                    "search_products",
                    {
                        "query": "Nike Air Max 270"
                    }
                )
            ]
        ),

        # -------------------------------------------------
        # Conversation 1:
        # Final response
        # -------------------------------------------------

        FakeResponse(
            content=(
                "I found the Nike Air Max 270."
            )
        ),

        # -------------------------------------------------
        # Conversation 2:
        # Agent resolves previous product
        # -------------------------------------------------

        FakeResponse(
            content="",
            tool_calls=[
                FakeToolCall(
                    "search_products",
                    {
                        "query": "Nike Air Max 270"
                    }
                )
            ]
        ),

        # -------------------------------------------------
        # Agent creates Smart Cart
        # -------------------------------------------------

        FakeResponse(
            content="",
            tool_calls=[
                FakeToolCall(
                    "create_smart_cart",
                    {}
                )
            ]
        ),

        # -------------------------------------------------
        # Agent adds verified product/cart
        # -------------------------------------------------

        FakeResponse(
            content="",
            tool_calls=[
                FakeToolCall(
                    "add_to_smart_cart",
                    {
                        "cart_id": 1,
                        "product_id": 1,
                        "quantity": 1,
                        "auto_buy_enabled": False
                    }
                )
            ]
        ),

        # -------------------------------------------------
        # Final response
        # -------------------------------------------------

        FakeResponse(
            content=(
                "The Nike Air Max 270 has been "
                "added to your Smart Cart."
            )
        )
    ]

    fake_chat = FakeChat(responses)

    monkeypatch.setattr(
        "app.agents.agent.chat",
        fake_chat
    )

    monkeypatch.setattr(
        "app.agents.agent.execute_tool",
        fake_execute_tool
    )

    history = []

    # =====================================================
    # Conversation 1
    # =====================================================

    first = run_agent(
        user_id=1,
        user_message=(
            "Tell me about Nike Air Max 270"
        ),
        conversation_history=history
    )

    assert first["success"] is True

    assert (
        "Nike Air Max 270"
        in first["reply"]
    )

    # -----------------------------------------------------
    # Persist conversation
    # -----------------------------------------------------

    history.extend(
        [
            {
                "role": "user",
                "content": (
                    "Tell me about Nike Air Max 270"
                )
            },
            {
                "role": "assistant",
                "content": first["reply"]
            }
        ]
    )

    # =====================================================
    # Conversation 2
    # =====================================================

    second = run_agent(
        user_id=1,
        user_message=(
            "Add it to my Smart Cart"
        ),
        conversation_history=history
    )

    assert second["success"] is True

    assert "Smart Cart" in second["reply"]

    # -----------------------------------------------------
    # Verify expected tools were used
    # -----------------------------------------------------

    tool_names = [
        entry["tool"]
        for entry in second["tool_history"]
    ]

    assert "search_products" in tool_names

    assert "create_smart_cart" in tool_names

    assert "add_to_smart_cart" in tool_names

    # -----------------------------------------------------
    # Verify Smart Cart was NOT configured for
    # automatic purchasing
    # -----------------------------------------------------

    add_calls = [
        entry
        for entry in second["tool_history"]
        if entry["tool"] == "add_to_smart_cart"
    ]

    assert len(add_calls) == 1

    assert (
        add_calls[0]["arguments"]
        ["auto_buy_enabled"]
        is False
    )