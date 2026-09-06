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
        "its price",
        "the price",
        "what is the price",
        "what's the price",
        "cost of",
        "how much for",
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
        "request IDs appearing in previous messages as trusted, "
        "even if a number was mentioned in an earlier reply.\n\n"

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
        "yes add to smart cart",
        "yes add it to smart cart",
        "yes add it to my smart cart",
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
    #
    # IMPORTANT: each pattern requires either the literal word
    # "price" or a currency marker (Rs./PKR) actually present.
    # Without that, "(?:maximum|max|...)" alone matches the word
    # "max" inside a product name like "Air Max 270" and wrongly
    # extracts 270 as a maximum price.
    # ---------------------------------------------------------

    price_patterns = [
        # "maximum price of Rs. 20,000" / "max price 20000"
        (
            r"\b(?:maximum|max|below|under|upto|up to)\s+"
            r"price\b\s*(?:of\s*)?(?:rs\.?|pkr)?\s*"
            r"([\d,]+(?:\.\d+)?)"
        ),
        # "below Rs. 18,000" / "under PKR 5000" — requires the
        # currency marker directly, not just any nearby digits.
        (
            r"\b(?:maximum|max|below|under|upto|up to)\b\s*"
            r"(?:of\s*)?(?:rs\.?|pkr)\s*"
            r"([\d,]+(?:\.\d+)?)"
        ),
        # bare "Rs. 20,000" / "PKR 5000" anywhere in the message.
        (
            r"\b(?:rs\.?|pkr)\b\s*"
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

def extract_contextual_smart_cart_arguments(
    user_message: str,
    conversation_history: list
) -> dict:
    """
    Extract Smart Cart arguments from the current message and
    inherit missing product configuration from recent conversation.
    """

    current = extract_smart_cart_arguments(user_message)

    # If current message explicitly provides details, preserve them.
    if current.get("variant") is not None:
        variant = current["variant"]
    else:
        variant = None

    if current.get("color") is not None:
        color = current["color"]
    else:
        color = None

    quantity = current.get("quantity", 1)

    # Walk backwards through the conversation.
    for message in reversed(conversation_history):
        if not isinstance(message, dict):
            continue

        role = message.get("role")
        content = message.get("content")

        if role not in {"user", "assistant"}:
            continue

        if not isinstance(content, str):
            continue

        content = content.strip()

        if not content:
            continue

        previous = extract_smart_cart_arguments(content)

        # Only inherit values that are missing from the current request.
        if variant is None and previous.get("variant") is not None:
            variant = previous["variant"]

        if color is None and previous.get("color") is not None:
            color = previous["color"]

        if quantity == 1 and previous.get("quantity") != 1:
            quantity = previous["quantity"]

        # Stop once we have enough contextual information.
        if variant is not None:
            break

    current["variant"] = variant
    current["color"] = color
    current["quantity"] = quantity

    return current
# -------------------------------------------------------------
# PRODUCT NAME RESOLUTION (fallback recovery helper)
# -------------------------------------------------------------

_NON_PRODUCT_PHRASES = {
    "Smart Cart",
    "Product ID",
    "Would You",
    "Add This",
    "Current Price",
    "Available From",
    "Yes Add",
}

def resolve_product_query_from_context(
    conversation_history: list,
    user_message: str
) -> str:
    """
    Deterministically resolve a product reference from recent
    conversation context.

    This function returns only a product search query.
    It NEVER returns or trusts a product_id.
    """

    current_text = user_message.strip()

    # ---------------------------------------------------------
    # If the current message explicitly contains a product name,
    # try to extract it first.
    # ---------------------------------------------------------
    explicit_patterns = [
        r"\badd\s+(.+?)\s+to\s+(?:my\s+)?smart\s+cart\b",
        r"\badd\s+(.+?)\s+to\s+(?:my\s+)?cart\b",
        r"\bput\s+(.+?)\s+in\s+(?:my\s+)?smart\s+cart\b",
        r"\bsave\s+(.+?)\s+to\s+(?:my\s+)?smart\s+cart\b",
    ]

    for pattern in explicit_patterns:
        match = re.search(
            pattern,
            current_text,
            flags=re.IGNORECASE
        )

        if match:
            candidate = match.group(1).strip()

            if candidate.lower() not in {
                "it",
                "that",
                "this",
                "the product",
                "the item",
                "same one",
            }:
                return candidate

    # ---------------------------------------------------------
    # Search conversation from newest to oldest.
    # ---------------------------------------------------------
    for message in reversed(conversation_history or []):

        if not isinstance(message, dict):
            continue

        content = message.get("content")

        if not isinstance(content, str):
            continue

        content = content.strip()

        if not content:
            continue

        # -----------------------------------------------------
        # 1. Product name inside quotes.
        #
        # Example:
        # The product "Nike Air Max 270" has been found...
        # -----------------------------------------------------
        quoted_patterns = [
            r'"([^"]+)"',
            r"'([^']+)'",
        ]

        for pattern in quoted_patterns:
            matches = re.findall(
                pattern,
                content
            )

            for candidate in matches:
                candidate = candidate.strip()

                if (
                    candidate
                    and candidate not in _NON_PRODUCT_PHRASES
                    and not candidate.lower().startswith(
                        ("product id", "rs.", "pkr")
                    )
                ):
                    # Avoid returning generic conversational text.
                    if len(candidate.split()) <= 6:
                        return candidate

        # -----------------------------------------------------
        # 2. Common product-introduction phrases.
        # -----------------------------------------------------
        phrase_patterns = [
            r"the product\s+([A-Z][A-Za-z0-9']*(?:\s+[A-Za-z0-9']+){0,5})",
            r"product:\s*([A-Z][A-Za-z0-9']*(?:\s+[A-Za-z0-9']+){0,5})",
            r"do you have\s+(.+?)(?:\?|$)",
            r"looking for\s+(.+?)(?:\?|$)",
        ]

        for pattern in phrase_patterns:
            match = re.search(
                pattern,
                content,
                flags=re.IGNORECASE
            )

            if match:
                candidate = match.group(1).strip()

                # Remove common trailing conversational text.
                candidate = re.split(
                    r"\s+(?:has been|is available|currently costs|costs|for)\b",
                    candidate,
                    maxsplit=1,
                    flags=re.IGNORECASE
                )[0].strip()

                if (
                    candidate
                    and candidate.lower() not in {
                        "it",
                        "that",
                        "this",
                        "the product",
                        "the item",
                        "same one",
                    }
                ):
                    return candidate

        # -----------------------------------------------------
        # 3. Product-like capitalized phrase.
        # -----------------------------------------------------
        pattern = re.compile(
            r"\b([A-Z][A-Za-z0-9']*(?:\s+[A-Z][A-Za-z0-9']*){1,5})\b"
        )

        for match in pattern.finditer(content):
            candidate = match.group(1).strip()

            if candidate in _NON_PRODUCT_PHRASES:
                continue

            if candidate.lower() in {
                "the product",
                "the item",
                "smart cart",
                "current price",
                "product id",
            }:
                continue

            return candidate

    # ---------------------------------------------------------
    # Nothing reliable found.
    # ---------------------------------------------------------
    return user_message

def has_variant_or_color_reference(message: str) -> bool:
    """
    Detect whether the message mentions a specific size/variant or
    color, which implies the customer wants a stock-level answer even
    if they phrased it as "do you have ... size 9 ... black?" rather
    than using an explicit availability keyword.
    """

    text = message.lower()

    if re.search(r"\bsize\s*[a-z0-9]+\b", text):
        return True

    if re.search(r"\bwaist\s*[a-z0-9]+\b", text):
        return True

    colors = [
        "black", "white", "red", "blue", "green", "yellow",
        "pink", "grey", "gray", "brown", "beige", "orange", "purple",
    ]

    return any(color in text for color in colors)

def resolve_smart_cart_product(
    user_message: str,
    conversation_history: list
) -> dict:
    """
    Resolve the product intended by the customer for a Smart Cart action.

    Resolution order:
    1. Deterministically resolve references such as "it", "that product",
       or "same one" from recent conversation context.
    2. If deterministic resolution fails, use the LLM as a fallback.
    
    Product/cart IDs are still obtained exclusively from backend tools.
    """

    # ---------------------------------------------------------
    # Step 1: Deterministic context resolution
    # ---------------------------------------------------------
    deterministic_query = resolve_product_query_from_context(
        conversation_history=conversation_history,
        user_message=user_message
    )

    # If the resolver found a product different from the current
    # generic Smart Cart message, use it directly.
    if (
        deterministic_query
        and deterministic_query.strip()
        and deterministic_query.strip().lower()
        != user_message.strip().lower()
    ):
        return {
            "success": True,
            "query": deterministic_query.strip()
        }

    # ---------------------------------------------------------
    # Step 2: LLM fallback
    # ---------------------------------------------------------
    planner_messages = [
        {
            "role": "system",
            "content": (
                "You are resolving a customer's Smart Cart request.\n\n"
                "Use the conversation context to determine which product "
                "the customer means.\n\n"
                "You MUST call search_products using the resolved product "
                "name or description.\n\n"
                "Do not call any other tool.\n"
                "Do not invent product IDs."
            )
        }
    ]

    for message in conversation_history:
        if not isinstance(message, dict):
            continue

        role = message.get("role")
        content = message.get("content")

        if role not in {"user", "assistant"}:
            continue

        if not isinstance(content, str):
            continue

        content = content.strip()

        if content:
            planner_messages.append({
                "role": role,
                "content": content
            })

    planner_messages.append({
        "role": "user",
        "content": user_message
    })

    response = chat(
        model=OLLAMA_MODEL,
        messages=planner_messages,
        tools=[
            next(
                tool
                for tool in OLLAMA_TOOLS
                if tool["function"]["name"] == "search_products"
            )
        ],
        think=False
    )

    tool_calls = response.message.tool_calls or []

    if len(tool_calls) != 1:
        return {
            "success": False,
            "error": (
                "I could not determine which product you want "
                "to add to the Smart Cart."
            )
        }

    tool_call = tool_calls[0]

    if tool_call.function.name != "search_products":
        return {
            "success": False,
            "error": (
                "The product resolver did not return a valid "
                "product search."
            )
        }

    arguments = tool_call.function.arguments or {}

    if not isinstance(arguments, dict):
        try:
            arguments = json.loads(arguments)
        except Exception:
            return {
                "success": False,
                "error": "Invalid product search arguments."
            }

    query = arguments.get("query")

    if not isinstance(query, str) or not query.strip():
        return {
            "success": False,
            "error": "No product could be resolved from the conversation."
        }

    return {
        "success": True,
        "query": query.strip()
    }

def run_smart_cart_workflow(
    user_message: str,
    user_id: int,
    conversation_history: list
) -> dict:
    """
    Controlled Smart Cart workflow.

    The LLM resolves the product.
    Backend tools verify and perform all state-changing operations.
    """

    arguments = extract_contextual_smart_cart_arguments(
        user_message=user_message,
        conversation_history=conversation_history
    )
    
    explicit_auto_buy = is_explicit_auto_purchase_request(
        user_message
    )

    # ---------------------------------------------------------
    # Auto-buy safety
    # ---------------------------------------------------------

    if explicit_auto_buy and arguments["maximum_price"] is None:
        return {
            "success": True,
            "reply": (
                "Sure. What maximum price would you like to "
                "set for automatic purchase?"
            ),
            "tool_history": []
        }

    # ---------------------------------------------------------
    # Step 1: Resolve product
    # ---------------------------------------------------------

    resolved = resolve_smart_cart_product(
        user_message=user_message,
        conversation_history=conversation_history
    )

    if not resolved.get("success"):
        return {
            "success": True,
            "reply": (
                "Which product would you like me to add "
                "to your Smart Cart?"
            ),
            "tool_history": []
        }

    product_query = resolved["query"]

    # ---------------------------------------------------------
    # Step 2: Verify product through backend
    # ---------------------------------------------------------

    search_result = execute_tool(
        "search_products",
        query=product_query
    )

    tool_history = [
        {
            "tool": "search_products",
            "arguments": {
                "query": product_query
            },
            "result": search_result
        }
    ]

    if search_result.get("success") is not True:
        return {
            "success": False,
            "reply": (
                "I couldn't verify that product in the catalog."
            ),
            "tool_history": tool_history
        }

    products = search_result.get("products", [])

    if not products:
        return {
            "success": True,
            "reply": (
                f"I couldn't find a product matching "
                f"'{product_query}' in our catalog."
            ),
            "tool_history": tool_history
        }

    if len(products) > 1:
        return {
            "success": True,
            "reply": (
                "I found multiple products matching that request. "
                "Please tell me which one you'd like to add."
            ),
            "tool_history": tool_history
        }

    product = products[0]

    product_id = product.get("product_id")

    if product_id is None:
        return {
            "success": False,
            "reply": (
                "I couldn't verify the product identifier."
            ),
            "tool_history": tool_history
        }

    # ---------------------------------------------------------
    # Step 3: Create Smart Cart
    # ---------------------------------------------------------

    cart_result = execute_tool(
        "create_smart_cart",
        user_id=user_id
    )

    tool_history.append({
        "tool": "create_smart_cart",
        "arguments": {
            "user_id": user_id
        },
        "result": cart_result
    })

    if cart_result.get("success") is not True:
        return {
            "success": False,
            "reply": (
                "I couldn't create your Smart Cart right now."
            ),
            "tool_history": tool_history
        }

    cart = cart_result.get("cart", {})
    cart_id = cart.get("cart_id")

    if cart_id is None:
        return {
            "success": False,
            "reply": (
                "The Smart Cart was created but its identifier "
                "could not be verified."
            ),
            "tool_history": tool_history
        }

    # ---------------------------------------------------------
    # Step 4: Determine purchase authorization
    # ---------------------------------------------------------

    auto_buy_enabled = (
        explicit_auto_buy
        and arguments["maximum_price"] is not None
    )

    # ---------------------------------------------------------
    # Step 5: Add item using ONLY backend-verified IDs
    # ---------------------------------------------------------

    add_arguments = {
        "cart_id": cart_id,
        "product_id": product_id,
        "variant": arguments["variant"],
        "color": arguments["color"],
        "quantity": arguments["quantity"],
        "maximum_price": arguments["maximum_price"],
        "auto_buy_enabled": auto_buy_enabled,
    }
    print("DEBUG FINAL ADD ARGUMENTS:", add_arguments)
    add_result = execute_tool(
        "add_to_smart_cart",
        **add_arguments
    )

    tool_history.append({
        "tool": "add_to_smart_cart",
        "arguments": add_arguments,
        "result": add_result
    })

    if add_result.get("success") is not True:
        return {
            "success": False,
            "reply": (
                "I couldn't add that product to your Smart Cart."
            ),
            "tool_history": tool_history
        }

    # ---------------------------------------------------------
    # Step 6: Deterministic final response
    # ---------------------------------------------------------

    product_name = product.get(
        "name",
        product_query
    )

    if auto_buy_enabled:
        reply = (
            f"Done — I added the {product_name} to your Smart Cart "
            f"with automatic purchase enabled up to "
            f"Rs. {arguments['maximum_price']:,.0f}."
        )
    else:
        reply = (
            f"Done — I added the {product_name} to your Smart Cart. "
            "Automatic purchase is not enabled."
        )

    return {
        "success": True,
        "reply": reply,
        "tool_history": tool_history
    }
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

    known_product_ids = set()
    known_cart_ids = set()
    known_smart_cart_item_ids = set()
    known_support_request_ids = set()

    # ---------------------------------------------------------
    # Recovery state.
    #
    # With max_tool_steps kept low (5) for latency reasons, the
    # add_to_smart_cart flow cannot afford to wait for the model
    # to self-correct after guessing a wrong product_id -- that's
    # the exact scenario that previously hit the 503. Other tools
    # keep a 2-failure threshold to match the model-self-recovery
    # contract the test suite already encodes.
    # ---------------------------------------------------------

    unverified_product_failure_count = 0

    # ---------------------------------------------------------
    # Request type detection
    # ---------------------------------------------------------

    availability_required = (
        is_availability_request(user_message)
        or (
            is_product_search_request(user_message)
            and has_variant_or_color_reference(user_message)
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
    # CONTROLLED SMART CART WORKFLOW
    # ---------------------------------------------------------

    if smart_cart_action_required:
        return run_smart_cart_workflow(
            user_message=user_message,
            user_id=user_id,
            conversation_history=conversation_history
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

                    if not explicit_auto_buy:

                        tool_arguments["auto_buy_enabled"] = False

                    else:

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

                            continue

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
                # Record the ORIGINAL failed attempt immediately, in
                # order, before any override logic runs. Several
                # tests assert tool_history[0] is this failed call.
                # -------------------------------------------------

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

                unverified_product_error = (
                    tool_name in {
                        "check_inventory",
                        "check_availability",
                        "get_product_details",
                        "add_to_smart_cart",
                    }
                    and "Unverified product_id" in str(exc)
                )

                if unverified_product_error:
                    unverified_product_failure_count += 1

                # add_to_smart_cart is the flow that actually hit the
                # 503 in Swagger (product_id is always checked before
                # cart_id, so a bad product_id is always the FIRST
                # failure in that flow). Other tools keep the
                # 2-failure threshold to match the self-recovery
                # contract the existing test suite asserts on.
                product_override_threshold = (
                    1 if tool_name == "add_to_smart_cart" else 2
                )

                if (
                    unverified_product_error
                    and unverified_product_failure_count
                        >= product_override_threshold
                    and not known_product_ids
                ):

                    resolved_query = (
                        resolve_product_query_from_context(
                            conversation_history,
                            user_message
                        )
                    )

                    forced_result = execute_tool(
                        "search_products",
                        query=resolved_query
                    )

                    tool_history.append({
                        "tool": "search_products",
                        "arguments": {
                            "query": resolved_query
                        },
                        "result": forced_result
                    })

                    for product in forced_result.get(
                        "products",
                        []
                    ):

                        forced_product_id = product.get(
                            "product_id"
                        )

                        if forced_product_id is not None:

                            known_product_ids.add(
                                forced_product_id
                            )

                    messages.append({
                        "role": "tool",
                        "tool_name": "search_products",
                        "content": json.dumps(
                            forced_result,
                            default=str
                        )
                    })

                    messages.append({
                        "role": "user",
                        "content": (
                            "The product has now been verified via "
                            "search_products (see the result above). "
                            "Do not call search_products again. "
                            "Proceed directly to create_smart_cart "
                            "(if no verified cart_id exists yet) or "
                            "add_to_smart_cart using the verified "
                            "product_id."
                        )
                    })

                else:

                    # Covers: unverified cart_id, unverified item_id,
                    # unverified support request_id, disallowed tools,
                    # and product_id failures below their threshold.
                    # The model is expected to self-correct on its
                    # next turn by calling the appropriate approved
                    # tool (search_products / create_smart_cart).

                    recovery_message = (
                        "The previous tool call was rejected because "
                        "it used an unverified backend identifier.\n\n"

                        "Do NOT retry the same tool call with the "
                        "same or another guessed ID. Any ID number "
                        "that appeared in earlier reply text is NOT "
                        "valid for this run -- it must be "
                        "re-obtained.\n\n"

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

            else:

                # -------------------------------------------------
                # Tool executed without raising -- record the
                # result (success OR a returned success=False) and
                # feed it back to the model.
                # -------------------------------------------------

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

    # ---------------------------------------------------------
    # Maximum tool steps exceeded.
    # ---------------------------------------------------------

    raise RuntimeError(
        "Agent exceeded maximum tool-call steps"
    )