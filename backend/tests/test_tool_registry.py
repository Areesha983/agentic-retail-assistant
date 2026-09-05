import pytest

from app.agents import tool_registry


def test_registry_contains_expected_tools():
    expected_tools = {
        "search_products",
        "get_product_details",
        "check_inventory",
        "check_availability",
        "create_smart_cart",
        "add_to_smart_cart",
        "view_smart_cart",
        "cancel_smart_cart_item",
        "validate_purchase",
        "execute_purchase",
        "create_support_request",
        "view_support_requests",
        "update_support_request",
    }

    assert set(tool_registry.list_tools()) == expected_tools


def test_get_tool():
    tool = tool_registry.get_tool("search_products")

    assert callable(tool)


def test_get_tool_rejects_unknown_tool():
    with pytest.raises(
        ValueError,
        match="Unknown tool"
    ):
        tool_registry.get_tool("delete_database")


def test_get_tool_rejects_empty_name():
    with pytest.raises(
        ValueError,
        match="cannot be empty"
    ):
        tool_registry.get_tool("   ")


def test_execute_tool(monkeypatch):
    def fake_tool(value):
        return {
            "success": True,
            "value": value
        }

    monkeypatch.setitem(
        tool_registry.TOOL_REGISTRY,
        "fake_tool",
        fake_tool
    )

    result = tool_registry.execute_tool(
        "fake_tool",
        value=123
    )

    assert result["success"] is True
    assert result["value"] == 123