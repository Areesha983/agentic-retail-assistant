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
    }
]


ALLOWED_LLM_TOOLS = {
    "search_products",
    "get_product_details",
    "check_inventory",
    "check_availability",
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
    max_tool_steps: int = 5
):
    """
    Run one customer request through the local Ollama retail agent.

    The model may only use approved read-only tools.
    Product IDs must be verified through backend tool results before
    they can be used for inventory operations.
    """

    if not isinstance(user_message, str):
        raise ValueError("User message must be a string")

    user_message = user_message.strip()

    if not user_message:
        raise ValueError("User message cannot be empty")

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
                        f"Tool not allowed for LLM: {tool_name}"
                    )

                # Prevent the model from inventing product IDs.
                if tool_name in {
                    "check_inventory",
                    "check_availability",
                }:
                    product_id = arguments.get("product_id")

                    if product_id not in known_product_ids:
                        raise ValueError(
                            "Unverified product_id. "
                            "Call search_products first and use the "
                            "product_id returned by the backend."
                        )

                result = execute_tool(
                    tool_name,
                    **arguments
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