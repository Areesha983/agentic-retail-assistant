from types import SimpleNamespace

import pytest

from app.agents import agent


def make_tool_call(name, arguments):
    return SimpleNamespace(
        function=SimpleNamespace(
            name=name,
            arguments=arguments
        )
    )


def make_response(content="", tool_calls=None):
    return SimpleNamespace(
        message=SimpleNamespace(
            content=content,
            tool_calls=tool_calls or []
        )
    )


def test_clean_model_reply():
    content = """
Internal reasoning here.
</think>

Final customer answer.
"""

    result = agent.clean_model_reply(content)

    assert result == "Final customer answer."


def test_agent_rejects_empty_message():
    with pytest.raises(
        ValueError,
        match="cannot be empty"
    ):
        agent.run_agent(
            "   ",
            user_id=1001
        )


def test_agent_searches_product(monkeypatch):
    responses = iter([
        make_response(
            tool_calls=[
                make_tool_call(
                    "search_products",
                    {"query": "Nike Air Max"}
                )
            ]
        ),
        make_response(
            content="I found the Nike Air Max 270."
        )
    ])

    monkeypatch.setattr(
        agent,
        "chat",
        lambda **kwargs: next(responses)
    )

    def fake_execute_tool(tool_name, **kwargs):
        assert tool_name == "search_products"
        assert kwargs["query"] == "Nike Air Max"

        return {
            "success": True,
            "query": "Nike Air Max",
            "count": 1,
            "products": [
                {
                    "product_id": 1,
                    "name": "Air Max 270",
                    "brand": "Nike",
                    "current_price": 19000
                }
            ]
        }

    monkeypatch.setattr(
        agent,
        "execute_tool",
        fake_execute_tool
    )

    result = agent.run_agent(
        "Find Nike Air Max",
        user_id=1001
    )

    assert result["success"] is True
    assert result["reply"] == (
        "I found the Nike Air Max 270."
    )

    assert len(result["tool_history"]) == 1
    assert (
        result["tool_history"][0]["tool"]
        == "search_products"
    )


def test_agent_searches_before_inventory(monkeypatch):
    responses = iter([
        make_response(
            tool_calls=[
                make_tool_call(
                    "search_products",
                    {
                        "query":
                        "Nike Air Max 270 size 9 black"
                    }
                )
            ]
        ),
        make_response(
            tool_calls=[
                make_tool_call(
                    "check_inventory",
                    {
                        "product_id": 1,
                        "variant": "9",
                        "color": "black",
                        "branch": "Dolmen Mall"
                    }
                )
            ]
        ),
        make_response(
            content=(
                "Nike Air Max 270 size 9 black "
                "has 1 unit available at Dolmen Mall."
            )
        )
    ])

    monkeypatch.setattr(
        agent,
        "chat",
        lambda **kwargs: next(responses)
    )

    def fake_execute_tool(tool_name, **kwargs):
        if tool_name == "search_products":
            return {
                "success": True,
                "count": 1,
                "products": [
                    {
                        "product_id": 1,
                        "name": "Air Max 270",
                        "brand": "Nike"
                    }
                ]
            }

        if tool_name == "check_inventory":
            assert kwargs["product_id"] == 1

            return {
                "success": True,
                "product_id": 1,
                "total_quantity": 1,
                "inventory": [
                    {
                        "product_id": 1,
                        "variant": "Size 9",
                        "color": "Black",
                        "branch": "Dolmen Mall",
                        "quantity": 1
                    }
                ]
            }

        raise AssertionError(
            f"Unexpected tool: {tool_name}"
        )

    monkeypatch.setattr(
        agent,
        "execute_tool",
        fake_execute_tool
    )

    result = agent.run_agent(
        "Is Nike Air Max 270 size 9 black "
        "available at Dolmen Mall?",
        user_id=1001
    )

    tool_names = [
        item["tool"]
        for item in result["tool_history"]
    ]

    assert tool_names == [
        "search_products",
        "check_inventory"
    ]

    assert result["success"] is True
    assert "1 unit available" in result["reply"]


def test_agent_blocks_fake_product_id(monkeypatch):
    responses = iter([
        make_response(
            tool_calls=[
                make_tool_call(
                    "check_inventory",
                    {
                        "product_id": 12345,
                        "variant": "9",
                        "color": "black",
                        "branch": "Dolmen Mall"
                    }
                )
            ]
        ),
        make_response(
            tool_calls=[
                make_tool_call(
                    "search_products",
                    {
                        "query": "Nike Air Max 270"
                    }
                )
            ]
        ),
        make_response(
            tool_calls=[
                make_tool_call(
                    "check_inventory",
                    {
                        "product_id": 1,
                        "variant": "9",
                        "color": "black",
                        "branch": "Dolmen Mall"
                    }
                )
            ]
        ),
        make_response(
            content=(
                "Nike Air Max 270 size 9 black "
                "is available at Dolmen Mall."
            )
        )
    ])

    monkeypatch.setattr(
        agent,
        "chat",
        lambda **kwargs: next(responses)
    )

    execute_calls = []

    def fake_execute_tool(tool_name, **kwargs):
        execute_calls.append(
            (tool_name, kwargs)
        )

        if tool_name == "search_products":
            return {
                "success": True,
                "query": "Nike Air Max 270",
                "count": 1,
                "products": [
                    {
                        "product_id": 1,
                        "name": "Air Max 270",
                        "brand": "Nike"
                    }
                ]
            }

        if tool_name == "check_inventory":
            assert kwargs["product_id"] == 1

            return {
                "success": True,
                "product_id": 1,
                "total_quantity": 1,
                "inventory": [
                    {
                        "product_id": 1,
                        "variant": "Size 9",
                        "color": "Black",
                        "branch": "Dolmen Mall",
                        "quantity": 1
                    }
                ]
            }

        raise AssertionError(
            f"Unexpected tool: {tool_name}"
        )

    monkeypatch.setattr(
        agent,
        "execute_tool",
        fake_execute_tool
    )

    result = agent.run_agent(
        "Is Nike Air Max 270 size 9 black "
        "in stock at Dolmen Mall?",
        user_id=1001
    )

    assert all(
        kwargs.get("product_id") != 12345
        for _, kwargs in execute_calls
    )

    assert execute_calls[0][0] == "search_products"
    assert execute_calls[1][0] == "check_inventory"
    assert execute_calls[1][1]["product_id"] == 1

    assert result["tool_history"][0]["tool"] == (
        "check_inventory"
    )

    assert result["tool_history"][0]["result"]["success"] is False

    assert "Unverified product_id" in (
        result["tool_history"][0]["result"]["error"]
    )

    assert result["success"] is True


def test_agent_orchestrates_smart_cart_auto_buy(monkeypatch):
    responses = iter([
        make_response(
            tool_calls=[
                make_tool_call(
                    "search_products",
                    {
                        "query":
                        "Nike Air Max 270 size 9 black"
                    }
                )
            ]
        ),
        make_response(
            tool_calls=[
                make_tool_call(
                    "create_smart_cart",
                    {}
                )
            ]
        ),
        make_response(
            tool_calls=[
                make_tool_call(
                    "add_to_smart_cart",
                    {
                        "cart_id": 7,
                        "product_id": 1,
                        "variant": "Size 9",
                        "color": "Black",
                        "quantity": 1,
                        "maximum_price": 20000,
                        "auto_buy_enabled": True
                    }
                )
            ]
        ),
        make_response(
            content=(
                "Nike Air Max 270 size 9 black has been "
                "added to your Smart Cart with auto-buy "
                "enabled below Rs. 20,000."
            )
        )
    ])

    monkeypatch.setattr(
        agent,
        "chat",
        lambda **kwargs: next(responses)
    )

    execute_calls = []

    def fake_execute_tool(tool_name, **kwargs):
        execute_calls.append(
            (tool_name, kwargs)
        )

        if tool_name == "search_products":
            return {
                "success": True,
                "query":
                "Nike Air Max 270 size 9 black",
                "count": 1,
                "products": [
                    {
                        "product_id": 1,
                        "name": "Air Max 270",
                        "brand": "Nike",
                        "current_price": 25000
                    }
                ]
            }

        if tool_name == "create_smart_cart":
            assert kwargs["user_id"] == 1001

            return {
                "success": True,
                "cart": {
                    "cart_id": 7,
                    "user_id": 1001,
                    "status": "ACTIVE"
                }
            }

        if tool_name == "add_to_smart_cart":
            assert kwargs["cart_id"] == 7
            assert kwargs["product_id"] == 1
            assert kwargs["variant"] == "Size 9"
            assert kwargs["color"] == "Black"
            assert kwargs["quantity"] == 1
            assert kwargs["maximum_price"] == 20000
            assert kwargs["auto_buy_enabled"] is True

            return {
                "success": True,
                "message":
                "Item added to Smart Cart.",
                "item": {
                    "item_id": 15,
                    "cart_id": 7,
                    "product_id": 1,
                    "variant": "Size 9",
                    "color": "Black",
                    "quantity": 1,
                    "maximum_price": 20000,
                    "auto_buy_enabled": True,
                    "status": "WATCHING"
                }
            }

        raise AssertionError(
            f"Unexpected tool: {tool_name}"
        )

    monkeypatch.setattr(
        agent,
        "execute_tool",
        fake_execute_tool
    )

    result = agent.run_agent(
        (
            "Add Nike Air Max 270 size 9 black "
            "to my Smart Cart and auto-buy below "
            "Rs. 20,000"
        ),
        user_id=1001
    )

    tool_names = [
        item["tool"]
        for item in result["tool_history"]
    ]

    assert tool_names == [
        "search_products",
        "create_smart_cart",
        "add_to_smart_cart"
    ]

    assert execute_calls[0][0] == "search_products"

    assert execute_calls[1][0] == "create_smart_cart"
    assert execute_calls[1][1]["user_id"] == 1001

    assert execute_calls[2][0] == "add_to_smart_cart"
    assert execute_calls[2][1]["cart_id"] == 7
    assert execute_calls[2][1]["product_id"] == 1
    assert execute_calls[2][1]["maximum_price"] == 20000
    assert execute_calls[2][1]["auto_buy_enabled"] is True

    assert "execute_purchase" not in tool_names
    assert "validate_purchase" not in tool_names

    assert result["success"] is True
    assert "Smart Cart" in result["reply"]
    assert "Rs. 20,000" in result["reply"]


def test_agent_blocks_unverified_cart_id(monkeypatch):
    responses = iter([
        make_response(
            tool_calls=[
                make_tool_call(
                    "search_products",
                    {
                        "query": "Nike Air Max 270"
                    }
                )
            ]
        ),
        make_response(
            tool_calls=[
                make_tool_call(
                    "add_to_smart_cart",
                    {
                        "cart_id": 9999,
                        "product_id": 1,
                        "variant": "Size 9",
                        "color": "Black",
                        "quantity": 1,
                        "maximum_price": 20000,
                        "auto_buy_enabled": True
                    }
                )
            ]
        ),
        make_response(
            content=(
                "I need a verified Smart Cart before "
                "I can add the product."
            )
        )
    ])

    monkeypatch.setattr(
        agent,
        "chat",
        lambda **kwargs: next(responses)
    )

    execute_calls = []

    def fake_execute_tool(tool_name, **kwargs):
        execute_calls.append(
            (tool_name, kwargs)
        )

        if tool_name == "search_products":
            return {
                "success": True,
                "count": 1,
                "products": [
                    {
                        "product_id": 1,
                        "name": "Air Max 270",
                        "brand": "Nike"
                    }
                ]
            }

        raise AssertionError(
            "Unverified cart should never reach execute_tool"
        )

    monkeypatch.setattr(
        agent,
        "execute_tool",
        fake_execute_tool
    )

    result = agent.run_agent(
        "Add Nike Air Max 270 to Smart Cart",
        user_id=1001
    )

    assert execute_calls[0][0] == "search_products"

    assert all(
        kwargs.get("cart_id") != 9999
        for _, kwargs in execute_calls
    )

    assert result["success"] is True

    assert result["tool_history"][-1]["tool"] == (
        "add_to_smart_cart"
    )

    assert result["tool_history"][-1]["result"]["success"] is False

    assert "Unverified cart_id" in (
        result["tool_history"][-1]["result"]["error"]
    )


def test_agent_blocks_unverified_product_in_smart_cart(
    monkeypatch
):
    responses = iter([
        make_response(
            tool_calls=[
                make_tool_call(
                    "add_to_smart_cart",
                    {
                        "cart_id": 7,
                        "product_id": 9999,
                        "variant": "Size 9",
                        "color": "Black",
                        "quantity": 1,
                        "maximum_price": 20000,
                        "auto_buy_enabled": True
                    }
                )
            ]
        ),
        make_response(
            tool_calls=[
                make_tool_call(
                    "search_products",
                    {
                        "query": "Nike Air Max 270"
                    }
                )
            ]
        ),
        make_response(
            content=(
                "I found the product, but I need a "
                "verified Smart Cart before adding it."
            )
        )
    ])

    monkeypatch.setattr(
        agent,
        "chat",
        lambda **kwargs: next(responses)
    )

    execute_calls = []

    def fake_execute_tool(tool_name, **kwargs):
        execute_calls.append(
            (tool_name, kwargs)
        )

        if tool_name == "search_products":
            return {
                "success": True,
                "count": 1,
                "products": [
                    {
                        "product_id": 1,
                        "name": "Air Max 270",
                        "brand": "Nike"
                    }
                ]
            }

        raise AssertionError(
            f"Unexpected tool execution: {tool_name}"
        )

    monkeypatch.setattr(
        agent,
        "execute_tool",
        fake_execute_tool
    )

    result = agent.run_agent(
        "Add Nike Air Max 270 to my Smart Cart",
        user_id=1001
    )

    assert execute_calls[0][0] == "search_products"

    assert all(
        kwargs.get("product_id") != 9999
        for _, kwargs in execute_calls
    )

    assert result["tool_history"][0]["tool"] == (
        "add_to_smart_cart"
    )

    assert result["tool_history"][0]["result"]["success"] is False

    assert "Unverified product_id" in (
        result["tool_history"][0]["result"]["error"]
    )


def test_agent_does_not_enable_auto_buy_without_price(
    monkeypatch
):
    responses = iter([
        make_response(
            tool_calls=[
                make_tool_call(
                    "search_products",
                    {
                        "query": "Nike Air Max 270"
                    }
                )
            ]
        ),
        make_response(
            tool_calls=[
                make_tool_call(
                    "create_smart_cart",
                    {}
                )
            ]
        ),
        make_response(
            tool_calls=[
                make_tool_call(
                    "add_to_smart_cart",
                    {
                        "cart_id": 7,
                        "product_id": 1,
                        "variant": "Size 9",
                        "color": "Black",
                        "quantity": 1,
                        "auto_buy_enabled": True
                    }
                )
            ]
        ),
        make_response(
            content=(
                "Please provide a maximum price "
                "before enabling auto-buy."
            )
        )
    ])

    monkeypatch.setattr(
        agent,
        "chat",
        lambda **kwargs: next(responses)
    )

    execute_calls = []

    def fake_execute_tool(tool_name, **kwargs):
        execute_calls.append(
            (tool_name, kwargs)
        )

        if tool_name == "search_products":
            return {
                "success": True,
                "count": 1,
                "products": [
                    {
                        "product_id": 1,
                        "name": "Air Max 270",
                        "brand": "Nike"
                    }
                ]
            }

        if tool_name == "create_smart_cart":
            assert kwargs["user_id"] == 1001

            return {
                "success": True,
                "cart": {
                    "cart_id": 7,
                    "user_id": 1001,
                    "status": "ACTIVE"
                }
            }

        raise AssertionError(
            "add_to_smart_cart must not execute "
            "without a maximum price"
        )

    monkeypatch.setattr(
        agent,
        "execute_tool",
        fake_execute_tool
    )

    result = agent.run_agent(
        (
            "Add Nike Air Max 270 size 9 to my "
            "Smart Cart and auto-buy it"
        ),
        user_id=1001
    )

    assert execute_calls[0][0] == "search_products"
    assert execute_calls[1][0] == "create_smart_cart"

    assert all(
        tool_name != "add_to_smart_cart"
        for tool_name, _ in execute_calls
    )

    assert result["success"] is True

    rejected = result["tool_history"][-1]

    assert rejected["tool"] == "add_to_smart_cart"
    assert rejected["result"]["success"] is False

    assert "maximum_price" in (
        rejected["result"]["error"]
    )


def test_agent_requires_explicit_auto_buy_authorization(
    monkeypatch
):
    responses = iter([
        make_response(
            tool_calls=[
                make_tool_call(
                    "search_products",
                    {
                        "query": "Nike Air Max 270"
                    }
                )
            ]
        ),
        make_response(
            tool_calls=[
                make_tool_call(
                    "create_smart_cart",
                    {}
                )
            ]
        ),
        make_response(
            tool_calls=[
                make_tool_call(
                    "add_to_smart_cart",
                    {
                        "cart_id": 7,
                        "product_id": 1,
                        "variant": "Size 9",
                        "color": "Black",
                        "quantity": 1,
                        "maximum_price": 20000,
                        "auto_buy_enabled": False
                    }
                )
            ]
        ),
        make_response(
            content=(
                "The product has been added to your "
                "Smart Cart. Auto-buy is not enabled."
            )
        )
    ])

    monkeypatch.setattr(
        agent,
        "chat",
        lambda **kwargs: next(responses)
    )

    execute_calls = []

    def fake_execute_tool(tool_name, **kwargs):
        execute_calls.append(
            (tool_name, kwargs)
        )

        if tool_name == "search_products":
            return {
                "success": True,
                "count": 1,
                "products": [
                    {
                        "product_id": 1,
                        "name": "Air Max 270",
                        "brand": "Nike"
                    }
                ]
            }

        if tool_name == "create_smart_cart":
            assert kwargs["user_id"] == 1001

            return {
                "success": True,
                "cart": {
                    "cart_id": 7,
                    "user_id": 1001,
                    "status": "ACTIVE"
                }
            }

        if tool_name == "add_to_smart_cart":
            assert kwargs["auto_buy_enabled"] is False

            return {
                "success": True,
                "item": {
                    "item_id": 15,
                    "cart_id": 7,
                    "product_id": 1,
                    "maximum_price": 20000,
                    "auto_buy_enabled": False,
                    "status": "WATCHING"
                }
            }

        raise AssertionError(
            f"Unexpected tool: {tool_name}"
        )

    monkeypatch.setattr(
        agent,
        "execute_tool",
        fake_execute_tool
    )

    result = agent.run_agent(
        (
            "Add Nike Air Max 270 size 9 to my "
            "Smart Cart with a maximum price "
            "of Rs. 20,000"
        ),
        user_id=1001
    )

    add_call = execute_calls[2][1]

    assert add_call["maximum_price"] == 20000
    assert add_call["auto_buy_enabled"] is False

    assert result["success"] is True


def test_agent_never_executes_purchase_directly(
    monkeypatch
):
    responses = iter([
        make_response(
            tool_calls=[
                make_tool_call(
                    "execute_purchase",
                    {
                        "smart_cart_item_id": 15
                    }
                )
            ]
        ),
        make_response(
            content=(
                "I can't execute a purchase directly. "
                "Purchases are handled by the authorized "
                "purchase workflow."
            )
        )
    ])

    monkeypatch.setattr(
        agent,
        "chat",
        lambda **kwargs: next(responses)
    )

    execute_calls = []

    def fake_execute_tool(tool_name, **kwargs):
        execute_calls.append(
            (tool_name, kwargs)
        )

        raise AssertionError(
            "execute_purchase must never be exposed "
            "to the LLM agent"
        )

    monkeypatch.setattr(
        agent,
        "execute_tool",
        fake_execute_tool
    )

    result = agent.run_agent(
        "Buy the item now",
        user_id=1001
    )

    assert execute_calls == []
    assert result["success"] is True

    assert result["tool_history"][0]["tool"] == (
        "execute_purchase"
    )

    assert result["tool_history"][0]["result"]["success"] is False

    error = (
        result["tool_history"][0]["result"]["error"]
    ).lower()

    assert "not allowed" in error


def test_agent_handles_smart_cart_tool_failure(
    monkeypatch
):
    responses = iter([
        make_response(
            tool_calls=[
                make_tool_call(
                    "search_products",
                    {
                        "query": "Nike Air Max 270"
                    }
                )
            ]
        ),
        make_response(
            tool_calls=[
                make_tool_call(
                    "create_smart_cart",
                    {}
                )
            ]
        ),
        make_response(
            tool_calls=[
                make_tool_call(
                    "add_to_smart_cart",
                    {
                        "cart_id": 7,
                        "product_id": 1,
                        "variant": "Size 9",
                        "color": "Black",
                        "quantity": 1,
                        "maximum_price": 20000,
                        "auto_buy_enabled": True
                    }
                )
            ]
        ),
        make_response(
            content=(
                "I couldn't add the item to your "
                "Smart Cart because the operation failed."
            )
        )
    ])

    monkeypatch.setattr(
        agent,
        "chat",
        lambda **kwargs: next(responses)
    )

    def fake_execute_tool(tool_name, **kwargs):

        if tool_name == "search_products":
            return {
                "success": True,
                "count": 1,
                "products": [
                    {
                        "product_id": 1,
                        "name": "Air Max 270",
                        "brand": "Nike"
                    }
                ]
            }

        if tool_name == "create_smart_cart":
            return {
                "success": True,
                "cart": {
                    "cart_id": 7,
                    "user_id": 1001,
                    "status": "ACTIVE"
                }
            }

        if tool_name == "add_to_smart_cart":
            return {
                "success": False,
                "error": (
                    "Unable to add item to Smart Cart."
                )
            }

        raise AssertionError(
            f"Unexpected tool: {tool_name}"
        )

    monkeypatch.setattr(
        agent,
        "execute_tool",
        fake_execute_tool
    )

    result = agent.run_agent(
        (
            "Add Nike Air Max 270 size 9 black "
            "to my Smart Cart and auto-buy below "
            "Rs. 20,000"
        ),
        user_id=1001
    )

    assert result["success"] is True

    assert result["tool_history"][-1]["tool"] == (
        "add_to_smart_cart"
    )

    assert result["tool_history"][-1]["result"]["success"] is False

    assert "operation failed" in result["reply"].lower()

    tool_names = [
        item["tool"]
        for item in result["tool_history"]
    ]

    assert "execute_purchase" not in tool_names
    assert "validate_purchase" not in tool_names

def test_context_instruction_empty_without_history():
    result = agent.build_context_instruction(
        "Is size 9 available?",
        []
    )

    assert result == ""


def test_context_instruction_for_reference():
    history = [
        {
            "role": "user",
            "content": "Show me Nike shoes"
        },
        {
            "role": "assistant",
            "content": "I found the Nike Air Max 270."
        }
    ]

    result = agent.build_context_instruction(
        "Is size 9 available?",
        history
    )

    assert "previous conversation" in result.lower()
    assert "search_products" in result
    assert "product_id" in result
    assert "trusted" in result.lower()


def test_context_instruction_mentions_reference_resolution():
    history = [
        {
            "role": "user",
            "content": "Show me Nike Air Max 270"
        }
    ]

    result = agent.build_context_instruction(
        "Is it available?",
        history
    )

    assert "it" in result
    assert "that product" in result
    assert "same one" in result


def test_invalid_conversation_history_entry_is_ignored():
    history = [
        "invalid history entry",
        {
            "role": "user",
            "content": "Show me Nike shoes"
        }
    ]

    result = agent.build_context_instruction(
        "Is it available?",
        history
    )

    assert result != ""