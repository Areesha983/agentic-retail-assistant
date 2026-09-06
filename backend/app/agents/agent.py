import json
import re

from ollama import chat

from app.config import OLLAMA_MODEL
from app.agents.prompts import RETAIL_AGENT_SYSTEM_PROMPT
from app.agents.tool_registry import execute_tool


OLLAMA_TOOLS = [

    # ---------------------------------------------------------
    # PRODUCT TOOLS
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # INVENTORY TOOLS
    # ---------------------------------------------------------

    {
        "type": "function",
        "function": {
            "name": "check_inventory",
            "description": (
                "Check inventory for a product using a VERIFIED "
                "product_id returned by search_products or "
                "get_product_details. Never invent a product ID. "
                "Optionally filter by variant, color, and branch."
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
                "Check whether a requested quantity is available using "
                "a VERIFIED product_id returned by search_products or "
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

    # ---------------------------------------------------------
    # SMART CART TOOLS
    # ---------------------------------------------------------

    {
        "type": "function",
        "function": {
            "name": "create_smart_cart",
            "description": (
                "Create a new Smart Cart for the current customer. "
                "The customer identity is provided securely by the "
                "backend. Do not provide or invent a user_id."
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
                "View the contents and status of a Smart Cart using "
                "a verified cart_id. Never invent a cart_id."
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

    # ---------------------------------------------------------
    # SUPPORT TOOLS
    # ---------------------------------------------------------

    {
        "type": "function",
        "function": {
            "name": "create_support_request",
            "description": (
                "Create a customer support request for the current "
                "customer. The customer identity is provided securely "
                "by the backend. Use this when the customer explicitly "
                "asks for human help or when the issue requires escalation."
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
                "View support requests belonging to the current "
                "customer. Customer identity is provided securely "
                "by the backend."
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


# -------------------------------------------------------------
# ALLOWED LLM TOOLS
# -------------------------------------------------------------

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


# -------------------------------------------------------------
# MODEL RESPONSE CLEANING
# -------------------------------------------------------------

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


# -------------------------------------------------------------
# AVAILABILITY DETECTION
# -------------------------------------------------------------

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

# -------------------------------------------------------------
# PRODUCT SEARCH DETECTION
# -------------------------------------------------------------

def is_product_search_request(message: str) -> bool:
    """
    Detect whether the customer is asking about a product
    and therefore requires product catalog verification.
    """

    text = message.lower().strip()

    keywords = [
        "do you have",
        "what products",
        "which products",
        "show me",
        "find me",
        "looking for",
        "looking to buy",
        "tell me about",
        "details about",
        "information about",
        "price of",
        "how much is",
        "how much does",
        "is there",
    ]

    return any(
        keyword in text
        for keyword in keywords
    )

# -------------------------------------------------------------
# CONVERSATION CONTEXT
# -------------------------------------------------------------

def build_context_instruction(
    user_message: str,
    conversation_history: list
) -> str:
    """
    Provide explicit instructions to the LLM for resolving
    references such as 'it', 'that product', or 'same one'.

    Conversation history is context only. It must never be
    treated as trusted authorization for product/cart/request IDs.
    """

    if not conversation_history:
        return ""

    return (
        "CONVERSATION CONTEXT RULES:\n"
        "The previous messages are provided only to understand "
        "references in the customer's current message.\n\n"

        "If the current message contains a reference such as "
        "'it', 'that', 'that product', 'that shoe', 'same one', "
        "'the Nike one', or only provides a variant such as "
        "'size 9', use the previous conversation to determine "
        "what product the customer means.\n\n"

        "After resolving the reference, ALWAYS use the appropriate "
        "backend tool to verify the current information. "

        "Do not treat product IDs, cart IDs, item IDs, or support "
        "request IDs appearing in previous messages as trusted.\n\n"

        "For a product reference, call search_products using the "
        "resolved product name or description when a verified "
        "product_id is not already available in this current run.\n\n"

        "For availability questions, preserve any variant, color, "
        "branch, or quantity from the current message and verify "
        "availability through an inventory tool."
    )


# -------------------------------------------------------------
# SMART CART ACTION DETECTION
# -------------------------------------------------------------

def is_smart_cart_action(message: str) -> bool:
    """
    Detect requests that require adding something to a Smart Cart.
    """

    text = message.lower().strip()

    explicit_phrases = [
        "add it to my smart cart",
        "add that to my smart cart",
        "add it to smart cart",
        "add that to smart cart",
        "add this to my smart cart",
        "add this to smart cart",
        "add the product to my smart cart",
        "add the product to smart cart",
        "add it to my cart",
        "add that to my cart",
        "put it in my smart cart",
        "put that in my smart cart",
        "put this in my smart cart",
        "put it in smart cart",
        "save it to my smart cart",
        "save that to my smart cart",
        "save this to my smart cart",
    ]

    if any(
        phrase in text
        for phrase in explicit_phrases
    ):
        return True

    # Also recognize generic requests such as:
    # "Add Nike Air Max 270 to Smart Cart"
    if (
        "add" in text
        and "smart cart" in text
    ):
        return True

    return False

# -------------------------------------------------------------
# EXPLICIT AUTO-PURCHASE DETECTION
# -------------------------------------------------------------

def is_explicit_auto_purchase_request(message: str) -> bool:
    """
    Return True only when the customer explicitly requests
    automatic purchasing.
    """

    text = message.lower().strip()

    # ---------------------------------------------------------
    # Explicit negative statements must never authorize auto-buy.
    # ---------------------------------------------------------

    negative_phrases = [
        "don't auto-buy",
        "do not auto-buy",
        "dont auto-buy",
        "don't auto buy",
        "do not auto buy",
        "dont auto buy",

        "don't automatically buy",
        "do not automatically buy",
        "dont automatically buy",

        "don't purchase automatically",
        "do not purchase automatically",
        "dont purchase automatically",
    ]

    if any(
        phrase in text
        for phrase in negative_phrases
    ):
        return False

    # ---------------------------------------------------------
    # Explicit positive authorization.
    # ---------------------------------------------------------

    explicit_phrases = [
        "buy automatically",
        "buy it automatically",

        "purchase automatically",
        "purchase it automatically",

        "automatically buy",
        "automatically purchase",

        "buy it when the price drops",
        "purchase it when the price drops",

        "buy automatically when",
        "purchase automatically when",

        "automatically buy when",
        "automatically purchase when",

        "auto-buy",
        "auto-buy it",
        "auto-buy below",
        "auto-buy when",

        "auto buy",
        "auto buy it",
        "auto buy below",
        "auto buy when",
    ]

    return any(
        phrase in text
        for phrase in explicit_phrases
    )


# -------------------------------------------------------------
# SMART CART ARGUMENT EXTRACTION
# -------------------------------------------------------------

def extract_smart_cart_arguments(message: str) -> dict:
    """
    Extract non-ID Smart Cart arguments directly from the customer's
    current message.

    Product IDs and cart IDs are NEVER extracted from customer text.
    """

    text = message.lower()

    arguments = {
        "variant": None,
        "color": None,
        "quantity": 1,
        "maximum_price": None,
        "auto_buy_enabled": False,
    }

    # ---------------------------------------------------------
    # Quantity
    # ---------------------------------------------------------

        # ---------------------------------------------------------
    # Quantity
    # ---------------------------------------------------------

    quantity_match = re.search(
        r"\b(?:quantity|qty)\s*(?:of\s*)?(\d+)\b",
        text
    )

    if quantity_match:
        arguments["quantity"] = int(
            quantity_match.group(1)
        )

    else:
        quantity_match = re.search(
            r"\b(\d+)\s+(?:pieces?|items?|pairs?)\b",
            text
        )

        if quantity_match:
            arguments["quantity"] = int(
                quantity_match.group(1)
            )

    # ---------------------------------------------------------
    # Size / variant
    # ---------------------------------------------------------

    size_match = re.search(
        r"\bsize\s*([a-z0-9]+)\b",
        text
    )

    if size_match:
        size_value = size_match.group(1).upper()

        arguments["variant"] = (
            f"Size {size_value}"
        )

    # ---------------------------------------------------------
    # Other common variants
    # ---------------------------------------------------------

    variant_match = re.search(
        r"\b(?:variant|waist)\s*([a-z0-9]+)\b",
        text
    )

    if (
        variant_match
        and arguments["variant"] is None
    ):
        variant_value = (
            variant_match.group(1).upper()
        )

        if "waist" in text:
            arguments["variant"] = (
                f"Waist {variant_value}"
            )
        else:
            arguments["variant"] = variant_value

    # ---------------------------------------------------------
    # Color
    # ---------------------------------------------------------

    colors = [
        "black",
        "white",
        "red",
        "blue",
        "green",
        "yellow",
        "pink",
        "grey",
        "gray",
        "brown",
        "beige",
        "orange",
        "purple",
    ]

    for color in colors:

        if re.search(
            rf"\b{re.escape(color)}\b",
            text
        ):

            arguments["color"] = color.capitalize()
            break

    # ---------------------------------------------------------
    # Maximum price
    # ---------------------------------------------------------

    price_patterns = [
        (
            r"(?:maximum|max|below|under|upto|up to)"
            r"\s*(?:price)?\s*"
            r"(?:of\s*)?"
            r"(?:rs\.?|pkr)?\s*"
            r"([\d,]+(?:\.\d+)?)"
        ),
        (
            r"(?:rs\.?|pkr)\s*"
            r"([\d,]+(?:\.\d+)?)"
        ),
    ]

    for pattern in price_patterns:

        price_match = re.search(
            pattern,
            text
        )

        if price_match:

            price_text = (
                price_match
                .group(1)
                .replace(",", "")
            )

            arguments["maximum_price"] = float(
                price_text
            )

            break

    # ---------------------------------------------------------
    # Explicit automatic purchase authorization
    # ---------------------------------------------------------

    arguments["auto_buy_enabled"] = (
        is_explicit_auto_purchase_request(
            message
        )
    )

    return arguments


# -------------------------------------------------------------
# AGENT
# -------------------------------------------------------------

def run_agent(
    user_message: str,
    user_id: int,
    conversation_history: list | None = None,
    max_tool_steps: int = 5
):
    """
    Run one customer request through the local Ollama retail agent.

    The LLM may select and sequence only explicitly approved tools.

    The user_id is trusted backend context and must never be
    generated or invented by the LLM.
    """

    # ---------------------------------------------------------
    # Validate inputs
    # ---------------------------------------------------------

    if not isinstance(user_message, str):
        raise ValueError(
            "User message must be a string"
        )

    user_message = user_message.strip()

    if not user_message:
        raise ValueError(
            "User message cannot be empty"
        )

    if type(user_id) is not int or user_id <= 0:
        raise ValueError(
            "User ID must be a positive integer"
        )

    if conversation_history is None:
        conversation_history = []

    if not isinstance(conversation_history, list):
        raise ValueError(
            "Conversation history must be a list"
        )

    # ---------------------------------------------------------
    # Build system prompt
    # ---------------------------------------------------------

    system_content = RETAIL_AGENT_SYSTEM_PROMPT

    context_instruction = build_context_instruction(
        user_message,
        conversation_history
    )

    if context_instruction:

        system_content += (
            "\n\n"
            + context_instruction
        )

    messages = [
        {
            "role": "system",
            "content": system_content
        }
    ]

    # ---------------------------------------------------------
    # Add conversation history
    # ---------------------------------------------------------

    for message in conversation_history:

        if not isinstance(message, dict):
            continue

        role = message.get("role")
        content = message.get("content")

        if role not in {
            "user",
            "assistant"
        }:
            continue

        if not isinstance(content, str):
            continue

        content = content.strip()

        if not content:
            continue

        messages.append({
            "role": role,
            "content": content
        })

    # ---------------------------------------------------------
    # Add current customer message
    # ---------------------------------------------------------

    messages.append({
        "role": "user",
        "content": user_message
    })

    # ---------------------------------------------------------
    # Trusted identifiers
    # ---------------------------------------------------------

    tool_history = []

    # Product IDs returned by trusted backend product tools.
    known_product_ids = set()

    # Smart Cart IDs returned by trusted Smart Cart tools.
    known_cart_ids = set()

    # Smart Cart item IDs returned by trusted Smart Cart tools.
    known_smart_cart_item_ids = set()

    # Support request IDs returned by trusted support tools.
    known_support_request_ids = set()

    # ---------------------------------------------------------
    # Request type detection
    # ---------------------------------------------------------

    availability_required = (
        is_availability_request(
            user_message
        )
    )

    product_search_required = (
       is_product_search_request(
            user_message
        )
    )
    smart_cart_action_required = (
        is_smart_cart_action(
            user_message
        )
    )

    # ---------------------------------------------------------
    # Agent tool loop
    # ---------------------------------------------------------

    for _ in range(max_tool_steps):

        response = chat(
            model=OLLAMA_MODEL,
            messages=messages,
            tools=OLLAMA_TOOLS,
            think=False
        )

        messages.append(response.message)

        tool_calls = response.message.tool_calls or []

        # =====================================================
        # NO TOOL CALL
        # =====================================================

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
                and not history["result"].get(
                    "products",
                    []
                )
                for history in tool_history
            )

            # -------------------------------------------------
            # Availability must be confirmed by inventory.
            # -------------------------------------------------

            if (
                availability_required
                and not inventory_checked
                and not search_returned_no_products
            ):

                if known_product_ids:

                    instruction = (
                        "The customer asked about availability. "
                        "Do not answer yet. You must call "
                        "check_inventory or check_availability "
                        "using a verified product_id from this list: "
                        f"{sorted(known_product_ids)}. "
                        "Preserve the customer's requested variant, "
                        "color, branch, and quantity."
                    )

                else:

                    instruction = (
                        "The customer asked about availability. "
                        "Do not claim that something is available "
                        "or unavailable yet.\n\n"

                        "If the current message refers to a product "
                        "from previous conversation context, resolve "
                        "that product from the conversation first. "

                        "Then call search_products using the resolved "
                        "product name or description.\n\n"

                        "Do not search using only words such as "
                        "'it', 'that', 'same one', or a variant such "
                        "as 'size 9' unless that is genuinely the "
                        "product name.\n\n"

                        "After search_products returns a verified "
                        "product_id, call check_inventory or "
                        "check_availability using that verified "
                        "product_id."
                    )

                messages.append({
                    "role": "user",
                    "content": instruction
                })

                continue
            # -------------------------------------------------
            # Product questions must be verified through
            # search_products before answering.
            # -------------------------------------------------

            if (
                product_search_required
                and not known_product_ids
                and not search_returned_no_products
            ):
                messages.append({
                    "role": "user",
                    "content": (
                        "The customer is asking about a product. "
                        "Do not answer yet.\n\n"
                        "You MUST call search_products using the "
                        "product name or product description from "
                        "the customer's current message.\n\n"
                        "Do NOT invent a product_id.\n"
                        "Do NOT claim that the product exists until "
                        "search_products returns the result."
                    )
                })
                continue            

            # =================================================
            # SMART CART CONTROLLED WORKFLOW
            # =================================================

            if smart_cart_action_required:

                # -------------------------------------------------
                # Determine Smart Cart add state FIRST.
                #
                # This must happen before product/cart verification
                # so that a previously rejected add_to_smart_cart
                # attempt does not cause the agent to keep looping.
                # -------------------------------------------------

                smart_cart_add_succeeded = any(
                    history["tool"] == "add_to_smart_cart"
                    and history["result"].get("success") is True
                    for history in tool_history
                )

                smart_cart_add_blocked_for_missing_maximum_price = any(
                    history["tool"] == "add_to_smart_cart"
                    and history["result"].get("success") is False
                    and "maximum_price" in history["result"].get(
                        "error",
                        ""
                    )
                    for history in tool_history
                )

                smart_cart_add_attempted = any(
                    history["tool"] == "add_to_smart_cart"
                    for history in tool_history
                )

                # -------------------------------------------------
                # Handle an explicit auto-buy request with no
                # maximum price.
                # -------------------------------------------------

                if smart_cart_add_blocked_for_missing_maximum_price:
                    return {
                        "success": True,
                        "reply": (
                            "Please provide a maximum price "
                            "before enabling auto-buy."
                        ),
                        "tool_history": tool_history
                    }

                # -------------------------------------------------
                # If the LLM already attempted the Smart Cart add,
                # do NOT run the deterministic add again.
                #
                # This also handles rejected/unverified IDs.
                # -------------------------------------------------

                if smart_cart_add_attempted:
                    return {
                        "success": True,
                        "reply": clean_model_reply(
                            response.message.content
                        ),
                        "tool_history": tool_history
                    }

                # -------------------------------------------------
                # ONLY NOW verify product/cart IDs.
                # -------------------------------------------------

                product_verified = (
                    len(known_product_ids) == 1
                )

                cart_verified = (
                    len(known_cart_ids) == 1
                )

                # -------------------------------------------------
                # Product verification
                # -------------------------------------------------

                if not product_verified:

                    if not known_product_ids:

                        messages.append({
                            "role": "user",
                            "content": (
                                "The customer wants to add a product "
                                "to a Smart Cart.\n\n"

                                "Do not provide a final answer yet.\n"

                                "Resolve the product from the "
                                "conversation context.\n\n"

                                "Call search_products using the "
                                "resolved product name.\n\n"

                                "Do NOT invent a product_id."
                            )
                        })

                    else:

                        messages.append({
                            "role": "user",
                            "content": (
                                "Multiple products were identified "
                                "for the Smart Cart request.\n\n"

                                "Do not guess which product the "
                                "customer means.\n"

                                "Ask the customer to clarify which "
                                "product they want added."
                            )
                        })

                    continue

                # -------------------------------------------------
                # Smart Cart verification
                # -------------------------------------------------

                if not cart_verified:

                    if not known_cart_ids:

                        messages.append({
                            "role": "user",
                            "content": (
                                "The customer wants to add the "
                                "verified product to a Smart Cart.\n\n"

                                "No verified Smart Cart ID exists "
                                "in this current run.\n\n"

                                "Call create_smart_cart first.\n"

                                "Do NOT invent a cart_id."
                            )
                        })

                    else:

                        messages.append({
                            "role": "user",
                            "content": (
                                "More than one Smart Cart ID is "
                                "available in the current run.\n\n"

                                "Do not guess which cart to use."
                            )
                        })

                    continue

                
                          
                # -------------------------------------------------
                # Only perform deterministic add when:
                #
                # 1. It has not already succeeded.
                # 2. There was not an invalid-ID add attempt.
                #
                # A legitimate backend failure with verified IDs
                # may therefore be retried safely.
                # -------------------------------------------------

                if not smart_cart_add_succeeded:              

                    verified_product_id = (
                        next(iter(known_product_ids))
                    )

                    verified_cart_id = (
                        next(iter(known_cart_ids))
                    )

                    # -------------------------------------------------
                    # Deterministic customer arguments
                    # -------------------------------------------------

                    extracted_arguments = (
                        extract_smart_cart_arguments(
                            user_message
                        )
                    )

                    # -------------------------------------------------
                    # Preserve useful arguments from a previous
                    # LLM add_to_smart_cart attempt.
                    # -------------------------------------------------

                    attempted_arguments = {}

                    for history in reversed(
                        tool_history
                    ):

                        if (
                            history["tool"]
                            == "add_to_smart_cart"
                        ):

                            attempted_arguments = dict(
                                history.get(
                                    "arguments",
                                    {}
                                )
                            )

                            break

                    # -------------------------------------------------
                    # Non-ID arguments
                    # -------------------------------------------------

                    variant = (
                        attempted_arguments.get(
                            "variant"
                        )
                        if attempted_arguments.get(
                            "variant"
                        ) is not None
                        else extracted_arguments[
                            "variant"
                        ]
                    )

                    color = (
                        attempted_arguments.get(
                            "color"
                        )
                        if attempted_arguments.get(
                            "color"
                        ) is not None
                        else extracted_arguments[
                            "color"
                        ]
                    )

                    quantity = (
                        attempted_arguments.get(
                            "quantity"
                        )
                        if attempted_arguments.get(
                            "quantity"
                        ) is not None
                        else extracted_arguments[
                            "quantity"
                        ]
                    )

                    maximum_price = (
                        attempted_arguments.get(
                            "maximum_price"
                        )
                        if attempted_arguments.get(
                            "maximum_price"
                        ) is not None
                        else extracted_arguments[
                            "maximum_price"
                        ]
                    )

                    # -------------------------------------------------
                    # Explicit auto-buy authorization
                    # -------------------------------------------------

                    explicit_auto_buy = (
                        is_explicit_auto_purchase_request(
                            user_message
                        )
                    )

                    auto_buy_enabled = False

                    if explicit_auto_buy:

                        auto_buy_enabled = (
                            attempted_arguments.get(
                                "auto_buy_enabled"
                            ) is True
                        )

                        # -------------------------------------------------
                        # If the LLM failed to set the flag but the
                        # customer explicitly authorized auto-buy and
                        # provided a maximum price, preserve the
                        # authorization safely.
                        # -------------------------------------------------

                        if (
                            not auto_buy_enabled
                            and maximum_price is not None
                        ):

                            auto_buy_enabled = True

                    # -------------------------------------------------
                    # Auto-buy requires maximum price.
                    # -------------------------------------------------

                    if (
                        auto_buy_enabled
                        and maximum_price is None
                    ):

                        # Do NOT send the same failed operation
                        # back to the LLM repeatedly.
                        return {
                            "success": True,
                            "reply": (
                                "Sure. What maximum price would "
                                "you like to set for automatic "
                                "purchase?"
                            ),
                            "tool_history": tool_history
                        }

                    # -------------------------------------------------
                    # Force verified IDs and controlled authorization.
                    # -------------------------------------------------

                    forced_arguments = {
                        "cart_id": verified_cart_id,
                        "product_id": verified_product_id,
                        "variant": variant,
                        "color": color,
                        "quantity": quantity,
                        "maximum_price": maximum_price,
                        "auto_buy_enabled": auto_buy_enabled,
                    }

                    # -------------------------------------------------
                    # Execute controlled Smart Cart operation.
                    # -------------------------------------------------

                    result = execute_tool(
                        "add_to_smart_cart",
                        **forced_arguments
                    )

                    # -------------------------------------------------
                    # Record controlled Smart Cart action.
                    # -------------------------------------------------

                    tool_history.append({
                        "tool": "add_to_smart_cart",
                        "arguments": forced_arguments,
                        "result": result
                    })

                    # -------------------------------------------------
                    # Give result back to LLM.
                    # -------------------------------------------------

                    messages.append({
                        "role": "tool",
                        "tool_name": "add_to_smart_cart",
                        "content": json.dumps(
                            result,
                            default=str
                        )
                    })

                    # -------------------------------------------------
                    # Record item ID if successful.
                    # -------------------------------------------------

                    if result.get("success") is True:

                        item = result.get(
                            "item",
                            {}
                        )

                        item_id = item.get(
                            "item_id"
                        )

                        if item_id is not None:

                            known_smart_cart_item_ids.add(
                                item_id
                            )

                    continue

            # -------------------------------------------------
            # Normal final answer
            # -------------------------------------------------

            return {
                "success": True,
                "reply": clean_model_reply(
                    response.message.content
                ),
                "tool_history": tool_history
            }

        # =====================================================
        # PROCESS TOOL CALLS
        # =====================================================

        for tool_call in tool_calls:

            tool_name = tool_call.function.name

            arguments = (
                tool_call.function.arguments
                or {}
            )

            try:

                # -------------------------------------------------
                # Only approved tools.
                # -------------------------------------------------

                if tool_name not in ALLOWED_LLM_TOOLS:

                    raise ValueError(
                        f"Tool not allowed for the LLM "
                        f"and not available to the agent: "
                        f"{tool_name}"
                    )

                # -------------------------------------------------
                # Prevent invented product IDs.
                # -------------------------------------------------

                if tool_name in {
                    "check_inventory",
                    "check_availability",
                    "get_product_details",
                    "add_to_smart_cart",
                }:

                    product_id = arguments.get(
                        "product_id"
                    )

                    if product_id not in known_product_ids:

                        raise ValueError(
                            "Unverified product_id. "
                            "Call search_products first and use "
                            "the product_id returned by the backend."
                        )

                # -------------------------------------------------
                # Prevent invented Smart Cart IDs.
                # -------------------------------------------------

                if tool_name in {
                    "add_to_smart_cart",
                    "view_smart_cart",
                }:

                    cart_id = arguments.get(
                        "cart_id"
                    )

                    if cart_id not in known_cart_ids:

                        raise ValueError(
                            "Unverified cart_id. "
                            "Call create_smart_cart first or use "
                            "a verified cart_id from the application context."
                        )

                # -------------------------------------------------
                # Prevent invented Smart Cart item IDs.
                # -------------------------------------------------

                if tool_name == "cancel_smart_cart_item":

                    item_id = arguments.get(
                        "item_id"
                    )

                    if item_id not in known_smart_cart_item_ids:

                        raise ValueError(
                            "Unverified Smart Cart item_id."
                        )

                # -------------------------------------------------
                # Prevent invented support request IDs.
                # -------------------------------------------------

                if tool_name == "update_support_request":

                    request_id = arguments.get(
                        "request_id"
                    )

                    if request_id not in known_support_request_ids:

                        raise ValueError(
                            "Unverified support request_id."
                        )

                # -------------------------------------------------
                # Inject trusted customer identity.
                # -------------------------------------------------

                tool_arguments = dict(
                    arguments
                )

                if tool_name == "create_smart_cart":

                    tool_arguments["user_id"] = user_id

                elif tool_name == "create_support_request":

                    tool_arguments["user_id"] = user_id

                elif tool_name == "view_support_requests":

                    tool_arguments["user_id"] = user_id

                # -------------------------------------------------
                # Smart Cart safety guard
                # -------------------------------------------------

                if tool_name == "add_to_smart_cart":

                    explicit_auto_buy = (
                        is_explicit_auto_purchase_request(
                            user_message
                        )
                    )

                    maximum_price = tool_arguments.get(
                        "maximum_price"
                    )

                    # -------------------------------------------------
                    # Adding to Smart Cart does NOT authorize auto-buy.
                    # -------------------------------------------------

                    if not explicit_auto_buy:

                        tool_arguments["auto_buy_enabled"] = False

                    # -------------------------------------------------
                    # Explicit automatic purchase request
                    # -------------------------------------------------

                    else:

                        # Auto-buy ALWAYS requires a maximum price.
                        if maximum_price is None:

                            result = {
                                "success": False,
                                "error": (
                                    "Auto-buy cannot be enabled "
                                    "without a maximum_price."
                                )
                            }

                            tool_history.append({
                                "tool": tool_name,
                                "arguments": tool_arguments,
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

                            # Do NOT execute add_to_smart_cart.
                            continue

                        # Customer explicitly authorized auto-buy
                        # AND supplied a maximum price.
                        tool_arguments["auto_buy_enabled"] = True

                # -------------------------------------------------
                # Execute approved tool.
                # -------------------------------------------------

                result = execute_tool(
                    tool_name,
                    **tool_arguments
                )                

                # -------------------------------------------------
                # Record trusted product IDs.
                # -------------------------------------------------

                if tool_name == "search_products":

                    for product in result.get(
                        "products",
                        []
                    ):

                        product_id = product.get(
                            "product_id"
                        )

                        if product_id is not None:

                            known_product_ids.add(
                                product_id
                            )

                elif tool_name == "get_product_details":

                    product = result.get(
                        "product",
                        {}
                    )

                    product_id = product.get(
                        "product_id"
                    )

                    if product_id is not None:

                        known_product_ids.add(
                            product_id
                        )

                # -------------------------------------------------
                # Record trusted Smart Cart IDs.
                # -------------------------------------------------

                elif tool_name == "create_smart_cart":

                    cart = result.get(
                        "cart",
                        {}
                    )

                    cart_id = cart.get(
                        "cart_id"
                    )

                    if cart_id is not None:

                        known_cart_ids.add(
                            cart_id
                        )

                elif tool_name == "add_to_smart_cart":
                    if result.get("success") is True:
                        item = result.get(
                            "item",
                            {}
                        )

                        cart_id = item.get(
                            "cart_id"
                        )

                        item_id = item.get(
                            "item_id"
                        )

                        if cart_id is not None:
                            known_cart_ids.add(
                                cart_id
                            )

                        if item_id is not None:
                            known_smart_cart_item_ids.add(
                                item_id
                            )                

                elif tool_name == "view_smart_cart":

                    cart = result.get(
                        "cart",
                        {}
                    )

                    items = result.get(
                        "items",
                        []
                    )

                    cart_id = cart.get(
                        "cart_id"
                    )

                    if cart_id is not None:

                        known_cart_ids.add(
                            cart_id
                        )

                    for item in items:

                        item_id = item.get(
                            "item_id"
                        )

                        if item_id is not None:

                            known_smart_cart_item_ids.add(
                                item_id
                            )

                elif tool_name == "cancel_smart_cart_item":

                    item = result.get(
                        "item",
                        {}
                    )

                    item_id = item.get(
                        "item_id"
                    )

                    if item_id is not None:

                        known_smart_cart_item_ids.add(
                            item_id
                        )

                # -------------------------------------------------
                # Record trusted support request IDs.
                # -------------------------------------------------

                elif tool_name == "create_support_request":

                    request = result.get(
                        "request",
                        {}
                    )

                    request_id = request.get(
                        "request_id"
                    )

                    if request_id is not None:

                        known_support_request_ids.add(
                            request_id
                        )

                elif tool_name == "view_support_requests":

                    requests = result.get(
                        "requests",
                        []
                    )

                    for request in requests:

                        request_id = request.get(
                            "request_id"
                        )

                        if request_id is not None:

                            known_support_request_ids.add(
                                request_id
                            )

                elif tool_name == "update_support_request":

                    request = result.get(
                        "request",
                        {}
                    )

                    request_id = request.get(
                        "request_id"
                    )

                    if request_id is not None:

                        known_support_request_ids.add(
                            request_id
                        )

            except Exception as exc:

                result = {
                    "success": False,
                    "error": str(exc)
                }

                # -------------------------------------------------
                # Recovery instruction for invalid IDs.
                # -------------------------------------------------

                recovery_message = (
                    "The previous tool call was rejected because "
                    "it used an unverified backend identifier.\n\n"

                    "Do NOT retry the same tool call with another "
                    "guessed ID.\n\n"

                    "If a product_id is required and no verified "
                    "product_id exists in the current run, first "
                    "call search_products using the product name "
                    "resolved from the conversation.\n\n"

                    "If a cart_id is required and no verified cart_id "
                    "exists in the current run, first call "
                    "create_smart_cart.\n\n"

                    "Only use IDs returned by successful backend "
                    "tools during this current run."
                )

                messages.append({
                    "role": "user",
                    "content": recovery_message
                })

            # -------------------------------------------------
            # Store tool execution history.
            # -------------------------------------------------

            tool_history.append({
                "tool": tool_name,
                "arguments": arguments,
                "result": result
            })

            # -------------------------------------------------
            # Give tool result back to model.
            # -------------------------------------------------

            messages.append({
                "role": "tool",
                "tool_name": tool_name,
                "content": json.dumps(
                    result,
                    default=str
                )
            })

    # ---------------------------------------------------------
    # Maximum tool steps exceeded.
    # ---------------------------------------------------------

    raise RuntimeError(
        "Agent exceeded maximum tool-call steps"
    )