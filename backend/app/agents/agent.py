import json

from ollama import chat

from app.config import OLLAMA_MODEL
from app.agents.prompts import RETAIL_AGENT_SYSTEM_PROMPT
from app.agents.tool_registry import execute_tool


OLLAMA_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": (
                "Search the retail product catalog by product name, "
                "brand, or product type. Use this first when the user "
                "mentions a product by name and its product_id is not known."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Product search text."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_product_details",
            "description": (
                "Get details for a product when its verified product ID "
                "is already known."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "integer",
                        "description": "Verified product ID."
                    }
                },
                "required": ["product_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_inventory",
            "description": (
                "Check inventory for a product using a VERIFIED product_id "
                "returned by search_products or get_product_details. "
                "Never invent a product ID. Optionally filter by variant, "
                "color, and branch."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "integer"
                    },
                    "variant": {
                        "type": ["string", "null"]
                    },
                    "color": {
                        "type": ["string", "null"]
                    },
                    "branch": {
                        "type": ["string", "null"]
                    }
                },
                "required": ["product_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_availability",
            "description": (
                "Check whether a requested quantity is available using a "
                "VERIFIED product_id returned by search_products or "
                "get_product_details. Never invent a product ID."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "integer"
                    },
                    "variant": {
                        "type": ["string", "null"]
                    },
                    "color": {
                        "type": ["string", "null"]
                    },
                    "branch": {
                        "type": ["string", "null"]
                    },
                    "quantity": {
                        "type": "integer",
                        "minimum": 1
                    }
                },
                "required": [
                    "product_id",
                    "quantity"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_smart_cart",
            "description": (
                "Create a new Smart Cart for the current customer. "
                "The customer identity is provided securely by the backend. "
                "Do not provide or invent a user_id."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_to_smart_cart",
            "description": (
                "Add a VERIFIED product to an existing Smart Cart. "
                "Use a cart_id returned by create_smart_cart or explicitly "
                "provided by the trusted application context. Never invent "
                "cart_id or product_id. Store optional variant, color, "
                "quantity, maximum price, and explicit automatic-purchase "
                "authorization."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "cart_id": {
                        "type": "integer",
                        "description": "Verified Smart Cart ID."
                    },
                    "product_id": {
                        "type": "integer",
                        "description": "Verified product ID."
                    },
                    "variant": {
                        "type": ["string", "null"]
                    },
                    "color": {
                        "type": ["string", "null"]
                    },
                    "quantity": {
                        "type": "integer",
                        "minimum": 1
                    },
                    "maximum_price": {
                        "type": ["number", "null"],
                        "description": (
                            "Maximum price authorized by the customer."
                        )
                    },
                    "auto_buy_enabled": {
                        "type": "boolean",
                        "description": (
                            "True only when the customer explicitly "
                            "authorizes automatic purchase."
                        )
                    }
                },
                "required": [
                    "cart_id",
                    "product_id",
                    "quantity",
                    "auto_buy_enabled"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "view_smart_cart",
            "description": (
                "View the contents and status of a Smart Cart using a "
                "verified cart_id. Never invent a cart_id."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "cart_id": {
                        "type": "integer",
                        "description": "Verified Smart Cart ID."
                    }
                },
                "required": ["cart_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_smart_cart_item",
            "description": (
                "Cancel a Smart Cart item using a verified item_id. "
                "Never invent an item_id."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "item_id": {
                        "type": "integer",
                        "description": "Verified Smart Cart item ID."
                    }
                },
                "required": ["item_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_support_request",
            "description": (
                "Create a customer support request for the current customer. "
                "The customer identity is provided securely by the backend. "
                "Use this when the customer explicitly asks for human help "
                "or when the issue requires escalation."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Customer's support issue."
                    },
                    "reason": {
                        "type": ["string", "null"]
                    },
                    "priority": {
                        "type": "string",
                        "enum": [
                            "LOW",
                            "MEDIUM",
                            "HIGH",
                            "URGENT"
                        ]
                    }
                },
                "required": [
                    "message",
                    "priority"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "view_support_requests",
            "description": (
                "View support requests belonging to the current customer. "
                "Customer identity is provided securely by the backend."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_support_request",
            "description": (
                "Update a support request using a verified request_id. "
                "Never invent a request_id."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "request_id": {
                        "type": "integer",
                        "description": "Verified support request ID."
                    },
                    "status": {
                        "type": "string",
                        "enum": [
                            "OPEN",
                            "IN_PROGRESS",
                            "RESOLVED",
                            "CANCELLED"
                        ]
                    },
                    "resolution": {
                        "type": ["string", "null"]
                    }
                },
                "required": [
                    "request_id",
                    "status"
                ]
            }
        }
    }
]


ALLOWED_LLM_TOOLS = {
    "search_products",
    "get_product_details",
    "check_inventory",
    "check_availability",
    "create_smart_cart",
    "add_to_smart_cart",
    "view_smart_cart",
    "cancel_smart_cart_item",
    "create_support_request",
    "view_support_requests",
    "update_support_request",
}


def clean_model_reply(content: str) -> str:
    """
    Remove model reasoning/thinking text from customer-facing output.
    """

    if not content:
        return ""

    content = content.strip()

    if "</think>" in content:
        content = content.rsplit("</think>", 1)[-1].strip()

    return content


def is_availability_request(message: str) -> bool:
    """
    Detect whether the customer is asking about stock/availability.
    """

    text = message.lower()

    keywords = [
        "available",
        "availability",
        "in stock",
        "stock",
        "available hai",
        "maujood",
        "mil jayega",
        "mil sakta",
    ]

    return any(
        keyword in text
        for keyword in keywords
    )


def run_agent(
    user_message: str,
    user_id: int,
    max_tool_steps: int = 5
):
    """
    Run one customer request through the local Ollama retail agent.

    The LLM may select and sequence only explicitly approved tools.

    The user_id is trusted backend context and must never be generated
    or invented by the LLM.
    """

    if not isinstance(user_message, str):
        raise ValueError("User message must be a string")

    user_message = user_message.strip()

    if not user_message:
        raise ValueError("User message cannot be empty")

    if type(user_id) is not int or user_id <= 0:
        raise ValueError(
            "User ID must be a positive integer"
        )

    messages = [
        {
            "role": "system",
            "content": RETAIL_AGENT_SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": user_message
        }
    ]

    tool_history = []

    # Product IDs returned by trusted backend product tools.
    known_product_ids = set()

    # Smart Cart IDs returned by trusted Smart Cart tools.
    known_cart_ids = set()

    # Smart Cart item IDs returned by trusted Smart Cart tools.
    known_smart_cart_item_ids = set()

    # Support request IDs returned by trusted support tools.
    known_support_request_ids = set()

    availability_required = is_availability_request(
        user_message
    )

    for _ in range(max_tool_steps):
        response = chat(
            model=OLLAMA_MODEL,
            messages=messages,
            tools=OLLAMA_TOOLS,
            think=False
        )

        messages.append(response.message)

        tool_calls = response.message.tool_calls or []

        # No tool call means the model has produced its final answer.
        if not tool_calls:
            inventory_checked = any(
                history["tool"] in {
                    "check_inventory",
                    "check_availability",
                }
                and history["result"].get("success") is True
                for history in tool_history
            )

            search_returned_no_products = any(
                history["tool"] == "search_products"
                and history["result"].get("success") is True
                and not history["result"].get("products", [])
                for history in tool_history
            )

            # Availability must be confirmed by an inventory tool.
            if (
                availability_required
                and not inventory_checked
                and not search_returned_no_products
            ):
                if known_product_ids:
                    instruction = (
                        "The customer asked about availability. "
                        "Do not answer yet. You must call check_inventory "
                        "or check_availability using a verified product_id "
                        f"from this list: {sorted(known_product_ids)}. "
                        "Preserve the customer's requested variant, color, "
                        "branch, and quantity."
                    )
                else:
                    instruction = (
                        "The customer asked about availability. "
                        "Do not claim that something is available or "
                        "unavailable yet. Search for the product first, "
                        "then check inventory using the verified product_id."
                    )

                messages.append({
                    "role": "user",
                    "content": instruction
                })

                continue

            return {
                "success": True,
                "reply": clean_model_reply(
                    response.message.content
                ),
                "tool_history": tool_history
            }

        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = tool_call.function.arguments or {}

            try:
                # Only explicitly approved tools may be used.
                if tool_name not in ALLOWED_LLM_TOOLS:
                    raise ValueError(
                        f"Tool not allowed for the LLM and not available "
                        f"to the agent: {tool_name}"
                    )

                # Prevent the model from inventing product IDs.
                if tool_name in {
                    "check_inventory",
                    "check_availability",
                    "get_product_details",
                    "add_to_smart_cart",
                }:
                    product_id = arguments.get("product_id")

                    if (
                        tool_name != "get_product_details"
                        and product_id not in known_product_ids
                    ):
                        raise ValueError(
                            "Unverified product_id. "
                            "Call search_products first and use the "
                            "product_id returned by the backend."
                        )

                    if (
                        tool_name == "get_product_details"
                        and product_id not in known_product_ids
                    ):
                        raise ValueError(
                            "Unverified product_id. "
                            "Call search_products first and use the "
                            "product_id returned by the backend."
                        )

                # Prevent the model from inventing Smart Cart IDs.
                if tool_name in {
                    "add_to_smart_cart",
                    "view_smart_cart",
                }:
                    cart_id = arguments.get("cart_id")

                    if cart_id not in known_cart_ids:
                        raise ValueError(
                            "Unverified cart_id. "
                            "Call create_smart_cart first or use a "
                            "verified cart_id from the application context."
                        )

                # Prevent the model from inventing Smart Cart item IDs.
                if tool_name == "cancel_smart_cart_item":
                    item_id = arguments.get("item_id")

                    if item_id not in known_smart_cart_item_ids:
                        raise ValueError(
                            "Unverified Smart Cart item_id."
                        )

                # Prevent the model from inventing support request IDs.
                if tool_name == "update_support_request":
                    request_id = arguments.get("request_id")

                    if request_id not in known_support_request_ids:
                        raise ValueError(
                            "Unverified support request_id."
                        )

                # Inject trusted customer identity into customer-scoped
                # tools. The LLM never receives or generates this value.
                tool_arguments = dict(arguments)

                if tool_name == "create_smart_cart":
                    tool_arguments["user_id"] = user_id

                elif tool_name == "create_support_request":
                    tool_arguments["user_id"] = user_id

                elif tool_name == "view_support_requests":
                    tool_arguments["user_id"] = user_id

                # ---------------------------------------------------------
                # Smart Cart safety guard
                # ---------------------------------------------------------
                # Auto-buy is only allowed when a maximum price
                # has been explicitly provided.
                if tool_name == "add_to_smart_cart":
                    if tool_arguments.get("auto_buy_enabled") is True:
                        maximum_price = tool_arguments.get(
                            "maximum_price"
                        )

                        if maximum_price is None:
                            result = {
                                "success": False,
                                "error": (
                                    "Auto-buy cannot be enabled without "
                                    "a maximum_price."
                                )
                            }

                            # Do NOT call execute_tool().
                            # The request is rejected at the agent boundary.
                            tool_history.append({
                                "tool": tool_name,
                                "arguments": arguments,
                                "result": result
                            })

                            messages.append({
                                "role": "tool",
                                "tool_name": tool_name,
                                "content": json.dumps(
                                    result,
                                    default=str
                                )
                            })

                            continue

                # Execute approved tool.
                result = execute_tool(
                    tool_name,
                    **tool_arguments
                )

                # Record trusted product IDs returned by the backend.
                if tool_name == "search_products":
                    for product in result.get("products", []):
                        product_id = product.get("product_id")

                        if product_id is not None:
                            known_product_ids.add(product_id)

                elif tool_name == "get_product_details":
                    product = result.get("product", {})
                    product_id = product.get("product_id")

                    if product_id is not None:
                        known_product_ids.add(product_id)

                # Record trusted Smart Cart IDs returned by the backend.
                elif tool_name == "create_smart_cart":
                    cart = result.get("cart", {})
                    cart_id = cart.get("cart_id")

                    if cart_id is not None:
                        known_cart_ids.add(cart_id)

                elif tool_name == "add_to_smart_cart":
                    item = result.get("item", {})

                    cart_id = item.get("cart_id")
                    item_id = item.get("item_id")

                    if cart_id is not None:
                        known_cart_ids.add(cart_id)

                    if item_id is not None:
                        known_smart_cart_item_ids.add(item_id)

                elif tool_name == "view_smart_cart":
                    cart = result.get("cart", {})
                    items = result.get("items", [])

                    cart_id = cart.get("cart_id")

                    if cart_id is not None:
                        known_cart_ids.add(cart_id)

                    for item in items:
                        item_id = item.get("item_id")

                        if item_id is not None:
                            known_smart_cart_item_ids.add(item_id)

                elif tool_name == "cancel_smart_cart_item":
                    item = result.get("item", {})
                    item_id = item.get("item_id")

                    if item_id is not None:
                        known_smart_cart_item_ids.add(item_id)

                # Record trusted support request IDs.
                elif tool_name == "create_support_request":
                    request = result.get("request", {})
                    request_id = request.get("request_id")

                    if request_id is not None:
                        known_support_request_ids.add(request_id)

                elif tool_name == "view_support_requests":
                    requests = result.get("requests", [])

                    for request in requests:
                        request_id = request.get("request_id")

                        if request_id is not None:
                            known_support_request_ids.add(request_id)

                elif tool_name == "update_support_request":
                    request = result.get("request", {})
                    request_id = request.get("request_id")

                    if request_id is not None:
                        known_support_request_ids.add(request_id)

            except Exception as exc:
                result = {
                    "success": False,
                    "error": str(exc)
                }

            tool_history.append({
                "tool": tool_name,
                "arguments": arguments,
                "result": result
            })

            messages.append({
                "role": "tool",
                "tool_name": tool_name,
                "content": json.dumps(
                    result,
                    default=str
                )
            })

    raise RuntimeError(
        "Agent exceeded maximum tool-call steps"
    )