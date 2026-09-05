from typing import Any, Callable

from app.tools import (
    product_tools,
    inventory_tools,
    smart_cart_tools,
    purchase_tools,
    support_tools,
)


TOOL_REGISTRY: dict[str, Callable[..., Any]] = {
    # Product tools
    "search_products": product_tools.search_products,
    "get_product_details": product_tools.get_product_details,

    # Inventory tools
    "check_inventory": inventory_tools.check_inventory,
    "check_availability": inventory_tools.check_availability,

    # Smart Cart tools
    "create_smart_cart": smart_cart_tools.create_smart_cart,
    "add_to_smart_cart": smart_cart_tools.add_to_smart_cart,
    "view_smart_cart": smart_cart_tools.view_smart_cart,
    "cancel_smart_cart_item": smart_cart_tools.cancel_smart_cart_item,

    # Purchase tools
    "validate_purchase": purchase_tools.validate_purchase,
    "execute_purchase": purchase_tools.execute_purchase,

    # Support tools
    "create_support_request": support_tools.create_support_request,
    "view_support_requests": support_tools.view_support_requests,
    "update_support_request": support_tools.update_support_request,
}


def list_tools() -> list[str]:
    """
    Return the names of all tools available to the retail agent.
    """
    return list(TOOL_REGISTRY.keys())


def get_tool(tool_name: str) -> Callable[..., Any]:
    """
    Return an approved tool by name.
    """

    if not isinstance(tool_name, str):
        raise ValueError("Tool name must be a string")

    tool_name = tool_name.strip()

    if not tool_name:
        raise ValueError("Tool name cannot be empty")

    tool = TOOL_REGISTRY.get(tool_name)

    if tool is None:
        raise ValueError(f"Unknown tool: {tool_name}")

    return tool


def execute_tool(tool_name: str, **kwargs):
    """
    Execute an approved registered tool.
    """

    tool = get_tool(tool_name)

    return tool(**kwargs)