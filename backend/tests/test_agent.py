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
        agent.run_agent("   ")


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
        "Find Nike Air Max"
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
        "available at Dolmen Mall?"
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
        # Model first invents an invalid product ID.
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

        # After the backend rejects it, model searches properly.
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

        # Model now uses the verified product ID.
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

        # Final customer-facing answer.
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
        "in stock at Dolmen Mall?"
    )

    # The fabricated product_id=12345 must never reach execute_tool.
    assert all(
        kwargs.get("product_id") != 12345
        for _, kwargs in execute_calls
    )

    # Only verified backend operations should execute.
    assert execute_calls[0][0] == "search_products"
    assert execute_calls[1][0] == "check_inventory"
    assert execute_calls[1][1]["product_id"] == 1

    # History should still record the rejected fake attempt.
    assert result["tool_history"][0]["tool"] == "check_inventory"
    assert result["tool_history"][0]["result"]["success"] is False
    assert "Unverified product_id" in (
        result["tool_history"][0]["result"]["error"]
    )

    assert result["success"] is True